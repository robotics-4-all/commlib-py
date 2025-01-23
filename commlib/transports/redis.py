import functools
import logging
import re
import time
from typing import Any, Callable, Dict, Optional, Tuple, Union

import redis

from commlib.action import (
    BaseActionClient,
    BaseActionService,
    _ActionCancelMessage,
    _ActionFeedbackMessage,
    _ActionGoalMessage,
    _ActionResultMessage,
    _ActionStatusMessage,
)
from commlib.compression import CompressionType, deflate, inflate_str
from commlib.connection import BaseConnectionParameters
from commlib.exceptions import RPCRequestError
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import (
    BasePublisher, BaseSubscriber,
    validate_pubsub_topic, validate_pubsub_topic_strict
)
from commlib.rpc import (
    BaseRPCClient,
    BaseRPCService,
    CommRPCHeader,
    CommRPCMessage,
)
from commlib.serializer import JSONSerializer, Serializer
from commlib.transports.base_transport import BaseTransport
from commlib.utils import gen_timestamp

from rich import console, pretty

pretty.install()
console = console.Console()

redis_logger = None


class ConnectionParameters(BaseConnectionParameters):
    host: str = "localhost"
    port: int = 6379
    unix_socket: str = ""
    db: int = 0
    username: str = ""
    password: str = ""
    socket_timeout: Union[float, None] = None


class RedisConnection(redis.Redis):
    """RedisConnection."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super(RedisConnection, self).__init__(*args, **kwargs)


class RedisTransport(BaseTransport):
    @classmethod
    def logger(cls) -> logging.Logger:
        global redis_logger
        if redis_logger is None:
            redis_logger = logging.getLogger(__name__)
        return redis_logger

    def __init__(self,
                 compression: CompressionType = CompressionType.DEFAULT_COMPRESSION,
                 serializer: Serializer = JSONSerializer(),
                 *args,
                 **kwargs):
        """
        Initialize the RedisTransport.

        Args:
            compression (CompressionType): The compression type to use for message compression.
                Defaults to CompressionType.DEFAULT_COMPRESSION.
            serializer (Serializer): The serializer to use for message serialization.
                Defaults to JSONSerializer().
            *args: Variable length argument list to be passed to the parent class constructor.
            **kwargs: Arbitrary keyword arguments to be passed to the parent class constructor.
        """
        super().__init__(*args, **kwargs)
        self._serializer = serializer
        self._compression = compression
        self._rsub = None
        self._redis = None
        self._redis_pubsub_join_timeout = 1  # sec
        self._rsub_thread = None
        self._wait_for_connection_init = 0.01  # sec
        self._wait_for_pubsub_stop = 0.1  # sec

    @property
    def is_connected(self) -> bool:
        try:
            if self._redis is None:
                return False
            self._redis.ping()
            return True
        except Exception as e:
            return False

    @property
    def log(self) -> logging.Logger:
        return self.logger()

    def connect(self) -> None:
        if self._conn_params.unix_socket not in ("", None):
            self._redis = RedisConnection(
                unix_socket_path=self._conn_params.unix_socket,
                username=self._conn_params.username,
                password=self._conn_params.password,
                db=self._conn_params.db,
                decode_responses=True,
                socket_timeout=self._conn_params.socket_timeout,
                socket_keep_alive=True,
                retry_on_timeout=True,
            )
        else:
            self._redis = RedisConnection(
                host=self._conn_params.host,
                port=self._conn_params.port,
                username=self._conn_params.username,
                password=self._conn_params.password,
                db=self._conn_params.db,
                decode_responses=False,
                socket_timeout=self._conn_params.socket_timeout,
                retry_on_timeout=True,
            )

        self._rsub = self._redis.pubsub()

    def start(self) -> None:
        if not self.is_connected:
            self.connect()
        while not self.is_connected:
            time.sleep(self._wait_for_connection_init)

    def stop(self) -> None:
        if not self.is_connected:
            self.log.warning("Attempting to stop transport while not connected")
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        if self._rsub is not None:
            self._rsub.close()
        if self._redis is not None:
            self._redis.connection_pool.disconnect(inuse_connections=True)
            self._redis.close()
            del self._redis

    def delete_queue(self, queue_name: str) -> bool:
        return True if self._redis.delete(queue_name) else False

    def queue_exists(self, queue_name: str) -> bool:
        return True if self._redis.exists(queue_name) else False

    def create_queue(self, queue_name: str) -> bool:
        self._redis.rpush(queue_name, "QueueInit")

    def push_msg_to_queue(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        if self._compression != CompressionType.NO_COMPRESSION:
            payload = inflate_str(payload)
        self._redis.rpush(queue_name, payload)

    def publish(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        if self._compression != CompressionType.NO_COMPRESSION:
            payload = inflate_str(payload)
        self._redis.publish(queue_name, payload)

    def subscribe(self, topic: str, callback: Callable):
        if topic in (None, ""):
            self.log.warning(f"Attempt to subscribe to empty topic - {topic}")
            return
        _clb = functools.partial(self._on_msg_internal, callback)
        if self._rsub is None:
            self.log.warning("Redis pubsub not initialized - Cannot proceed to subscriptions!")
            return
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        self._rsub.psubscribe(**{topic: _clb})
        self._rsub_thread = self._rsub.run_in_thread(0.001, daemon=True,
                                                     exception_handler=self.exception_handler)
        return self._rsub_thread

    def exception_handler(self, ex, pubsub, thread):
        self.log.error(f"Redis PubSub error in thread: {thread}, exception: {ex}")
        thread.stop()
        thread.join(timeout=self._redis_pubsub_join_timeout)
        pubsub.close()

    def msubscribe(self, topics: Dict[str, callable]):
        _topics = {}
        for topic, callback in topics.items():
            _clb = functools.partial(self._on_msg_internal, callback)
            _topics[topic] = _clb
        if _topics in (None, {}):
            self.log.warning(f"Attempt to subscribe to empty topics - {_topics}")
            return
        if self._rsub is None:
            self.log.warning("Redis pubsub not initialized - Cannot proceed to subscriptions!")
            return
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        self._rsub.psubscribe(**_topics)
        self._rsub_thread = self._rsub.run_in_thread(0.001, daemon=True,
                                                     exception_handler=self.exception_handler)
        return self._rsub_thread

    def _on_msg_internal(self, callback: Callable, data: Any):
        if self._compression != CompressionType.NO_COMPRESSION:
            # _topic = data['channel']
            data["data"] = deflate(data["data"])
        callback(data)

    def wait_for_msg(self, queue_name: str, timeout=10):
        try:
            msgq, payload = self._redis.blpop(queue_name, timeout=timeout)
            if isinstance(payload, bytes) and payload == b'QueueInit':
                return self.wait_for_msg(queue_name, timeout)
            if self._compression != CompressionType.NO_COMPRESSION:
                payload = deflate(payload)
        except Exception:
            # self.log.warning(f"Timeout after {timeout} seconds waiting for message")
            msgq = ""
            payload = None
        return msgq, payload


class RPCService(BaseRPCService):
    """RPCService.
    Redis RPC Service class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCService class
            kwargs: See BaseRPCService class
        """
        super(RPCService, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request_handle(self, data: Dict[str, Any], header: Dict[str, Any]):
        try:
            self._executor.submit(self._on_request_internal, data, header)
        except Exception as exc:
            self.log.error(str(exc), exc_info=False)

    def _on_request_internal(self, data: Dict[str, Any], header: Dict[str, Any]):
        if "reply_to" not in header:
            return
        try:
            _req_msg = CommRPCMessage(
                header=CommRPCHeader(reply_to=header["reply_to"]), data=data
            )
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
            if self._msg_type is None:
                resp = self.on_request(data)
            else:
                resp = self.on_request(self._msg_type.Request(**data))
                # RPCMessage.Response object here
                resp = resp.model_dump()
        except RPCRequestError:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        except Exception as exc:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        self._send_response(resp, _req_msg.header.reply_to)

    def run_forever(self):
        """
        Continuously runs the transport, processing messages and handling stop events.

        This method starts the transport and enters an infinite loop where it waits for
        messages on the specified RPC queue. When a message is received, it detaches the
        request handler to process the payload. If a stop event is set, it breaks the loop,
        deletes the RPC queue, and stops the transport.

        Note:
            This method blocks indefinitely until a stop event is set.

        Raises:
            Exception: If there is an error starting the transport or processing messages.
        """
        self._transport.start()
        # if self._transport.queue_exists(self._rpc_name):
        #     self._transport.delete_queue(self._rpc_name)
        # self._transport.create_queue(self._rpc_name)
        while True:
            time.sleep(0.001)
            msgq, payload = self._transport.wait_for_msg(self._rpc_name)
            if payload is None: continue
            self._detach_request_handler(payload)
            if self.t_stop_event.is_set():
                break

    def _detach_request_handler(self, payload: str):
        data, header = self._unpack_comm_msg(payload)
        # self.log.info(f"RPC Request <{self._rpc_name}>")
        self._on_request_handle(data, header)

    def _unpack_comm_msg(self, payload: str) -> Tuple:
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header


class RPCClient(BaseRPCClient):
    """RPCClient."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _gen_queue_name(self):
        return f"rpc-{self._gen_random_id()}"

    def _prepare_request(self, data: Dict[str, Any]):
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.model_dump()

    def call(self, msg: RPCMessage.Request, timeout: float = 10) -> RPCMessage.Response:
        """
        Sends an RPC request message and waits for a response.

        Args:
            msg (RPCMessage.Request): The RPC request message to be sent.
            timeout (float, optional): The maximum time to wait for a response in seconds. Defaults to 10.

        Returns:
            RPCMessage.Response: The response message received. If no response is received within the timeout period, returns None.
        """
        if self._msg_type is None and isinstance(msg, dict):
            data = msg
        elif self._msg_type is not None and isinstance(msg, self._msg_type.Request):
            data = msg.model_dump()
        else:
            raise RPCRequestError("Invalid message type passed to RPC call")
        _msg = self._prepare_request(data)
        _reply_to = _msg["header"]["reply_to"]
        # print(f"Waiting for queue {self._rpc_name}...")
        # while not self._transport.queue_exists(self._rpc_name):
        #     time.sleep(0.001)
        # print("Queue exists!")
        self._transport.push_msg_to_queue(self._rpc_name, _msg)
        _, _msg = self._transport.wait_for_msg(_reply_to, timeout=timeout)
        self._transport.delete_queue(_reply_to)
        if _msg is None:
            return None
        data, header = self._unpack_comm_msg(_msg)
        # TODO: Evaluate response type and raise exception if necessary
        if self._msg_type is None:
            return data
        else:
            return self._msg_type.Response(**data)

    def _unpack_comm_msg(self, payload: str) -> Tuple:
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header


class Publisher(BasePublisher):
    """Publisher.
    Redis Publisher (Single Topic).
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        self._msg_seq = 0

        super().__init__(*args, **kwargs)

        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def publish(self, msg: PubSubMessage) -> None:
        """publish.
        Publish message

        Args:
            msg (PubSubMessage): msg

        Returns:
            None:
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        self.log.debug(f"Publishing Message to topic <{self._topic}>")
        self._transport.publish(self._topic, data)
        self._msg_seq += 1


class MPublisher(Publisher):
    """MPublisher.
    Multi-Topic Redis Publisher
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See Publisher class
            kwargs: See Publisher class
        """
        super().__init__(topic=None, *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        """publish.

        Args:
            msg (PubSubMessage): Message to publish
            topic (str): Topic (URI) to send the message

        Returns:
            None:
        """
        validate_pubsub_topic_strict(topic)
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        self.log.debug(f"Publishing Message: <{topic}>:{data}")
        self._transport.publish(topic, data)
        self._msg_seq += 1


class WPublisher:
    """WPublisher.
    Redis Wrapped-Publisher
    """
    def __init__(self, mpub: MPublisher, topic: str,
                 msg_type: Union[PubSubMessage, None] = None,):
        """__init__.

        Args:
            mpub (MPublisher): Multi-Topic Publisher
            topic (str): topic
            msg_type (PubSubMessage, optional): Message Type
        """
        self._mpub = mpub
        self._topic = topic
        self._msg_type = msg_type
        validate_pubsub_topic_strict(self._topic)

    def publish(self, msg: Union[PubSubMessage, None]) -> None:
        if self._msg_type is not None and not isinstance(msg, self._msg_type):
            raise ValueError(f'Argument "msg" must be of type {self._msg_type}')
        self._mpub.publish(msg, self._topic)


class Subscriber(BaseSubscriber):
    """Subscriber.
    Redis Subscriber
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            queue_size (int): queue_size
            args:
            kwargs:
        """
        self._subscriber_thread = None
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic_strict(self._topic)

    def stop(self):
        """
        Stops the subscriber thread if it is running and then calls the
        stop method of the superclass to perform any additional cleanup.

        This method ensures that the subscriber thread is properly stopped
        before the transport is stopped, preventing any potential issues
        with lingering threads.
        """
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Runs the subscriber thread indefinitely, with periodic checks for a stop event.

        This method starts the transport and subscribes to a topic, then enters an
        infinite loop where it periodically checks for a stop event and sends a ping
        to the Redis server to keep the connection alive.

        Args:
            interval (float): The time interval (in seconds) to wait between each
                              iteration of the loop. Default is 0.001 seconds.

        Notes:
            - The method will break out of the loop if the stop event is set.
            - The method sends a ping to the Redis server on each iteration to keep
              the connection alive.
        """
        self._transport.start()
        self._subscriber_thread = self._transport.subscribe(
            self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            if self._transport._rsub is not None:
                self._transport._rsub.ping()
            time.sleep(interval)

    def _on_message(self, payload: Dict[str, Any]):
        try:
            data, uri = self._unpack_comm_msg(payload)
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, data)
                else:
                    _clb = functools.partial(self.onmessage, self._msg_type(**data))
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        _uri = msg["channel"]
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class WSubscriber(BaseSubscriber):
    """WSubscriber class for subscribing to topics and handling messages using a.
    single connection."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the WSubscriber.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(topic=None, *args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        self._subs: Dict[str, callable] = {}
        self._subscriber_threads = []
        self._subscriber_thread = None

    def subscribe(self, topic, callback: callable) -> None:
        """
        Subscribe to a given topic with a callback function.

        Args:
            topic (str): The topic to subscribe to.
            callback (callable): The function to be called when a message is received on the subscribed topic.

        Returns:
            None
        """
        validate_pubsub_topic_strict(topic)
        self._subs[topic] = callback

    def stop(self):
        """
        Stops the transport by stopping all subscriber threads and the main subscriber thread if they exist.

        This method iterates through all threads in the `_subscriber_threads` list and calls their `stop` method.
        If the `_subscriber_thread` is not `None`, it also calls its `stop` method.
        Finally, it calls the `stop` method of the superclass.
        """
        for sub_thread in self._subscriber_threads:
            sub_thread.stop()
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Start the subscriber and run forever, continuously handling incoming messages.

        Args:
            interval (float, optional): The interval between checking for new messages.
        """
        self._transport.start()
        _topics = {}
        for topic, callback in self._subs.items():
            _topics[topic] = functools.partial(self._on_message, callback)
        self._subscriber_thread = self._transport.msubscribe(_topics)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(interval)

    def _on_message(self, callback: callable, payload: Dict[str, Any]):
        """
        Internal method to handle incoming messages and invoke the callback function.

        Args:
            callback (callable): The callback function to handle the message.
            payload (Dict[str, Any]): The payload of the received message.
        """
        try:
            data, uri = self._unpack_comm_msg(payload)
            if callback is not None:
                if self._msg_type is None:
                    _clb = functools.partial(callback, data)
                else:
                    _clb = functools.partial(callback, self._msg_type(**data))
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        """
        Internal method to unpack the communication message.

        Args:
            msg (Dict[str, Any]): The communication message to unpack.

        Returns:
            Tuple: A tuple containing the unpacked data and URI.
        """
        _uri = msg["channel"]
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class PSubscriber(BaseSubscriber):
    """PSubscriber.
    Redis Pattern-based Subscriber.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic(self._topic)

    def stop(self):
        """
        Stops the Redis transport by stopping the subscriber thread if it exists,
        and then calls the stop method of the superclass.

        This method ensures that any active subscriber thread is properly stopped
        before the transport itself is stopped.
        """
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Starts the transport and subscribes to the topic, then continuously pings
        the Redis subscription to keep the connection alive until a stop event is set.

        Args:
            interval (float): The time to wait between each ping to the Redis subscription.
                              Default is 0.001 seconds.

        The method will run indefinitely until the stop event (`self._t_stop_event`) is set.
        """
        self._transport.start()
        self._subscriber_thread = self._transport.subscribe(
            self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            if self._transport._rsub is not None:
                self._transport._rsub.ping()
            time.sleep(interval)

    def _on_message(self, payload: Dict[str, Any]) -> None:
        try:
            data, topic = self._unpack_comm_msg(payload)
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, data, topic)
                else:
                    _clb = functools.partial(
                        self.onmessage, self._msg_type(**data), topic
                    )
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        """
        Internal method to unpack the communication message.

        Args:
            msg (Dict[str, Any]): The communication message to unpack.

        Returns:
            Tuple: A tuple containing the unpacked data and URI.
        """
        _uri = msg["channel"].decode("utf-8")
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class ActionService(BaseActionService):
    """ActionService.
    Redis Action Server class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionService class.
            kwargs:
        """
        super(ActionService, self).__init__(*args, **kwargs)

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
    """ActionClient.
    Redis Action Client class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionClient class
            kwargs: See BaseActionClient class
        """
        super(ActionClient, self).__init__(*args, **kwargs)

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
        )
        self._feedback_sub = Subscriber(
            msg_type=_ActionFeedbackMessage,
            conn_params=self._conn_params,
            topic=self._feedback_topic,
            on_message=self._on_feedback,
        )
