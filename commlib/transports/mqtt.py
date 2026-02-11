"""MQTT transport implementation.

Provides MQTT-based pub/sub and RPC communication using paho-mqtt library.
Supports MQTT 3.1.1 and MQTT 5.0 protocols with automatic reconnection.
"""

import functools
import logging
import time
from enum import IntEnum
from typing import Any, Callable, Dict, Optional, Tuple, Union

import paho.mqtt.client as mqtt
from paho.mqtt.client import error_string
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from commlib.task_queue import (
    BaseTaskProducer,
    BaseTaskWorker,
    TaskEnvelope,
    TaskProgress,
    TaskResult,
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
from commlib.compression import CompressionType, deflate, inflate_str
from commlib.endpoints import EndpointState
from commlib.connection import BaseConnectionParameters
from commlib.exceptions import RPCClientTimeoutError, RPCRequestError, SubscriberError
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import (
    BasePublisher,
    BaseSubscriber,
    validate_pubsub_topic,
    validate_pubsub_topic_strict,
)
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

mqtt_logger: Optional[logging.Logger] = None


class MQTTReturnCode(IntEnum):
    CONNECTION_SUCCESS = 0
    INCORRECT_PROTOCOL_VERSION = 1
    INVALID_CLIENT_ID = 2
    SERVER_UNAVAILABLE = 3
    AUTHENTICATION_ERROR = 4
    AUTHORIZATION_ERROR = 5


class MQTTProtocolType(IntEnum):
    MQTTv31 = mqtt.MQTTv31
    MQTTv311 = mqtt.MQTTv311
    MQTTv5 = mqtt.MQTTv5


class MQTTQoS(IntEnum):
    """
    MQTT QoS Levels.
    https://mntolia.com/mqtt-qos-levels-explained/
    """

    L0 = 0  # At Most Once
    L1 = 1  # At Least Once
    L2 = 2  # Exactly Once


class ConnectionParameters(BaseConnectionParameters):
    host: str = "localhost"
    port: int = 1883
    username: str = ""
    password: str = ""
    protocol: MQTTProtocolType = MQTTProtocolType.MQTTv311
    transport: str = "tcp"
    keepalive: int = 60


class MQTTTransport(BaseTransport):
    """MQTTTransport."""

    @classmethod
    def logger(cls) -> logging.Logger:
        global mqtt_logger
        if mqtt_logger is None:
            mqtt_logger = logging.getLogger(__name__)
        return mqtt_logger

    def __init__(
        self,
        *args,
        serializer: Any = JSONSerializer(),
        compression: int = CompressionType.DEFAULT_COMPRESSION,
        **kwargs,
    ):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            serializer (Serializer): serializer
            compression (CompressionType): compression_type
        """
        super().__init__(*args, **kwargs)
        self._client = None
        self._serializer = serializer
        self._compression = compression
        self._mqtt_properties = None
        self._stopped = False
        self._subscriptions: Dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        """is_connected.

        Returns:
            bool: True if connected to broker, False otherwise.
        """
        # return self._connected
        return self._client.is_connected() if self._client else False

    def _configure_client(self):
        assert self._client is not None
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        # self._client.on_log = self.on_log
        self._client.on_message = self.on_message

        # Configure reconnection delay
        min_delay = int(self._conn_params.reconnect_delay)
        max_delay = min_delay * 10 if min_delay > 0 else 120
        self._client.reconnect_delay_set(min_delay=min_delay, max_delay=max_delay)

        self._client.username_pw_set(
            self._conn_params.username, self._conn_params.password
        )
        if self._conn_params.ssl:
            import ssl

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            self._client.tls_set_context(ssl_ctx)
            if self._conn_params.ssl_insecure:
                self._client.tls_insecure_set(True)
            else:
                self._client.tls_insecure_set(False)

    def connect(self) -> None:
        if self._connected:
            raise ConnectionError("Transport already connected to broker")
        self._stopped = False

        properties = None
        client_kwargs = {
            "protocol": self._conn_params.protocol,
            "transport": self._conn_params.transport,
        }

        if self._conn_params.protocol == MQTTProtocolType.MQTTv5:
            properties = Properties(PacketTypes.CONNECT)
            properties.MaximumPacketSize = 20
        else:
            client_kwargs["clean_session"] = True

        self._client = mqtt.Client(**client_kwargs)
        self._configure_client()
        assert self._client is not None
        self._client.connect(
            self._conn_params.host,
            int(self._conn_params.port),
            keepalive=self._conn_params.keepalive,
            properties=properties,
        )
        self._mqtt_properties = properties
        self._client.loop_start()

    def on_connect(
        self,
        client: Any,
        userdata: Any,
        flags: Dict[str, Any],
        rc: int,
        properties: Any = None,
    ):
        """on_connect.

        Callback for on-connect event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            flags (Dict[str, Any]): Interla paho-mqtt flags
            rc (int): Return Code - Internal paho-mqtt
        """
        if rc == MQTTReturnCode.CONNECTION_SUCCESS:
            self._set_connected(True)  # Event-driven state update
            self._report_on_connect()
            self._restore_subscriptions()  # Restore subscriptions after reconnection
        else:
            self.log.error("Failed to connect to MQTT Broker: %s", error_string(rc))

    def _report_on_connect(self) -> None:
        self.log.debug("MQTT Transport initiated:")
        self.log.debug(
            "- Broker: mqtt://" + f"{self._conn_params.host}:{self._conn_params.port}"
        )
        self.log.debug("- Data Serialization: %s", self._serializer)
        self.log.debug("- Data Compression: %s", self._compression)

    def on_disconnect(
        self, client: Any, userdata: Any, rc: int, unk: Any = None
    ) -> None:
        """on_disconnect.

        Callback for on-disconnect event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            rc (int): Return Code - Internal paho-mqtt
        """
        self._set_connected(False)  # Event-driven state update
        if self._stopped:
            self.log.debug("Gracefully disconnected from MQTT broker")
            return

        err_msg = ""
        if (
            rc == MQTTReturnCode.AUTHORIZATION_ERROR
            or rc == MQTTReturnCode.AUTHENTICATION_ERROR
        ):
            err_msg = "Authentication error with MQTT broker"
            self.log.error(err_msg)
        elif rc == MQTTReturnCode.CONNECTION_SUCCESS:
            # Graceful disconnect
            self.log.debug("Gracefully disconnected from MQTT broker")
        elif self._conn_params.reconnect_attempts == 0:
            self.log.debug("Disconnected from MQTT broker with: %s. ", error_string(rc))
            self._stopped = True
        else:
            err_msg = error_string(rc)
            self.log.warning("Disconnected from MQTT broker with: %s. ", err_msg)
            self.log.warning(
                "Attempting reconnection in %s....", self._conn_params.reconnect_delay
            )

        # paho-mqtt will automatically reconnect when loop is running

    def _restore_subscriptions(self) -> None:
        """Restore all tracked subscriptions after reconnection."""
        if not self._subscriptions:
            return
        assert self._client is not None
        self.log.debug(
            "Restoring %s subscriptions after reconnect", len(self._subscriptions)
        )
        for topic, (callback, qos) in self._subscriptions.items():
            try:
                _clb = functools.partial(self._on_msg_internal, callback)
                self._client.subscribe(
                    topic, qos=qos, options=None, properties=self._mqtt_properties
                )
                self._client.message_callback_add(topic, _clb)
                self.log.debug("Restored subscription to %s", topic)
            except (
                RuntimeError,
                ConnectionError,
                TimeoutError,
                ValueError,
                KeyError,
                AttributeError,
                OSError,
            ) as e:
                self.log.warning("Failed to restore subscription to %s: %s", topic, e)

    def on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]) -> None:
        """on_message.

        Callback for on-message event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            msg (Dict[str, Any]): Received message
        """

    def on_log(self, client: Any, userdata: Any, level, buf):
        self.log.info(level, buf)

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: MQTTQoS = MQTTQoS.L0,
        retain: bool = False,
    ) -> None:
        """publish.

        Args:
            topic (str): topic
            payload (Dict[str, Any]): payload
            qos (int): MQTT QoS Level (see MQTTQoS class)
            retain (bool): If set to True, then it tells the broker to store
                that message on the topic as the “last good message”.
        """
        assert self._client is not None
        topic = topic.replace(".", "/")
        pl = self._serializer.serialize(payload)
        if self._compression != CompressionType.NO_COMPRESSION:
            pl = inflate_str(pl, self._compression)
        self._client.publish(
            topic, pl, qos=qos, retain=retain, properties=self._mqtt_properties
        )

    def subscribe(
        self, topic: str, callback: Callable, qos: MQTTQoS = MQTTQoS.L0
    ) -> str:
        """subscribe.

        Args:
            topic (str): topic
            callback (Any): callback
            qos (int): MQTT QoS Level (see MQTTQoS class)

        Returns:
            str:
        """
        # Adds subtopic specific callback handlers
        if topic in (None, ""):
            self.log.warning("Attempt to subscribe to empty topic - %s", topic)
            return ""
        assert self._client is not None
        transformed_topic = self._transform_topic(topic)
        # Track subscription with original topic and QoS for reconnection
        self._subscriptions[transformed_topic] = (callback, qos)
        try:
            self._client.subscribe(
                transformed_topic,
                qos=qos,
                options=None,
                properties=self._mqtt_properties,
            )
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            raise SubscriberError(f"Failed to subscribe to topic {transformed_topic}")
        _clb = functools.partial(self._on_msg_internal, callback)
        self._client.message_callback_add(transformed_topic, _clb)
        return transformed_topic

    @staticmethod
    @functools.lru_cache(maxsize=512)
    def _transform_topic_cached(topic: str) -> str:
        """Transform commlib topic to MQTT topic format (cached).

        Transforms:
        - dots (.) to forward slashes (/)
        - trailing asterisk (*) to multi-level wildcard (#)
        - single asterisk wildcards (/*) to single-level wildcard (/+)
        - remaining asterisks (*) to multi-level wildcard (#)

        Args:
            topic: Commlib-style topic string

        Returns:
            MQTT-formatted topic string
        """
        # Replace trailing single asterisk with MQTT's multi-level wildcard
        if topic.endswith("*"):
            topic = topic[:-1] + "#"
        # Replace dots with forward slashes
        # Replace single asterisk wildcards with MQTT's single-level wildcard
        # Replace remaining asterisks with MQTT's multi-level wildcard
        topic = topic.replace(".", "/").replace("/*", "/+").replace("*", "#")
        return topic

    def _transform_topic(self, topic):
        """Transform commlib topic to MQTT topic (wrapper for cached version)."""
        return self._transform_topic_cached(topic)

    def unsubscribe(self, topic: str) -> None:
        assert self._client is not None
        self._client.unsubscribe(topic)

    def _on_msg_internal(
        self, callback: Callable, client: Any, userdata: Any, msg: Any
    ) -> None:
        msg.topic
        _payload = msg.payload
        msg.qos
        msg.retain
        if self._compression != CompressionType.NO_COMPRESSION:
            _payload = deflate(_payload, self._compression)
        msg.payload = _payload
        callback(client, userdata, msg)

    def disconnect(self) -> None:
        assert self._client is not None
        self._client.loop_stop()
        self._client.disconnect()

    def start(self) -> None:
        """start.

        Start the event loop. Cannot create any more endpoints from here on.
        """
        try:
            self.connect()
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as e:
            self.log.error("Could not establish connection to MQTT Broker: %s", e)
            if not self._conn_params.reconnect_attempts:
                return
            self.stop()
            time.sleep(self._conn_params.reconnect_delay)
            self.start()

    def stop(self) -> None:
        """stop.

        Disconnects the client and stops the event loop.
        """
        self._stopped = True
        self.disconnect()

    def loop_forever(self):
        """loop_forever.

        Starts the loop and waits until termination. This is synchronous.
        """
        assert self._client is not None
        self._client.loop_forever()


class Publisher(BasePublisher):
    """Publisher.
    MQTT Publisher
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BasePublisher
            kwargs: See BasePublisher
        """
        self._msg_seq = 0
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def publish(self, msg: PubSubMessage, topic: str = "", key: str = "") -> None:
        """publish.

        Args:
            msg (PubSubMessage): Message to Publish
            topic (str): Optional topic override
            key (str): Optional key

        Returns:
            None:
        """
        assert self._transport is not None
        data = self._prepare_msg(msg)
        _topic = topic if topic else self._topic
        self._transport.publish(_topic, data, qos=MQTTQoS.L0)
        self._msg_seq += 1


class MPublisher(Publisher):
    """MPublisher.
    Multi-Topic Publisher
    """

    def __init__(self, *args, **kwargs):
        super().__init__(topic=None, *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str = "", key: str = "") -> None:
        """publish.

        Args:
            msg (PubSubMessage): msg
            topic (str): topic
            key (str): Optional key

        Returns:
            None:
        """
        assert self._transport is not None
        validate_pubsub_topic_strict(topic)
        data = self._prepare_msg(msg)
        self._transport.publish(topic, data)
        self._msg_seq += 1


class WPublisher:
    """WPublisher.
    MQTT Wrapped-Publisher
    """

    def __init__(
        self,
        mpub: MPublisher,
        topic: str,
        msg_type: Union[PubSubMessage, None] = None,
    ):
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

    @property
    def connected(self):
        return self._mpub.connected

    def publish(self, msg: Union[PubSubMessage, None]) -> None:
        """
        Publish a message to the specified topic.

        Args:
            msg (Union[PubSubMessage, None]): The message to be published.
            Must be of type PubSubMessage if self._msg_type is not None.

        Raises:
            ValueError: If the msg is not of type PubSubMessage when self._msg_type is not None.
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        assert msg is not None
        self._mpub.publish(msg, self._topic)


class Subscriber(BaseSubscriber):
    """Subscriber.
    MQTT Subscriber
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic_strict(self._topic)

    def run_forever(self):
        assert self._transport is not None
        self._transport.start()
        self._transport.subscribe(self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in subscriber")
                    break
            time.sleep(self._LOOP_INTERVAL)
        self._transport.stop()

    def _on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        """_on_message.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        # Received MqttMessage (paho)
        try:
            data, uri = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data)
                else:
                    self.onmessage(self._msg_type(**data))
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _uri = msg.topic
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg.payload)
        return _data, _uri


class WSubscriber(BaseSubscriber):
    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(topic=None, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        self._subs: Dict[str, Callable] = {}

    def run_forever(self):
        """
        Runs the MQTT transport in a loop, subscribing to topics and handling messages.

        This method starts the MQTT transport, subscribes to the topics with their respective
        callbacks, and enters an infinite loop to keep the transport running. The loop can be
        stopped by setting the `_t_stop_event`.

        The method performs the following steps:
        1. Starts the MQTT transport.
        2. Subscribes to the topics with their respective callbacks.
        3. Enters an infinite loop to keep the transport running.
        4. Checks for the `_t_stop_event` to break the loop and stop the transport.

        Note:
            The loop runs indefinitely until the `_t_stop_event` is set. The sleep interval
            within the loop is set to 0.001 seconds to avoid high CPU usage.

        Raises:
            Any exceptions raised by the transport's `start` or `stop` methods.

        """
        assert self._transport is not None
        self._transport.start()
        for topic, callback in self._subs.items():
            self._transport.subscribe(
                topic, functools.partial(self._on_message, callback)
            )
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(self._LOOP_INTERVAL)
        self._transport.stop()

    def subscribe(self, topic: str, callback: Callable) -> None:
        """
        Subscribe to a given MQTT topic with a callback function.

        Args:
            topic (str): The MQTT topic to subscribe to. Must match the TOPIC_PATTERN_REGEX.
            callback (callable): The function to be called when a message is received on the subscribed topic.

        Raises:
            ValueError: If the topic is invalid (i.e., it is '.', '*', '-', '_', None, or does not match the TOPIC_PATTERN_REGEX).
        """
        validate_pubsub_topic_strict(topic)
        self._subs[topic] = callback

    def _on_message(
        self, callback: Callable, client: Any, userdata: Any, msg: Dict[str, Any]
    ) -> None:
        """_on_message.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, uri = self._unpack_comm_msg(msg)
            if callback is not None:
                if self._msg_type is None:
                    callback(data)
                else:
                    callback(self._msg_type(**data))
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Dict[str, Any], str]:
        _uri = msg.topic
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg.payload)
        return _data, _uri


class PSubscriber(BaseSubscriber):
    """PSubscriber."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic(self._topic)

    def run_forever(self):
        assert self._transport is not None
        self._transport.start()
        self._transport.subscribe(self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(self._LOOP_INTERVAL)
        self._transport.stop()

    def _on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            data, topic = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data, topic)
                else:
                    self.onmessage(self._msg_type(**data), topic)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _uri = msg.topic
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg.payload)
        return _data, _uri


class RPCService(BaseRPCService):
    """RPCService.
    MQTT RPC Service class.
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCService
            kwargs: See BaseRPCService
        """
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        assert self._transport is not None
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp, qos=MQTTQoS.L1)

    def _on_request_handle(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        self._executor.submit(self._on_request_internal, client, userdata, msg)

    def _on_request_internal(self, client: Any, userdata: Any, msg: Any):
        try:
            req_msg, uri = self._unpack_comm_msg(
                msg.payload,
                msg.topic,
            )
        except ValueError as exc:
            self.log.warning(
                "Could not unpack request message: %s\nDropping client request!",
                exc,
                exc_info=True,
            )
            return
        try:
            assert self.on_request is not None
            if self._msg_type is None:
                resp = self.on_request(req_msg.data)
            else:
                resp = self.on_request(self._msg_type.Request(**req_msg.data))
                # RPCMessage.Response object here
                resp = resp.model_dump()
            self._send_response(resp, req_msg.header.reply_to)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=True)

    def run_forever(self):
        """run_forever."""
        assert self._transport is not None
        self._transport.start()
        self._transport.subscribe(
            self._rpc_name, self._on_request_handle, qos=MQTTQoS.L1
        )
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(self._LOOP_INTERVAL)
        self._transport.stop()


class RPCServer(BaseRPCServer):
    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCServer
            kwargs: See BaseRPCServer
        """
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        """_send_response.

        Args:
            data (dict): data
            reply_to (str): reply_to
        """
        assert self._transport is not None
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp, qos=MQTTQoS.L1)

    def _on_request_handle(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            self._executor.submit(self._on_request_internal, client, userdata, msg)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)

    def _on_request_internal(self, client: Any, userdata: Any, msg: Any):
        try:
            req_msg, uri = self._unpack_comm_msg(msg)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
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
            clb = self._svc_map[svc_uri][0]
            msg_type = self._svc_map[svc_uri][1]
            if msg_type is None:
                resp = clb(req_msg.data)
            else:
                resp = clb(msg_type.Request(**req_msg.data))
                resp = resp.model_dump()
            self._send_response(resp, req_msg.header.reply_to)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)
            return

    def start_endpoints(self):
        assert self._transport is not None
        for uri in self._svc_map:
            if self._base_uri in (None, ""):
                full_uri = uri
            else:
                full_uri = f"{self._base_uri}.{uri}"
            self.log.info("Registering RPC endpoint <%s>", full_uri)
            self._transport.subscribe(full_uri, self._on_request_handle, qos=MQTTQoS.L1)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[CommRPCMessage, str]:
        """_unpack_comm_msg.

        Unpack payload, header and uri from communcation message.

        Args:
            msg (Any): msg

        Returns:
            Tuple[Any, Any, Any]:
        """
        try:
            assert self._serializer is not None
            _uri = msg.topic
            _payload = self._serializer.deserialize(msg.payload)
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as e:
            raise RPCRequestError(str(e))
        return _req_msg, _uri


class RPCClient(BaseRPCClient):
    """RPCClient.
    MQTT RPC Client
    """

    def __init__(self, *args, **kwargs):
        self._response = None

        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(
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

    def _unpack_comm_msg(self, payload: Any, uri: Optional[str] = None) -> Any:
        if uri is None and hasattr(payload, "topic"):
            uri = payload.topic
            payload = payload.payload
        assert self._serializer is not None
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header, uri

    def _wait_for_response(self, timeout: float = 10.0):
        """_wait_for_response.

        Args:
            timeout (float): timeout
        """
        assert self._transport is not None
        start_t = time.time()
        while self._response is None:
            if not self._transport.is_connected or self._transport.is_stopped:
                raise RPCClientTimeoutError("Transport is not connected")
            elapsed_t = time.time() - start_t
            if elapsed_t >= timeout:
                raise RPCClientTimeoutError(f"Response timeout after {timeout} seconds")
            time.sleep(self._LOOP_INTERVAL)
        return self._response

    def call(self, msg: RPCMessage.Request, timeout: float = 10) -> RPCMessage.Response:
        """
        Sends an RPC request message and waits for a response.

        Args:
            msg (RPCMessage.Request): The RPC request message to be sent.
            timeout (float, optional): The maximum time to wait for a response in seconds. Defaults to 10.

        Returns:
            RPCMessage.Response: The response message received. If no response is received within the timeout period, returns None.
        """
        assert self._transport is not None
        try:
            data = self._prepare_call_data(msg)
        except ValueError as e:
            raise RPCRequestError(str(e))
        _msg = self._prepare_request(data)
        _reply_to = _msg["header"]["reply_to"]
        self._transport.subscribe(_reply_to, self._on_response_wrapper)
        self._transport.publish(self._rpc_name, _msg, qos=MQTTQoS.L1)
        _resp = self._wait_for_response(timeout=timeout)
        self._transport.unsubscribe(_reply_to)
        if _resp is None:
            return None  # type: ignore[return-value]
        # TODO: Evaluate response type and raise exception if necessary
        if self._msg_type is None:
            return _resp
        self._response = None
        return self._msg_type.Response(**_resp)

    def _on_response_wrapper(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        data, header, uri = self._unpack_comm_msg(msg)
        self._response = data


class ActionService(BaseActionService):
    """ActionService.
    MQTT Action Server
    """

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
        self._mpublisher = MPublisher(
            conn_params=self._conn_params,
            debug=self.debug,
        )
        self._feedback_pub = WPublisher(self._mpublisher, self._feedback_topic)
        self._status_pub = WPublisher(self._mpublisher, self._status_topic)
        self._notify_pub = WPublisher(self._mpublisher, self._notify_topic)


class ActionClient(BaseActionClient):
    """ActionClient.
    MQTT Action Client
    """

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=self._conn_params)
        self._task_topic = f"{self._queue_name}/tasks"
        self._result_topic = f"{self._queue_name}/results"
        self._progress_topic = f"{self._queue_name}/progress"
        self._result_sub = None
        self._progress_sub = None

    def run(self, wait: bool = True) -> None:
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
        self._state = EndpointState.CONNECTED

    def stop(self, wait: bool = True) -> None:
        if self._result_sub is not None:
            self._result_sub.stop()
        if self._progress_sub is not None:
            self._progress_sub.stop()
        if self._transport is not None:
            self._transport.stop()
        self._state = EndpointState.DISCONNECTED

    def _send_task(self, envelope: TaskEnvelope) -> None:
        assert self._transport is not None
        data = envelope.model_dump()
        payload = JSONSerializer.serialize(data)
        self._transport.publish(self._task_topic, payload)

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


class TaskWorker(BaseTaskWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=self._conn_params)
        self._task_topic = f"{self._queue_name}/tasks"
        self._result_topic = f"{self._queue_name}/results"
        self._progress_topic = f"{self._queue_name}/progress"
        self._task_sub = None
        self._pub = None

    def run(self, wait: bool = True) -> None:
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        self._transport.start()
        self._pub = Publisher(
            conn_params=self._conn_params,
            topic=self._result_topic,
        )
        self._pub.run()
        self._task_sub = Subscriber(
            conn_params=self._conn_params,
            topic=self._task_topic,
            on_message=self._on_task_msg,
        )
        self._task_sub.run()
        self._state = EndpointState.CONNECTED

    def stop(self, wait: bool = True) -> None:
        self._stop_event.set()
        if self._task_sub is not None:
            self._task_sub.stop()
        if self._pub is not None:
            self._pub.stop()
        if self._transport is not None:
            self._transport.stop()
        self._state = EndpointState.DISCONNECTED

    def _on_task_msg(self, msg) -> None:
        if isinstance(msg, dict):
            data = msg
        else:
            data = msg.model_dump() if hasattr(msg, "model_dump") else msg
        envelope = TaskEnvelope(**data)
        import threading as _threading

        _threading.Thread(
            target=self._process_task,
            args=(envelope,),
            daemon=True,
        ).start()

    def _publish_result(self, result: TaskResult) -> None:
        assert self._transport is not None
        data = result.model_dump()
        payload = JSONSerializer.serialize(data)
        self._transport.publish(self._result_topic, payload)

    def _publish_progress(self, progress: TaskProgress) -> None:
        assert self._transport is not None
        data = progress.model_dump()
        payload = JSONSerializer.serialize(data)
        self._transport.publish(self._progress_topic, payload)

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        super()._send_to_dlq(envelope, error)
        assert self._transport is not None
        data = envelope.model_dump()
        data["error"] = error
        dlq_topic = self._config.get_dlq_name().replace(".", "/")
        payload = JSONSerializer.serialize(data)
        self._transport.publish(dlq_topic, payload)
