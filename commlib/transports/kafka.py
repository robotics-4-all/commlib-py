"""Kafka transport implementation.

Provides Kafka-based pub/sub and RPC communication using confluent-kafka library.
Supports topic-based message distribution.
"""

import logging
import threading
import time

from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple

from confluent_kafka import (
    OFFSET_END,
    Consumer,
    KafkaError,
    KafkaException,
    Producer,
)

from commlib.task_queue import (
    BaseTaskProducer,
    BaseTaskWorker,
    TaskEnvelope,
    TaskProgress,
    TaskResult,
    TaskStatus,
)
from commlib.action import (
    BaseActionClient,
    BaseActionService,
    _ActionCancelMessage,
    _ActionFeedbackMessage,
    _ActionGoalMessage,
    _ActionResultMessage,
    _ActionStatusMessage,
)
from commlib.compression import CompressionType
from commlib.endpoints import EndpointState
from commlib.connection import BaseConnectionParameters
from commlib.exceptions import RPCClientTimeoutError, RPCRequestError
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import (
    BaseRPCClient,
    BaseRPCServer,
    BaseRPCService,
    CommRPCHeader,
    CommRPCMessage,
)
from commlib.serializer import JSONSerializer
from commlib.transports.base_transport import BaseTransport
from commlib.utils import gen_timestamp

kafka_logger: logging.Logger = logging.getLogger("kafka")


SECURITY_PROTOCOL = "SASL_SSL"
SASL_MECHANISM = "PLAIN"


class ConnectionParameters(BaseConnectionParameters):
    """Connection Parameters."""

    # https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md
    host: str = "localhost"
    port: int = 29092
    username: str = ""
    password: str = ""
    ssl: bool = False
    group: str = "main"
    auto_create_topics: bool = True
    auto_commit_interval: int = 1000  # ms


class KafkaTransport(BaseTransport):
    """Kafka Transport."""

    def __init__(
        self,
        *args,
        compression: int = CompressionType.DEFAULT_COMPRESSION,
        serializer: Any = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._serializer = serializer if serializer is not None else JSONSerializer()
        self._compression = compression
        self._producer: Optional[Producer] = None
        self._subscribers: List[Tuple[Consumer, Thread, threading.Event]] = []
        self._producers: List[Producer] = []
        self._consumers: List[Consumer] = []
        self.connect()

    def connect(self) -> None:
        """Connect."""
        pass

    @property
    def producer(self) -> Optional[Producer]:
        """Producer."""
        return self._producer

    @producer.setter
    def producer(self, value: Optional[Producer]) -> None:
        self._producer = value

    @property
    def is_connected(self) -> bool:
        """Is connected."""
        return self._connected

    def start(self) -> None:
        """Start."""
        if not self.is_connected:
            self.connect()

    def stop(self) -> None:
        """Stop."""
        if self.is_connected:
            for producer in self._producers:
                try:
                    producer.flush()
                finally:
                    pass
            for consumer, thread, stop_event in self._subscribers:
                stop_event.set()
                thread.join()
                consumer.close()
            self._subscribers = []
            for consumer in self._consumers:
                try:
                    consumer.close()
                finally:
                    pass
            self._set_connected(False)

    def create_producer(self, kafka_cfg):
        """Create producer."""
        producer = Producer(kafka_cfg)
        self._producers.append(producer)
        return producer

    def create_consumer(self, kafka_cfg):
        """Create consumer."""
        consumer = Consumer(kafka_cfg)
        self._consumers.append(consumer)
        return consumer

    def publish_data(
        self,
        producer: Producer,
        data: Dict,
        topic: str,
        key: str = "",
        on_delivery=None,
    ):
        """Publish data."""
        producer.poll(0)
        payload = self._serializer.serialize(data)
        if on_delivery is None:
            on_delivery = self._on_publish
        _value = payload.encode("utf-8") if isinstance(payload, str) else payload
        producer.produce(
            topic, key=key.encode("utf-8"), value=_value, on_delivery=on_delivery
        )

    def _on_publish(self, err, msg):
        pass

    def publish(self, topic: str, data: Dict[str, Any], key: str = "") -> None:
        """Publish."""
        if self._producer is None:
            self._producer = self.create_producer(self._conn_params.model_dump())
        self.publish_data(self._producer, data, topic, key)

    def _unpack_kafka_msg(self, msg: Any) -> Tuple:
        _topic = msg.topic()
        _key = msg.key()
        _timestamp = msg.timestamp()
        _data = self._serializer.deserialize(msg.value())
        return _data, _topic, _key, _timestamp

    def _poll_loop(
        self, consumer: Consumer, stop_event: threading.Event, callback: Callable
    ):
        while not stop_event.is_set():
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                _err = msg.error()
                if (  # type: ignore[attr-defined]  # pylint: disable=protected-access
                    _err is not None and _err.code() == KafkaError._PARTITION_EOF
                ):
                    print(
                        "%% %s [%d] reached end at offset %d\n"
                        % (msg.topic(), msg.partition() or 0, msg.offset() or 0)
                    )
                elif (  # type: ignore[attr-defined]
                    _err is not None and _err.code() == KafkaError.UNKNOWN_TOPIC_OR_PART
                ):
                    time.sleep(1.0)
                    continue
                elif _err is not None:
                    self.log.error("Kafka error: %s", _err)
            else:
                try:
                    callback(msg)
                except Exception:
                    self.log.error(
                        "Exception caught in _poll_loop callback", exc_info=True
                    )

    def subscribe(
        self, topic: str, callback: Callable, group_id: Optional[str] = None
    ) -> None:
        """Subscribe."""
        import uuid

        kafka_cfg = self._conn_params.model_dump()

        if group_id is None:
            kafka_cfg["group.id"] = f"rpc-reply-{uuid.uuid4()}"
        else:
            kafka_cfg["group.id"] = group_id

        kafka_cfg["auto.offset.reset"] = "end"
        kafka_cfg["enable.auto.offset.store"] = True
        kafka_cfg["enable.auto.commit"] = True

        consumer = self.create_consumer(kafka_cfg)

        consumer.subscribe([topic])

        stop_event = threading.Event()
        thread = threading.Thread(
            target=self._poll_loop, args=(consumer, stop_event, callback), daemon=True
        )
        thread.start()

        self._subscribers.append((consumer, thread, stop_event))


class Publisher(BasePublisher):
    """Publisher."""

    def __init__(self, *args, key: str = "", **kwargs):
        self._key = key
        self._msg_seq = 0
        self._producer: Producer = None  # type: ignore[assignment]

        super().__init__(*args, **kwargs)
        self._create_kafka_conf()
        self._transport = KafkaTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _create_kafka_conf(self):
        assert self._conn_params is not None, "Connection parameters are not set."
        conn: Any = self._conn_params
        if conn.username not in (
            None,
            "",
        ) and conn.password not in (None, ""):
            auth = {
                "sasl.mechanisms": SASL_MECHANISM,
                "security.protocol": SECURITY_PROTOCOL,
                "sasl.username": conn.username,
                "sasl.password": conn.password,
            }
        else:
            auth = {}
        host = f"{conn.host}:{conn.port}"
        self._kafka_cfg = {
            "bootstrap.servers": host,
            "allow.auto.create.topics": conn.auto_create_topics,
            **auth,
        }

    def publish(self, msg: PubSubMessage, topic: str = "", key: str = "") -> None:
        """Publish."""
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        if key in (None, ""):
            key = self._key
        _topic = topic if topic else self._topic

        assert self._transport is not None, "Transport is not initialized."
        self._transport.publish_data(
            self._producer, data, _topic, key, on_delivery=self._on_delivery
        )
        self._msg_seq += 1

    def _on_delivery(self, err, msg):
        if err is not None:
            self.logger().error(err)
        self.logger().info(
            "Published on %s, partition", msg.topic(), f"{msg.partition()}"
        )

    def run(self, wait: bool = True):
        """Start the publisher.

        Args:
            wait: If True, wait for transport to connect before returning.
                  Fixed in commit 148b825 to match base class API.
        """
        super().run(wait=wait)
        assert self._transport is not None, "Transport is not initialized."
        self._producer = self._transport.create_producer(self._kafka_cfg)

    def stop(self, wait: bool = True):  # pylint: disable=unused-argument
        """Stop."""
        if self._producer is not None:
            self._producer.flush()


class MPublisher(Publisher):
    """Multi-topic Publisher for Kafka."""

    def __init__(self, *args, key: str = "", **kwargs):
        self._key = key
        super().__init__(*args, topic="*", **kwargs)

    def publish(self, msg: PubSubMessage, topic: str = "", key: str = "") -> None:
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        if key in (None, ""):
            key = self._key
        assert self._serializer is not None
        payload = self._serializer.serialize(data)
        _value = payload.encode("utf-8") if isinstance(payload, str) else payload
        self._producer.poll(0)
        self._producer.produce(
            topic, key=key.encode("utf-8"), value=_value, on_delivery=self._on_delivery
        )
        self._msg_seq += 1


class Subscriber(BaseSubscriber):
    """Subscriber."""

    def __init__(self, *args, key: str = "", **kwargs):
        self._key = key
        self._consumer: Consumer = None  # type: ignore[assignment]
        super().__init__(*args, **kwargs)
        self._create_kafka_conf()
        assert self._conn_params is not None, "Connection parameters are not set."
        assert self._serializer is not None, "Serializer is not initialized."
        self._transport = KafkaTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _create_kafka_conf(self):
        assert self._conn_params is not None, "Connection parameters are not set."
        conn: Any = self._conn_params
        if conn.username not in (
            None,
            "",
        ) and conn.password not in (None, ""):
            auth = {
                "sasl.mechanisms": SASL_MECHANISM,
                "security.protocol": SECURITY_PROTOCOL,
                "sasl.username": conn.username,
                "sasl.password": conn.password,
            }
        else:
            auth = {}
        host = f"{conn.host}:{conn.port}"
        self._kafka_cfg = {
            "bootstrap.servers": host,
            "auto.offset.reset": "end",
            "group.id": conn.group,
            "enable.auto.offset.store": True,
            "enable.auto.commit": True,
            "allow.auto.create.topics": conn.auto_create_topics,
            "auto.commit.interval.ms": conn.auto_commit_interval,
            **auth,
        }

    def run_forever(self):
        """Run forever."""
        running = True
        assert self._transport is not None, "Transport is not initialized."
        self._consumer = self._transport.create_consumer(self._kafka_cfg)
        try:
            assert self._topic is not None, "Topic is required for Kafka subscriber"
            self._consumer.subscribe([self._topic], on_assign=self._on_assign)
            while running:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                _err = msg.error()
                if _err is not None:
                    if _err.code() == KafkaError._PARTITION_EOF:  # type: ignore[attr-defined]  # pylint: disable=protected-access
                        print(
                            "%% %s [%d] reached end at offset %d\n"
                            % (msg.topic(), msg.partition() or 0, msg.offset() or 0)
                        )
                    elif (  # type: ignore[attr-defined]
                        _err.code() == KafkaError.UNKNOWN_TOPIC_OR_PART
                    ):
                        kafka_logger.warning(
                            "Topic not yet available: %s (waiting for auto-create)",
                            self._topic,
                        )
                        time.sleep(1.0)
                        continue
                    else:
                        raise KafkaException(_err)
                else:
                    self._on_message(msg)
                    # self._consumer.store_offsets(msg)
                    # self._consumer.commit(asynchronous=False)
        finally:
            # Close down consumer to commit final offsets.
            self._consumer.close()

    def _on_assign(self, consumer, partitions):
        self.logger().info("Assignment:", partitions)
        self._reset_offset(consumer, partitions)

    def _reset_offset(self, consumer, partitions):
        for p in partitions:
            p.offset = OFFSET_END
        consumer.assign(partitions)

    def _on_message(self, msg: Any):
        try:
            data, _topic, _key, _ts = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data)
                else:
                    self.onmessage(self._msg_type(**data))
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _topic = msg.topic()
        _key = msg.key()
        _timestamp = msg.timestamp()
        assert self._serializer is not None, "Serializer is not initialized."
        _data = self._serializer.deserialize(msg.value())
        return _data, _topic, _key, _timestamp

    def stop(self, wait: bool = True):  # pylint: disable=unused-argument
        """Stop."""
        self._consumer.close()


class PSubscriber(Subscriber):
    """Pattern Subscriber for Kafka."""

    def _on_message(self, msg: Any):
        try:
            data, topic, _key, _ts = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data, topic)
                else:
                    self.onmessage(self._msg_type(**data), topic)
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)


class RPCService(BaseRPCService):
    """RPC Service."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = KafkaTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        assert self._transport is not None, "Transport is not initialized."
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp)

    def _on_request_handle(self, msg: Any) -> None:
        self._executor.submit(self._on_request_internal, msg)

    def _on_request_internal(self, msg: Any) -> None:
        try:
            req_msg, _uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.warning(
                "Could not unpack request message: %s\nDropping client request!",
                exc,
                exc_info=True,
            )
            return
        try:
            assert self.on_request is not None, "on_request callback is not set."
            if self._msg_type is None:
                resp = self.on_request(req_msg.data)
            else:
                resp = self.on_request(self._msg_type.Request(**req_msg.data))
                resp = resp.model_dump()
            self._send_response(resp, req_msg.header.reply_to)
        except Exception as exc:
            self.log.error(str(exc), exc_info=True)

    def _unpack_comm_msg(self, payload: Any, uri: Optional[str] = None) -> Any:
        assert self._serializer is not None, "Serializer is not initialized."
        try:
            if hasattr(payload, "topic"):
                uri = payload.topic()
                payload = payload.value()
            _payload = self._serializer.deserialize(payload)
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
        except Exception as e:
            raise RPCRequestError(str(e)) from e
        return _req_msg, uri

    def run_forever(self):
        """run_forever."""
        assert self._transport is not None, "Transport is not initialized."
        self._transport.subscribe(
            self._rpc_name, self._on_request_handle, group_id=self._rpc_name
        )
        self._transport.start()
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(0.001)
        self._transport.stop()


class RPCServer(BaseRPCServer):
    """RPC Server."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCServer
            kwargs: See BaseRPCServer
        """
        super().__init__(*args, **kwargs)
        assert self._conn_params is not None, "Connection parameters are not set."
        assert self._serializer is not None, "Serializer is not initialized."
        assert self._compression is not None, "Compression is not initialized."
        self._transport = KafkaTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        for uri in self._svc_map:
            callback = self._svc_map[uri][0]
            msg_type = self._svc_map[uri][1]
            self._register_endpoint(uri, callback, msg_type)

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        """_send_response.

        Args:
            data (dict): data
            reply_to (str): reply_to
        """
        assert self._transport is not None, "Transport is not initialized."
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp)

    def _on_request_handle(self, msg: Any) -> None:
        self._executor.submit(self._on_request_internal, msg)

    def _on_request_internal(self, msg: Any) -> None:
        try:
            req_msg, _uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.error(
                "Could not unpack request message: %s\nDropping client request!",
                exc,
                exc_info=True,
            )
            return
        try:
            uri = uri.replace("/", ".")
            svc_uri = uri.replace(self._base_uri, "")
            if svc_uri[0] == ".":
                svc_uri = svc_uri[1:]
            if svc_uri not in self._svc_map:
                return
            else:
                clb = self._svc_map[svc_uri][0]
                msg_type = self._svc_map[svc_uri][1]
                if msg_type is None:
                    resp = clb(req_msg.data)
                else:
                    resp = clb(msg_type.Request(**req_msg.data))
                    resp = resp.model_dump()
            self._send_response(resp, req_msg.header.reply_to)
        except Exception as exc:
            self.log.error(str(exc), exc_info=False)
            return

    def _unpack_comm_msg(self, msg: Any) -> Tuple[CommRPCMessage, str]:
        assert self._serializer is not None, "Serializer is not initialized."
        """_unpack_comm_msg.

        Unpack payload, header and uri from communcation message.

        Args:
            msg (Any): msg

        Returns:
            Tuple[Any, Any, Any]:
        """
        try:
            _uri = msg.topic()
            _payload = self._serializer.deserialize(msg.value())
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
        except Exception as e:
            raise RPCRequestError(str(e)) from e
        return _req_msg, _uri

    def _register_endpoint(
        self, uri: str, callback: Callable, msg_type: Optional[RPCMessage] = None
    ):
        self._svc_map[uri] = (callback, msg_type)
        if self._base_uri in (None, ""):
            full_uri = uri
        else:
            full_uri = f"{self._base_uri}.{uri}"
        self.log.info("Registering endpoint <%s>", full_uri)
        assert self._transport is not None, "Transport is not initialized."
        self._transport.subscribe(full_uri, self._on_request_handle, group_id=full_uri)

    def run_forever(self):
        """run_forever."""
        assert self._transport is not None, "Transport is not initialized."
        self._transport.start()
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught")
                    break
            time.sleep(0.001)
        self._transport.stop()


class RPCClient(BaseRPCClient):
    """RPCClient."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCClient
            kwargs: See BaseRPCClient
        """
        self._response = None
        self._delay: float = 0.0

        super().__init__(*args, **kwargs)
        assert self._conn_params is not None, "Connection parameters are not set."
        assert self._serializer is not None, "Serializer is not initialized."
        assert self._compression is not None, "Compression is not initialized."
        self._transport = KafkaTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _gen_queue_name(self):
        """_gen_queue_name."""
        return f"rpc-{self._gen_random_id()}"

    def _prepare_request(
        self, data: Dict[str, Any], reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.header.reply_to = (
            reply_to if reply_to else self._gen_queue_name()
        )
        self._comm_obj.data = data
        return self._comm_obj.model_dump()

    def _on_response_wrapper(self, msg: Any) -> None:
        try:
            data, _header, _uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.error(exc, exc_info=True)
            data = {}
        self._response = data

    def _unpack_comm_msg(self, payload: Any, uri: Optional[str] = None) -> Any:
        assert self._serializer is not None, "Serializer is not initialized."
        if hasattr(payload, "topic"):
            uri = payload.topic()
            payload = payload.value()
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header, uri

    def _wait_for_response(self, timeout: float = 10.0):
        """_wait_for_response.

        Args:
            timeout (float): timeout
        """
        start_t = time.time()
        while self._response is None:
            elapsed_t = time.time() - start_t
            if elapsed_t >= timeout:
                raise RPCClientTimeoutError(f"Response timeout after {timeout} seconds")
            time.sleep(0.001)
        return self._response

    def call(self, msg: RPCMessage.Request, timeout: float = 30) -> RPCMessage.Response:
        """call.

        Args:
            msg (RPCMessage.Request): msg
            timeout (float): timeout
        """
        if self._msg_type is None:
            data: Any = msg if isinstance(msg, dict) else msg.model_dump()
        else:
            if not isinstance(msg, self._msg_type.Request):
                raise ValueError("Message type not valid")
            data = msg.model_dump()

        self._response = None

        _msg = self._prepare_request(data)
        _reply_to = _msg["header"]["reply_to"]

        assert self._transport is not None, "Transport is not initialized."
        self._transport.subscribe(_reply_to, self._on_response_wrapper)
        start_t = time.time()
        self._transport.publish(self._rpc_name, _msg)
        _resp = self._wait_for_response(timeout=timeout)
        elapsed_t = time.time() - start_t
        self._delay = elapsed_t

        if self._msg_type is None:
            return _resp  # type: ignore[reportReturnType]
        else:
            return self._msg_type.Response(**_resp)


class ActionService(BaseActionService):
    """ActionService."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionService
            kwargs: See BaseActionService
        """
        super().__init__(*args, **kwargs)

        self._goal_rpc = RPCService(
            msg_type=_ActionGoalMessage,
            rpc_name=self._goal_rpc_uri,
            conn_params=self._conn_params,
            on_request=self._handle_send_goal,
            debug=self.debug,
        )
        self._cancel_rpc = RPCService(
            msg_type=_ActionCancelMessage,
            rpc_name=self._cancel_rpc_uri,
            conn_params=self._conn_params,
            on_request=self._handle_cancel_goal,
            debug=self.debug,
        )
        self._result_rpc = RPCService(
            msg_type=_ActionResultMessage,
            rpc_name=self._result_rpc_uri,
            conn_params=self._conn_params,
            on_request=self._handle_get_result,
            debug=self.debug,
        )
        self._feedback_pub = Publisher(
            msg_type=_ActionFeedbackMessage,
            topic=self._feedback_topic,
            conn_params=self._conn_params,
            debug=self.debug,
        )
        self._status_pub = Publisher(
            msg_type=_ActionStatusMessage,
            topic=self._status_topic,
            conn_params=self._conn_params,
            debug=self.debug,
        )


class ActionClient(BaseActionClient):
    """ActionClient."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionClient
            kwargs: See BaseActionClient
        """
        super().__init__(*args, **kwargs)

        self._goal_client = RPCClient(
            msg_type=_ActionGoalMessage,
            rpc_name=self._goal_rpc_uri,
            conn_params=self._conn_params,
            debug=self.debug,
        )
        self._cancel_client = RPCClient(
            msg_type=_ActionCancelMessage,
            rpc_name=self._cancel_rpc_uri,
            conn_params=self._conn_params,
            debug=self.debug,
        )
        self._result_client = RPCClient(
            msg_type=_ActionResultMessage,
            rpc_name=self._result_rpc_uri,
            conn_params=self._conn_params,
            debug=self.debug,
        )
        self._status_sub = Subscriber(
            msg_type=_ActionStatusMessage,
            conn_params=self._conn_params,
            topic=self._status_topic,
            on_message=self._on_status,
            debug=self.debug,
        )
        self._feedback_sub = Subscriber(
            msg_type=_ActionFeedbackMessage,
            conn_params=self._conn_params,
            topic=self._feedback_topic,
            on_message=self._on_feedback,
            debug=self.debug,
        )


class TaskProducer(BaseTaskProducer):
    """Task Producer."""

    _transport: KafkaTransport  # type: ignore[assignment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = KafkaTransport(conn_params=self._conn_params)
        self._task_topic = f"{self._queue_name}-tasks"
        self._result_topic = f"{self._queue_name}-results"
        self._progress_topic = f"{self._queue_name}-progress"
        self._result_sub = None
        self._progress_sub = None

    def run(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Run."""
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        self._transport.start()
        self._result_sub = Subscriber(
            conn_params=self._conn_params,
            topic=self._result_topic,
            on_message=self._on_result_msg,
        )
        self._result_sub.run()
        self._progress_sub = Subscriber(
            conn_params=self._conn_params,
            topic=self._progress_topic,
            on_message=self._on_progress_msg,
        )
        self._progress_sub.run()
        self.set_state(EndpointState.CONNECTED)

    def stop(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Stop."""
        if self._result_sub is not None:
            self._result_sub.stop()
        if self._progress_sub is not None:
            self._progress_sub.stop()
        if self._transport is not None:
            self._transport.stop()
        self.set_state(EndpointState.DISCONNECTED)

    def _send_task(self, envelope: TaskEnvelope) -> None:
        assert self._transport is not None
        producer = self._transport.producer
        assert producer is not None
        data = envelope.model_dump()
        payload = JSONSerializer.serialize(data)
        producer.produce(
            topic=self._task_topic,
            key=envelope.task_id.encode(),
            value=payload.encode() if isinstance(payload, str) else payload,
        )
        producer.flush()

    def _on_result_msg(self, msg) -> None:
        if isinstance(msg, dict):
            data = msg
        else:
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
        result = TaskResult(**data)
        self._handle_result(result)

    def _on_progress_msg(self, msg) -> None:
        if isinstance(msg, dict):
            data = msg
        else:
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
        progress = TaskProgress(**data)
        self._handle_progress(progress)

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        envelope.status = int(TaskStatus.DEAD_LETTER)
        self.log.warning(
            "Task %s sent to DLQ '%s': %s",
            envelope.task_id,
            self._config.get_dlq_name(),
            error,
        )
        assert self._transport is not None
        producer = self._transport.producer
        assert producer is not None
        data = envelope.model_dump()
        data["error"] = error
        dlq_topic = self._config.get_dlq_name().replace(".", "-")
        payload = JSONSerializer.serialize(data)
        producer.produce(
            topic=dlq_topic,
            key=envelope.task_id.encode(),
            value=payload.encode() if isinstance(payload, str) else payload,
        )
        producer.flush()


class TaskWorker(BaseTaskWorker):
    """Task Worker."""

    _transport: KafkaTransport  # type: ignore[assignment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = KafkaTransport(conn_params=self._conn_params)
        self._task_topic = f"{self._queue_name}-tasks"
        self._result_topic = f"{self._queue_name}-results"
        self._progress_topic = f"{self._queue_name}-progress"
        self._task_sub = None

    def run(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Run."""
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        self._transport.start()
        self._task_sub = Subscriber(
            conn_params=self._conn_params,
            topic=self._task_topic,
            on_message=self._on_task_msg,
        )
        self._task_sub.run()
        self.set_state(EndpointState.CONNECTED)

    def stop(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Stop."""
        self._stop_event.set()
        if self._task_sub is not None:
            self._task_sub.stop()
        if self._transport is not None:
            self._transport.stop()
        self.set_state(EndpointState.DISCONNECTED)

    def _on_task_msg(self, msg) -> None:
        if isinstance(msg, dict):
            data = msg
        else:
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
        envelope = TaskEnvelope(**data)

        threading.Thread(
            target=self._process_task,
            args=(envelope,),
            daemon=True,
        ).start()

    def _publish_result(self, result: TaskResult) -> None:
        assert self._transport is not None
        producer = self._transport.producer
        assert producer is not None
        data = result.model_dump()
        payload = JSONSerializer.serialize(data)
        producer.produce(
            topic=self._result_topic,
            key=result.task_id.encode(),
            value=payload.encode() if isinstance(payload, str) else payload,
        )
        producer.flush()

    def _publish_progress(self, progress: TaskProgress) -> None:
        assert self._transport is not None
        producer = self._transport.producer
        assert producer is not None
        data = progress.model_dump()
        payload = JSONSerializer.serialize(data)
        producer.produce(
            topic=self._progress_topic,
            key=progress.task_id.encode(),
            value=payload.encode() if isinstance(payload, str) else payload,
        )
        producer.flush()

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        super()._send_to_dlq(envelope, error)
        assert self._transport is not None
        producer = self._transport.producer
        assert producer is not None
        data = envelope.model_dump()
        data["error"] = error
        dlq_topic = self._config.get_dlq_name().replace(".", "-")
        payload = JSONSerializer.serialize(data)
        producer.produce(
            topic=dlq_topic,
            key=envelope.task_id.encode(),
            value=payload.encode() if isinstance(payload, str) else payload,
        )
        producer.flush()
