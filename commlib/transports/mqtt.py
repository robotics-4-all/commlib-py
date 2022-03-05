"""
MQTT Implementation
"""

import functools
import time
from enum import IntEnum
from typing import Any, Dict, Tuple

import paho.mqtt.client as mqtt

from commlib.action import (BaseActionClient, BaseActionService,
                            _ActionCancelMessage, _ActionFeedbackMessage,
                            _ActionGoalMessage, _ActionResultMessage,
                            _ActionStatusMessage)
from commlib.events import BaseEventEmitter, Event
from commlib.exceptions import RPCClientTimeoutError
from commlib.logger import Logger
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import BaseRPCClient, BaseRPCServer, BaseRPCService
from commlib.serializer import Serializer, JSONSerializer
from commlib.utils import gen_timestamp


class MQTTReturnCode(IntEnum):
    CONNECTION_SUCCESS = 0
    INCORRECT_PROTOCOL_VERSION = 1
    INVALID_CLIENT_ID = 2
    SERVER_UNAVAILABLE = 3
    AUTHENTICATION_ERROR = 4
    AUTHORIZATION_ERROR = 5


class MQTTProtocolType(IntEnum):
    MQTTv31 = 1
    MQTTv311 = 2


class Credentials:
    def __init__(self, username: str = '', password: str = ''):
        self.username = username
        self.password = password


class ConnectionParameters:
    __slots__ = ['host', 'port', 'creds', 'protocol']
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 1883,
                 protocol: MQTTProtocolType = MQTTProtocolType.MQTTv311,
                 creds: Credentials = Credentials()):
        """__init__.

        Args:
            host (str): host
            port (int): port
            protocol (MQTTProtocolType): protocol
            creds (Credentials): creds
        """
        self.host = host
        self.port = port
        self.protocol = protocol
        self.creds = creds

    @property
    def credentials(self):
        return self.creds


class MQTTTransport:
    """MQTTTransport.
    """

    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 serializer: Serializer = JSONSerializer(),
                 logger: Logger = None):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            logger (Logger): logger
        """
        self._conn_params = conn_params
        self._logger = logger
        self._connected = False

        self._serializer = serializer

        self.logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._client = mqtt.Client(clean_session=True,
                                   protocol=mqtt.MQTTv311,
                                   transport='tcp')

        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        # self._client.on_log = self.on_log
        self._client.on_message = self.on_message

        self._client.username_pw_set(self._conn_params.creds.username,
                                     self._conn_params.creds.password)

        self._client.connect(self._conn_params.host,
                             int(self._conn_params.port),
                             60)

    @property
    def is_connected(self):
        return self._connected

    def on_connect(self, client: Any, userdata: Any,
                   flags: Dict[str, Any], rc: int):
        """on_connect.

        Callback for on-connect event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            flags (Dict[str, Any]): Interla paho-mqtt flags
            rc (int): Return Code - Internal paho-mqtt
        """
        if rc == MQTTReturnCode.CONNECTION_SUCCESS:
            self.logger.debug(
                f"Connected to MQTT broker <{self._conn_params.host}:{self._conn_params.port}>")
            self._connected = True

    def on_disconnect(self, client: Any, userdata: Any,
                      rc: Dict[str, Any]):
        """on_disconnect.

        Callback for on-disconnect event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            rc (int): Return Code - Internal paho-mqtt
        """
        if rc != 0:
            self.logger.warn("Unexpected disconnection from MQTT Broker.")

    def on_message(self, client: Any, userdata: Any,
                   msg: Dict[str, Any]):
        """on_message.

        Callback for on-message event.

        Args:
            client (Any): Internal paho-mqtt
            userdata (Any): Internal paho-mqtt userdata
            msg (Dict[str, Any]): Received message
        """
        raise NotImplementedError()

    def on_log(self, client: Any, userdata: Any,
               level, buf):
        ## SPAM output
        # self.logger.debug(f'MQTT Log: {buf}')
        pass

    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 0,
                retain: bool = False, confirm_delivery: bool = False):
        """publish.

        Args:
            topic (str): topic
            payload (Dict[str, Any]): payload
            qos (int): qos
            retain (bool): retain
            confirm_delivery (bool): confirm_delivery
        """
        topic = topic.replace('.', '/')
        pl = self._serializer.serialize(payload)
        ph = self._client.publish(topic, pl, qos=qos, retain=retain)
        if confirm_delivery:
            ph.wait_for_publish()

    def subscribe(self, topic: str, callback: Any, qos: int = 0) -> str:
        """subscribe.

        Args:
            topic (str): topic
            callback (Any): callback
            qos (int): qos

        Returns:
            str:
        """
        ## Adds subtopic specific callback handlers
        topic = topic.replace('.', '/').replace('*', '#')
        self._client.subscribe(topic, qos)
        self._client.message_callback_add(topic, callback)
        return topic

    def start_loop(self):
        """start_loop.

        Start the event loop. Cannot create any more endpoints from here on.
        """
        self._client.loop_start()

    def stop_loop(self):
        """stop_loop.

        Stops the event loop.
        """
        self._client.loop_stop(force=True)

    def loop_forever(self):
        """loop_forever.

        Starts the loop and waits until termination. This is synchronous.
        """
        self._client.loop_forever()


class Publisher(BasePublisher):
    """Publisher.
    MQTT Publisher
    """

    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BasePublisher
            kwargs: See BasePublisher
        """
        self._msg_seq = 0
        self.conn_params = conn_params
        super().__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)
        self._transport.start_loop()

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
            data = msg.as_dict()
        self._transport.publish(self._topic, data)
        self._msg_seq += 1


class MPublisher(Publisher):
    """MPublisher.
    Multi-Topic Publisher
    """

    def __init__(self, *args, **kwargs):
        super(MPublisher, self).__init__(topic='*', *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        """publish.

        Args:
            msg (PubSubMessage): msg
            topic (str): topic

        Returns:
            None:
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.as_dict()
        self._transport.publish(topic, data)
        self._msg_seq += 1


class Subscriber(BaseSubscriber):
    """Subscriber.
    MQTT Subscriber
    """

    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        self.conn_params = conn_params
        super(Subscriber, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)

    def run(self):
        self._topic = self._transport.subscribe(self._topic,
                                                self._on_message)
        self._transport.start_loop()
        self.logger.debug(f'Started Subscriber: <{self._topic}>')

    def run_forever(self):
        self._transport.subscribe(self._topic,
                                  self._on_message)
        self.logger.debug(f'Started Subscriber: <{self._topic}>')
        self._transport.loop_forever()

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
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**data))
                _clb()
        except Exception:
            self.logger.error('Exception caught in _on_message', exc_info=True)

    def _unpack_comm_msg(self, msg: Any) -> Tuple:
        _uri = msg.topic
        _data = self._serializer.deserialize(msg.payload)
        return _data, _uri


class PSubscriber(Subscriber):
    """PSubscriber.
    """

    def _on_message(self, client: Any, userdata: Any, msg: Dict[str, Any]):
        """_on_message.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, topic = self._unpack_comm_msg(msg)
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage,
                                             data,
                                             topic)
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**data),
                                             topic)
                _clb()
        except Exception:
            self.logger.error('Exception caught in _on_message', exc_info=True)


class RPCService(BaseRPCService):
    """RPCService.
    MQTT RPC Service class.
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseRPCService
            kwargs: See BaseRPCService
        """
        self.conn_params = conn_params
        super(RPCService, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)

    def _send_response(self, data: dict, reply_to: str):
        """_send_response.

        Args:
            data (dict): data
            reply_to (str): reply_to
        """
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.as_dict()
        self._transport.publish(reply_to, _resp)

    def _on_request_internal(self, client: Any, userdata: Any,
                             msg: Dict[str, Any]):
        """_on_request_internal.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, header, uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.logger.error('Could not unpack message. Dropping message!',
                              exc_info=False)
            return
        try:
            if self._msg_type is None:
                resp = self.on_request(data)
            else:
                resp = self.on_request(self._msg_type.Request(**data))
                ## RPCMessage.Response object here
                resp = resp.as_dict()
        except Exception as exc:
            self.logger.error(str(exc), exc_info=False)
            resp = {}
        reply_to = header['reply_to']
        self._send_response(resp, reply_to)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Any, Any, Any]:
        """_unpack_comm_msg.

        Unpack payload, header and uri from communcation message.

        Args:
            msg (Any): msg

        Returns:
            Tuple[Any, Any, Any]:
        """
        _uri = msg.topic
        _payload = self._serializer.deserialize(msg.payload)
        _data = _payload['data']
        _header = _payload['header']
        return _data, _header, _uri

    def run_forever(self):
        """run_forever.
        """
        self._transport.subscribe(self._rpc_name,
                                  self._on_request_internal)
        self._transport.start_loop()
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.logger.debug('Stop event caught in thread')
                    break
            time.sleep(0.001)
        self._transport.stop_loop()

    def stop(self):
        self._t_stop_event.set()


class RPCServer(BaseRPCServer):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseRPCServer
            kwargs: See BaseRPCServer
        """
        self.conn_params = conn_params
        super(RPCServer, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)
        for uri in self._svc_map:
            callback = self._svc_map[uri][0]
            msg_type = self._svc_map[uri][1]
            self._register_endpoint(uri, callback, msg_type)

    def _send_response(self, data: dict, reply_to: str):
        """_send_response.

        Args:
            data (dict): data
            reply_to (str): reply_to
        """
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.as_dict()
        self._transport.publish(reply_to, _resp)

    def _on_request_internal(self, client: Any, userdata: Any,
                             msg: Dict[str, Any]):
        """_on_request_internal.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, header, uri = self._unpack_comm_msg(msg)
            reply_to = header['reply_to']
            uri = uri.replace('/', '.')
            svc_uri = uri.replace(self._base_uri, '')
            if svc_uri[0] == '.':
                svc_uri = svc_uri[1:]
            if svc_uri not in self._svc_map:
                return
            else:
                clb = self._svc_map[svc_uri][0]
                msg_type = self._svc_map[svc_uri][1]
                if msg_type is None:
                    resp = clb(data)
                else:
                    resp = clb(msg_type.Request(**data))
                    resp = resp.as_dict()
        except Exception as exc:
            self.logger.error(exc, exc_info=False)
            resp = {}
            return
        self._send_response(resp, reply_to)

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Any, Any, Any]:
        """_unpack_comm_msg.

        Args:
            msg (Any): msg

        Returns:
            Tuple[Any, Any, Any]:
        """
        _uri = msg.topic
        _payload = self._serializer.deserialize(msg.payload)
        _data = _payload['data']
        _header = _payload['header']
        return _data, _header, _uri

    def _register_endpoint(self, uri: str, callback: Any,
                           msg_type: RPCMessage = None):
        self._svc_map[uri] = (callback, msg_type)
        if self._base_uri in (None, ''):
            full_uri = uri
        else:
            full_uri = f'{self._base_uri}.{uri}'
        self.logger.info(f'Registering endpoint <{full_uri}>')
        self._transport.subscribe(full_uri, self._on_request_internal)

    def run_forever(self):
        """run_forever.
        """
        self._transport.start_loop()
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.logger.debug('Stop event caught in thread')
                    break
            time.sleep(0.001)
        self._transport.stop_loop()

    def stop(self):
        self._t_stop_event.set()


class RPCClient(BaseRPCClient):
    """RPCClient.
    MQTT RPC Client
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseRPCClient
            kwargs: See BaseRPCClient
        """
        self.conn_params = conn_params
        self._response = None

        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)
        self._transport.start_loop()

    def _gen_queue_name(self):
        """_gen_queue_name.
        """
        return f'rpc-{self._gen_random_id()}'

    def _prepare_request(self, data):
        """_prepare_request.

        Args:
            data:
        """
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.as_dict()

    def _on_response_wrapper(self, client: Any, userdata: Any,
                             msg: Dict[str, Any]):
        """_on_response_wrapper.

        Args:
            client (Any): client
            userdata (Any): userdata
            msg (Dict[str, Any]): msg
        """
        try:
            data, header, uri = self._unpack_comm_msg(msg)
        except Exception as exc:
            self.logger.error(exc, exc_info=True)
            data = {}
        self._response = data

    def _unpack_comm_msg(self, msg: Any) -> Tuple[Any, Any, Any]:
        _uri = msg.topic
        _payload = self._serializer.deserialize(msg.payload)
        _data = _payload['data']
        _header = _payload['header']
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
                raise RPCClientTimeoutError(
                    f'Response timeout after {timeout} seconds')
            time.sleep(0.001)
        return self._response

    def call(self, msg: RPCMessage.Request,
             timeout: float = 30) -> RPCMessage.Response:
        """call.

        Args:
            msg (RPCMessage.Request): msg
            timeout (float): timeout
        """
        if self._msg_type is None:
            data = msg
        else:
            if not isinstance(msg, self._msg_type.Request):
                raise ValueError('Message type not valid')
            data = msg.as_dict()

        self._response = None

        _msg = self._prepare_request(data)
        _reply_to = _msg['header']['reply_to']

        self._transport.subscribe(_reply_to, callback=self._on_response_wrapper)
        start_t = time.time()
        self._transport.publish(self._rpc_name, _msg)
        _resp = self._wait_for_response(timeout=timeout)
        elapsed_t = time.time() - start_t
        self._delay = elapsed_t

        if self._msg_type is None:
            return _resp
        else:
            return self._msg_type.Response(**_resp)


class ActionService(BaseActionService):
    """ActionService.
    MQTT Action Server
    """

    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseActionService
            kwargs: See BaseActionService
        """
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args:
            kwargs:
        """
        super(ActionService, self).__init__(*args, **kwargs)

        self._goal_rpc = RPCService(msg_type=_ActionGoalMessage,
                                    rpc_name=self._goal_rpc_uri,
                                    conn_params=conn_params,
                                    on_request=self._handle_send_goal,
                                    logger=self._logger,
                                    debug=self.debug)
        self._cancel_rpc = RPCService(msg_type=_ActionCancelMessage,
                                      rpc_name=self._cancel_rpc_uri,
                                      conn_params=conn_params,
                                      on_request=self._handle_cancel_goal,
                                      logger=self._logger,
                                      debug=self.debug)
        self._result_rpc = RPCService(msg_type=_ActionResultMessage,
                                      rpc_name=self._result_rpc_uri,
                                      conn_params=conn_params,
                                      on_request=self._handle_get_result,
                                      logger=self._logger,
                                      debug=self.debug)
        self._feedback_pub = Publisher(msg_type=_ActionFeedbackMessage,
                                       topic=self._feedback_topic,
                                       conn_params=conn_params,
                                       logger=self._logger,
                                       debug=self.debug)
        self._status_pub = Publisher(msg_type=_ActionStatusMessage,
                                     topic=self._status_topic,
                                     conn_params=conn_params,
                                     logger=self._logger,
                                     debug=self.debug)


class ActionClient(BaseActionClient):
    """ActionClient.
    MQTT Action Client
    """

    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection Parameters
            args: See BaseActionClient
            kwargs: See BaseActionClient
        """
        super(ActionClient, self).__init__(*args, **kwargs)

        self._goal_client = RPCClient(msg_type=_ActionGoalMessage,
                                      rpc_name=self._goal_rpc_uri,
                                      conn_params=conn_params,
                                      logger=self._logger,
                                      debug=self.debug)
        self._cancel_client = RPCClient(msg_type=_ActionCancelMessage,
                                        rpc_name=self._cancel_rpc_uri,
                                        conn_params=conn_params,
                                        logger=self._logger,
                                        debug=self.debug)
        self._result_client = RPCClient(msg_type=_ActionResultMessage,
                                        rpc_name=self._result_rpc_uri,
                                        conn_params=conn_params,
                                        logger=self._logger,
                                        debug=self.debug)
        self._status_sub = Subscriber(msg_type=_ActionStatusMessage,
                                      conn_params=conn_params,
                                      topic=self._status_topic,
                                      on_message=self._on_status)
        self._feedback_sub = Subscriber(msg_type=_ActionFeedbackMessage,
                                        conn_params=conn_params,
                                        topic=self._feedback_topic,
                                        on_message=self._on_feedback)
        self._status_sub.run()
        self._feedback_sub.run()


class EventEmitter(BaseEventEmitter):
    """EventEmitter.
    MQTT Event Emitter class
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection Parameters
            args: See BaseEventEmitter
            kwargs: See BaseEventEmitter
        """
        super(EventEmitter, self).__init__(*args, **kwargs)

        self._transport = MQTTTransport(conn_params=conn_params,
                                        serializer=self._serializer,
                                        logger=self._logger)
        self._transport.start_loop()

    def send_event(self, event: Event) -> None:
        """send_event.

        Args:
            event (Event): The Event to send.

        Returns:
            None:
        """
        _msg = event.as_dict()
        self.logger.debug(f'Firing Event: {event.name}:<{event.uri}>')
        self._transport.publish(event.uri, _msg)
