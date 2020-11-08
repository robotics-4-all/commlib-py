import functools
import sys
import time
import json
import uuid
import datetime

from collections import deque
from threading import Semaphore, Thread, Event as ThreadEvent
import logging
from typing import OrderedDict, Any
from inspect import signature
from enum import IntEnum

from commlib.logger import Logger, LoggingLevel
from commlib.serializer import ContentType
from commlib.rpc import BaseRPCService, BaseRPCClient
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.action import (
    BaseActionServer, BaseActionClient, _ActionGoalMessage,
    _ActionResultMessage, _ActionGoalMessage, _ActionCancelMessage,
    _ActionStatusMessage, _ActionFeedbackMessage
)
from commlib.events import BaseEventEmitter, Event
from commlib.msg import RPCMessage, PubSubMessage, ActionMessage
from commlib.utils import gen_timestamp
from commlib.exceptions import RPCClientTimeoutError

import paho.mqtt.client as mqtt


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


class Credentials(object):
    def __init__(self, username: str = '', password: str = ''):
        self.username = username
        self.password = password


class ConnectionParameters(object):
    __slots__ = ['host', 'port', 'creds', 'protocol']
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 1883,
                 protocol: MQTTProtocolType = MQTTProtocolType.MQTTv311,
                 creds: Credentials = Credentials()):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.creds = creds


class MQTTTransport(object):
    def __init__(self, conn_params=ConnectionParameters(), logger=None):
        self._conn_params = conn_params
        self._logger = logger
        self._connected = False

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

        self._client.connect(self._conn_params.host, self._conn_params.port, 60)

    @property
    def is_connected(self):
        return self._connected

    def on_connect(self, client, userdata, flags, rc):
        if rc == MQTTReturnCode.CONNECTION_SUCCESS:
            self.logger.debug(
                f"Connected to MQTT broker <{self._conn_params.host}:{self._conn_params.port}>")
            self._connected = True

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warn("Unexpected disconnection from MQTT Broker.")

    def on_message(self, client, userdata, msg):
        raise NotImplementedError()

    def on_log(self, client, userdata, level, buf):
        ## SPAM output
        # self.logger.debug(f'MQTT Log: {buf}')
        pass

    def publish(self, topic: str, payload: dict, qos: int = 0,
                retain: bool = False,
                confirm_delivery: bool = False):
        topic = topic.replace('.', '/')
        ph = self._client.publish(topic, payload, qos=qos, retain=retain)
        if confirm_delivery:
            ph.wait_for_publish()

    def subscribe(self, topic: str, callback: callable, qos: int = 0):
        ## Adds subtopic specific callback handlers
        topic = topic.replace('.', '/').replace('*', '#')
        self._client.subscribe(topic, qos)
        self._client.message_callback_add(topic, callback)

    def start_loop(self):
        self._client.loop_start()

    def stop_loop(self):
        self._client.loop_stop(force=True)

    def loop_forever(self):
        self._client.loop_forever()


class Publisher(BasePublisher):
    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        self._msg_seq = 0
        self.conn_params = conn_params
        super(Publisher, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        logger=self._logger)
        self._transport.start_loop()

    def publish(self, msg: PubSubMessage) -> None:
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()
        _msg = self._prepare_msg(data)
        _msg = self._serializer.serialize(_msg)
        self._transport.publish(self._topic, _msg)
        self._msg_seq += 1

    def _prepare_msg(self, data):
        meta = {
            'timestamp': int(datetime.datetime.now(
                datetime.timezone.utc).timestamp() * 1000000),
            'properties': {
                'content_type': self._serializer.CONTENT_TYPE,
                'content_encoding': self._serializer.CONTENT_ENCODING
            }
        }
        _msg = {
            'data': data,
            'meta': meta
        }
        return _msg


class MPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        super(MPublisher, self).__init__(topic='*', *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()
        _msg = self._prepare_msg(data)
        _msg = self._serializer.serialize(_msg)
        self._transport.publish(topic, _msg)
        self._msg_seq += 1


class Subscriber(BaseSubscriber):
    def __init__(self,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        self.conn_params = conn_params
        super(Subscriber, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        logger=self._logger)

    def run(self):
        self._transport.subscribe(self._topic,
                                  self._on_message)
        self._transport.start_loop()
        self.logger.info(f'Started Subscriber: <{self._topic}>')

    def _on_message(self, client, userdata, msg):
        try:
            _topic = msg.topic
            _payload = json.loads(msg.payload)
            data = _payload['data']
            meta = _payload['meta']
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, OrderedDict(data))
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**data))
                _clb()
        except Exception:
            self.logger.error('Exception caught in _on_message', exc_info=True)


class PSubscriber(Subscriber):
    def _on_message(self, client, userdata, msg):
        try:
            _topic = msg.topic
            _payload = json.loads(msg.payload)
            data = _payload['data']
            meta = _payload['meta']
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage,
                                             OrderedDict(data),
                                             _topic)
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**data),
                                             _topic)
                _clb()
        except Exception:
            self.logger.error('Exception caught in _on_message', exc_info=True)


class RPCService(BaseRPCService):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        self.conn_params = conn_params
        super(RPCService, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        logger=self._logger)

    def _send_response(self, data, reply_to):
        meta = {
            'timestamp': int(datetime.datetime.now(
                datetime.timezone.utc).timestamp() * 1000000),
            'properties': {
                'content_type': self._serializer.CONTENT_TYPE,
                'content_encoding': self._serializer.CONTENT_ENCODING,
                'msg_type': ''  ## TODO
            }
        }
        _resp = {
            'data': data,
            'meta': meta
        }
        _resp = self._serializer.serialize(_resp)
        self._transport.publish(reply_to, _resp)

    def _on_request_wrapper(self, client, userdata, msg):
        try:
            _topic = msg.topic
            _payload = json.loads(msg.payload)
            data = _payload['data']
            meta = _payload['meta']
            if self._msg_type is None:
                resp = self.on_request(OrderedDict(data))
            else:
                resp = self.on_request(self._msg_type.Request(**data))
                ## RPCMessage.Response object here
                resp = resp.as_dict()
        except Exception as exc:
            self.logger.error(str(exc), exc_info=False)
            resp = {}
        reply_to = meta['reply_to']
        self._send_response(resp, reply_to)

    def run_forever(self):
        self._transport.subscribe(self._rpc_name,
                                  self._on_request_wrapper)
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
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        self.conn_params = conn_params
        self._response = None

        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = MQTTTransport(conn_params=conn_params,
                                        logger=self._logger)
        self._transport.start_loop()

    def __gen_queue_name(self):
        return f'rpc-{self._gen_random_id()}'

    def __prepare_request(self, data):
        _reply_to = self.__gen_queue_name()
        meta = {
            'timestamp': int(datetime.datetime.now(
                datetime.timezone.utc).timestamp() * 1000000),
            'reply_to': _reply_to,
            'properties': {
                'content_type': self._serializer.CONTENT_TYPE,
                'content_encoding': self._serializer.CONTENT_ENCODING
            }
        }
        _req = {
            'data': data,
            'meta': meta
        }
        return _req

    def _on_response_wrapper(self, client, userdata, msg):
        try:
            _topic = msg.topic
            _payload = json.loads(msg.payload)
            data = _payload['data']
            meta = _payload['meta']
        except Exception as exc:
            self.logger.error(exc, exc_info=True)
            data = {}
        self._response = data

    def _wait_for_response(self, timeout: float = 10.0):
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
        ## TODO: Evaluate msg type passed here.
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()

        self._response = None

        _msg = self.__prepare_request(data)
        _reply_to = _msg['meta']['reply_to']
        _msg = self._serializer.serialize(_msg)

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


class ActionServer(BaseActionServer):
    def __init__(self,
                 action_name: str,
                 msg_type: ActionMessage,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        super(ActionServer, self).__init__(action_name, msg_type,
                                           *args, **kwargs)

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
    def __init__(self,
                 action_name: str,
                 msg_type: ActionMessage,
                 conn_params: ConnectionParameters = ConnectionParameters(),
                 *args, **kwargs):
        super(ActionClient, self).__init__(action_name, msg_type,
                                           *args, **kwargs)

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
