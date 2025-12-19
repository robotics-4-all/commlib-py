"""MQTT transport implementation.

Provides MQTT-based pub/sub and RPC communication using paho-mqtt library.
Supports MQTT 3.1.1 and MQTT 5.0 protocols with automatic reconnection.
"""

import functools
import logging
import time
from enum import IntEnum
from typing import Any, Callable, Dict, Tuple, Union

import paho.mqtt.client as mqtt
from paho.mqtt.client import error_string
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

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
from commlib.serializer import JSONSerializer, Serializer
from commlib.transports.base_transport import BaseTransport
from commlib.utils import gen_timestamp

mqtt_logger: logging.Logger = None


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
        serializer: Serializer = JSONSerializer(),
        compression: CompressionType = CompressionType.DEFAULT_COMPRESSION,
        *args,
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
        self._subscriptions = {}  # Track subscriptions for reconnection

    @property
    def is_connected(self) -> bool:
        """is_connected.

        Returns:
            bool: True if connected to broker, False otherwise.
        """
        return self._connected

    def _connect_v3(self):
        properties = None
        self._client = mqtt.Client(
            clean_session=True,
            protocol=self._conn_params.protocol,
            transport=self._conn_params.transport,
        )

        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        # self._client.on_log = self.on_log
        self._client.on_message = self.on_message

        # Configure reconnection delay
        min_delay = int(self._conn_params.reconnect_delay)
        max_delay = min_delay * 10 if min_delay > 0 else 120
        self._client.reconnect_delay_set(min_delay=min_delay, max_delay=max_delay)

        self._client.username_pw_set(self._conn_params.username, self._conn_params.password)
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
        self._client.connect(
            self._conn_params.host,
            int(self._conn_params.port),
            keepalive=self._conn_params.keepalive,
            properties=properties,
        )
        return properties

    def _connect_v5(self):
        properties = Properties(PacketTypes.CONNECT)
        properties.MaximumPacketSize = 20
        self._client = mqtt.Client(
            protocol=self._conn_params.protocol,
            transport=self._conn_params.transport,
        )

        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        # self._client.on_log = self.on_log
        self._client.on_message = self.on_message

        # Configure reconnection delay
        min_delay = int(self._conn_params.reconnect_delay)
        max_delay = min_delay * 10 if min_delay > 0 else 120
        self._client.reconnect_delay_set(min_delay=min_delay, max_delay=min_delay)

        self._client.username_pw_set(self._conn_params.username, self._conn_params.password)
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
        self._client.connect(
            self._conn_params.host,
            int(self._conn_params.port),
            keepalive=self._conn_params.keepalive,
            properties=properties,
        )
        return properties

    def connect(self) -> None:
        if self._connected:
            raise ConnectionError("Transport already connected to broker")
        self._stopped = False
        # Workaround for both v3 and v5 support
        # http://www.steves-internet-guide.com/python-mqtt-client-changes/
        if self._conn_params.protocol == MQTTProtocolType.MQTTv5:
            properties = self._connect_v5()
        else:
            properties = self._connect_v3()
        self._mqtt_properties = properties
        self._client.loop_start()

    def on_connect(
        self, client: Any, userdata: Any, flags: Dict[str, Any], rc: int, properties: Any = None
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
            self._connected = True
            self._report_on_connect()
            self._restore_subscriptions()  # Restore subscriptions after reconnection
        else:
            self.log.error(f"Failed to connect to MQTT Broker: {error_string(rc)}")

    def _report_on_connect(self) -> None:
        self.log.info("Connected to MQTT Broker")
        self.log.debug("MQTT Transport initiated:")
        self.log.debug("- Broker: mqtt://" + f"{self._conn_params.host}:{self._conn_params.port}")
        self.log.debug(f"- Data Serialization: {self._serializer}")
        self.log.debug(f"- Data Compression: {self._compression}")

    def on_disconnect(self, client: Any, userdata: Any, rc: int, unk: Any = None) -> None:
        """on_disconnect.

        Callback for on-disconnect event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            rc (int): Return Code - Internal paho-mqtt
        """
        self._connected = False
        if self._stopped:
            self.log.info("Transport stopped, not attempting reconnection")
            self._client.loop_stop()
            return

        err_msg = ""
        if rc == MQTTReturnCode.AUTHORIZATION_ERROR or rc == MQTTReturnCode.AUTHENTICATION_ERROR:
            err_msg = "Authentication error with MQTT broker"
            self.log.error(err_msg)
        elif rc == MQTTReturnCode.CONNECTION_SUCCESS:
            # Graceful disconnect
            self.log.info("Gracefully disconnected from MQTT broker")
        else:
            err_msg = error_string(rc)
            self.log.warning(f"Disconnected from MQTT broker with: {err_msg}. ")
            self.log.warning(f"Attempting reconnection in {self._conn_params.reconnect_delay}....")

        # paho-mqtt will automatically reconnect when loop is running

    def _restore_subscriptions(self) -> None:
        """Restore all tracked subscriptions after reconnection."""
        if not self._subscriptions:
            return
        self.log.debug(f"Restoring {len(self._subscriptions)} subscriptions after reconnect")
        for topic, (callback, qos) in self._subscriptions.items():
            try:
                _clb = functools.partial(self._on_msg_internal, callback)
                self._client.subscribe(
                    topic, qos=qos, options=None, properties=self._mqtt_properties
                )
                self._client.message_callback_add(topic, _clb)
                self.log.debug(f"Restored subscription to {topic}")
            except Exception as e:
                self.log.warning(f"Failed to restore subscription to {topic}: {e}")

    def on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]) -> None:
        """on_message.

        Callback for on-message event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            msg (Dict[str, Any]): Received message
        """
        pass

    def on_log(self, client: Any, userdata: Any, level, buf):
        self.log.info(level, buf)

    def publish(
        self, topic: str, payload: Dict[str, Any], qos: MQTTQoS = MQTTQoS.L0, retain: bool = False
    ) -> None:
        """publish.

        Args:
            topic (str): topic
            payload (Dict[str, Any]): payload
            qos (int): MQTT QoS Level (see MQTTQoS class)
            retain (bool): If set to True, then it tells the broker to store
                that message on the topic as the “last good message”.
        """
        topic = topic.replace(".", "/")
        pl = self._serializer.serialize(payload)
        if self._compression != CompressionType.NO_COMPRESSION:
            pl = inflate_str(pl)
        self._client.publish(topic, pl, qos=qos, retain=retain, properties=self._mqtt_properties)

    def subscribe(self, topic: str, callback: Callable, qos: MQTTQoS = MQTTQoS.L0) -> str:
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
            self.log.warning(f"Attempt to subscribe to empty topic - {topic}")
            return None
        transformed_topic = self._transform_topic(topic)
        # Track subscription with original topic and QoS for reconnection
        self._subscriptions[transformed_topic] = (callback, qos)
        try:
            self._client.subscribe(
                transformed_topic, qos=qos, options=None, properties=self._mqtt_properties
            )
        except Exception:
            raise SubscriberError(f"Failed to subscribe to topic {transformed_topic}")
        _clb = functools.partial(self._on_msg_internal, callback)
        self._client.message_callback_add(transformed_topic, _clb)
        return transformed_topic

    def _transform_topic(self, topic):
        # topic = topic.replace(".", "/").replace("/*/*/*/", "/+/+/+/").replace(
        #     "/*/*/", "/+/+/").replace("/*/", "/+/").replace("*", "#")
        # Replace trailing single asterisk with MQTT's single-level wildcard
        if topic.endswith("*"):
            topic = topic[:-1] + "#"
        # Replace dots with forward slashes
        # Replace single asterisk wildcards with MQTT's single-level wildcard
        # Replace remaining asterisks with MQTT's multi-level wildcard
        topic = topic.replace(".", "/").replace("/*", "/+").replace("*", "#")
        return topic

    def unsubscribe(self, topic: str) -> None:
        self._client.unsubscribe(topic)

    def _on_msg_internal(self, callback: Callable, client: Any, userdata: Any, msg: Any) -> None:
        _topic = msg.topic
        _payload = msg.payload
        _qos = msg.qos
        _retain = msg.retain
        if self._compression != CompressionType.NO_COMPRESSION:
            _payload = deflate(_payload)
        msg.payload = _payload
        callback(client, userdata, msg)

    def disconnect(self) -> None:
        self._client.disconnect()

    def start(self) -> None:
        """start.

        Start the event loop. Cannot create any more endpoints from here on.
        """
        try:
            self.connect()
        except Exception as e:
            self.log.error(f"Could not establish connection to MQTT Broker: {e}")
            self.stop()
            time.sleep(self._conn_params.reconnect_delay)
            self.start()

    def stop(self) -> None:
        """stop.

        Disconnects the client and stops the event loop.
        """
        self._stopped = True
        self.disconnect()
        self._client.loop_stop()

    def loop_forever(self):
        """loop_forever.

        Starts the loop and waits until termination. This is synchronous.
        """
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

    def publish(self, msg: PubSubMessage) -> None:
        """publish.

        Args:
            msg (PubSubMessage): Message to Publish

        Returns:
            None:
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        self._transport.publish(self._topic, data, qos=MQTTQoS.L0)
        self._msg_seq += 1


class MPublisher(Publisher):
    """MPublisher.
    Multi-Topic Publisher
    """

    def __init__(self, *args, **kwargs):
        super().__init__(topic=None, *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        """publish.

        Args:
            msg (PubSubMessage): msg
            topic (str): topic

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
        self._transport.start()
        self._transport.subscribe(self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(0.001)
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
                    _clb = functools.partial(self.onmessage, data)
                else:
                    _clb = functools.partial(self.onmessage, self._msg_type(**data))
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _uri = msg.topic
        _data = self._serializer.deserialize(msg.payload)
        return _data, _uri


class WSubscriber(BaseSubscriber):

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(topic=None, *args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        self._subs: Dict[str, callable] = {}

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
        self._transport.start()
        for topic, callback in self._subs.items():
            self._transport.subscribe(topic, functools.partial(self._on_message, callback))
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(0.001)
        self._transport.stop()

    def subscribe(self, topic: str, callback: callable) -> None:
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
        self, callback: callable, client: Any, userdata: Any, msg: Dict[str, Any]
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
                    _clb = functools.partial(callback, data)
                else:
                    _clb = functools.partial(callback, self._msg_type(**data))
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Dict[str, Any], str]:
        _uri = msg.topic
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
        self._transport.start()
        self._transport.subscribe(self._topic, self._on_message)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(0.001)
        self._transport.stop()

    def _on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            data, topic = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, data, topic)
                else:
                    _clb = functools.partial(self.onmessage, self._msg_type(**data), topic)
                _clb()
        except Exception:
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _uri = msg.topic
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
        super(RPCService, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp, qos=MQTTQoS.L1)

    def _on_request_handle(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        self._executor.submit(self._on_request_internal, client, userdata, msg)

    def _on_request_internal(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            req_msg, uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.error(
                f"Could not unpack request message: {exc}\n" "Dropping client request!",
                exc_info=True,
            )
            return
        try:
            if self._msg_type is None:
                resp = self.on_request(req_msg.data)
            else:
                resp = self.on_request(self._msg_type.Request(**req_msg.data))
                # RPCMessage.Response object here
                resp = resp.model_dump()
            self._send_response(resp, req_msg.header.reply_to)
        except Exception as exc:
            self.log.error(str(exc), exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[CommRPCMessage, str]:
        try:
            _uri = msg.topic
            _payload = self._serializer.deserialize(msg.payload)
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
        except Exception as e:
            raise RPCRequestError(str(e))
        return _req_msg, _uri

    def run_forever(self):
        """run_forever."""
        self._transport.start()
        self._transport.subscribe(self._rpc_name, self._on_request_handle, qos=MQTTQoS.L1)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            time.sleep(0.001)
        self._transport.stop()


class RPCServer(BaseRPCServer):
    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCServer
            kwargs: See BaseRPCServer
        """
        super(RPCServer, self).__init__(*args, **kwargs)
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
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        self._transport.publish(reply_to, _resp, qos=MQTTQoS.L1)

    def _on_request_handle(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            self._executor.submit(self._on_request_internal, client, userdata, msg)
        except Exception as exc:
            self.log.error(str(exc), exc_info=False)

    def _on_request_internal(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        try:
            req_msg, uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.error(
                f"Could not unpack request message: {exc}" "\nDropping client request!",
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

    def start_endpoints(self):
        for uri in self._svc_map:
            if self._base_uri in (None, ""):
                full_uri = uri
            else:
                full_uri = f"{self._base_uri}.{uri}"
            self.log.info(f"Registering RPC endpoint <{full_uri}>")
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
            _uri = msg.topic
            _payload = self._serializer.deserialize(msg.payload)
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
        except Exception as e:
            raise RPCRequestError(str(e))
        return _req_msg, _uri


class RPCClient(BaseRPCClient):
    """RPCClient.
    MQTT RPC Client
    """

    def __init__(self, *args, **kwargs):
        self._response = None

        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _gen_queue_name(self):
        """_gen_queue_name."""
        return f"rpc-{self._gen_random_id()}"

    def _prepare_request(self, data: Dict[str, Any]):
        """_prepare_request.

        Args:
            data:
        """
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.model_dump()

    def _on_response_wrapper(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        """_on_response_wrapper.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, header, uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.log.error(exc, exc_info=True)
            data = {}
        finally:
            self._response = data

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Any, Any, Any]:
        _uri = msg.topic
        _payload = self._serializer.deserialize(msg.payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header, _uri

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
            data = msg
        else:
            if not isinstance(msg, self._msg_type.Request):
                raise ValueError("Message type not valid")
            data = msg.model_dump()

        self._response = None

        _msg = self._prepare_request(data)
        _reply_to = _msg["header"]["reply_to"]

        self._transport.subscribe(_reply_to, callback=self._on_response_wrapper, qos=MQTTQoS.L1)
        start_t = time.time()
        self._transport.publish(self._rpc_name, _msg, qos=MQTTQoS.L1)
        _resp = self._wait_for_response(timeout=timeout)
        elapsed_t = time.time() - start_t
        self._delay = elapsed_t
        self._transport.unsubscribe(_reply_to)

        if self._msg_type is None:
            return _resp
        else:
            return self._msg_type.Response(**_resp)


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
            debug=self.debug,
        )
        self._feedback_sub = Subscriber(
            msg_type=_ActionFeedbackMessage,
            conn_params=self._conn_params,
            topic=self._feedback_topic,
            on_message=self._on_feedback,
            debug=self.debug,
        )
