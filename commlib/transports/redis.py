import functools
import sys
import time
import atexit
import signal
import json
import uuid
import hashlib
import datetime
from typing import OrderedDict, Any

import redis

from commlib.logger import Logger, LoggingLevel
from commlib.rpc import BaseRPCService, BaseRPCClient
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.action import (
    BaseActionServer, BaseActionClient, _ActionGoalMessage,
    _ActionResultMessage, _ActionGoalMessage, _ActionCancelMessage,
    _ActionStatusMessage, _ActionFeedbackMessage
)

from commlib.events import BaseEventEmitter, Event
from commlib.msg import RPCMessage, PubSubMessage, ActionMessage


class Credentials(object):
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password


class ConnectionParametersBase(object):
    __slots__ = ['db', 'creds']

    def __init__(self, db=0, creds=None):
        self.db = db

        if creds is None:
            creds = Credentials()
        self.creds = creds

    @property
    def credentials(self):
        return self.creds


class TCPConnectionParameters(ConnectionParametersBase):
    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        super(TCPConnectionParameters, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port


class UnixSocketConnectionParameters(ConnectionParametersBase):
    def __init__(self, unix_socket='/tmp/redis.sock', *args, **kwargs):
        super(UnixSocketConnectionParameters, self).__init__(*args, **kwargs)
        self.unix_socket = unix_socket


class ConnectionParameters(TCPConnectionParameters):
    def __init__(self, *args, **kwargs):
        super(ConnectionParameters, self).__init__(*args, **kwargs)


class Connection(redis.Redis):
    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)


class RedisTransport(object):
    def __init__(self, conn_params=None, logger=None):
        conn_params = TCPConnectionParameters() if \
            conn_params is None else conn_params
        if isinstance(conn_params, UnixSocketConnectionParameters):
            self._redis = Connection(
                unix_socket_path=conn_params.unix_socket,
                db=conn_params.db, decode_responses=True)
        elif isinstance(conn_params, TCPConnectionParameters):
            self._redis = Connection(host=conn_params.host,
                                     port=conn_params.port,
                                     db=conn_params.db,
                                     decode_responses=True)

        self._conn_params = conn_params
        self.logger = Logger(self.__class__.__name__) if \
            logger is None else logger
        assert isinstance(self.logger, Logger)
        self._rsub = self._redis.pubsub()

    def delete_queue(self, queue_name):
        # self.logger.debug('Removing message queue: <{}>'.format(queue_name))
        self._redis.delete(queue_name)

    def push_msg_to_queue(self, queue_name, payload):
        self._redis.rpush(queue_name, payload)

    def publish(self, queue_name: str, payload: dict):
        self._redis.publish(queue_name, payload)

    def subscribe(self, topic: str, callback: callable):
        self._sub = self._rsub.subscribe(
            **{topic: callback})
        self._rsub.get_message()
        t = self._rsub.run_in_thread(0.001, daemon=True)
        return t

    def wait_for_msg(self, queue_name: str, timeout=10):
        try:
            msgq, payload = self._redis.blpop(queue_name, timeout=timeout)
        except Exception as exc:
            self.logger.error(exc)
            msgq = ''
            payload = None
        return msgq, payload


class _RPCService(BaseRPCService):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        super(_RPCService, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
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
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request(self, data: dict, meta: dict):
        try:
            resp = self.on_request(data)
        except Exception as exc:
            self.logger.error(str(exc), exc_info=False)
            resp = {}
        reply_to = meta['reply_to']
        self._send_response(resp, reply_to)

    def run_forever(self):
        self._transport.delete_queue(self._rpc_name)
        while True:
            msgq, payload = self._transport.wait_for_msg(self._rpc_name,
                                                         timeout=0)

            self.__detach_request_handler(payload)
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.logger.debug('Stop event caught in thread')
                    self._transport.delete_queue(self._rpc_name)
                    break
            time.sleep(0.001)

    def stop(self):
        self._t_stop_event.set()

    def __detach_request_handler(self, payload):
        payload = self._serializer.deserialize(payload)
        data = payload['data']
        meta = payload['meta']
        self.logger.debug(f'RPC Request <{self._rpc_name}>')
        _future = self.__exec_in_thread(
            functools.partial(self._on_request, data, meta)
        )
        return _future

    def __exec_in_thread(self, on_request):
        _future = self._executor.submit(on_request)
        return _future


class RPCService(_RPCService):
    def __init__(self,
                 msg_type: RPCMessage,
                 *args, **kwargs):
        super(RPCService, self).__init__(*args, **kwargs)
        self._msg_type = msg_type

    def _on_request(self, msg: RPCMessage.Request, meta):
        try:
            resp = self.on_request(msg)
        except Exception as exc:
            self.logger.error(str(exc), exc_info=False)
            resp = self._msg_type.Response()
        if not isinstance(resp, self._msg_type.Response):
            self.logger.error('Wrong Response type!')
            resp = self._msg_type.Response()
        data = resp.as_dict()
        reply_to = meta['reply_to']
        self._send_response(data, reply_to)

    def __detach_request_handler(self, payload):
        payload = self._serializer.deserialize(payload)
        data = payload['data']
        meta = payload['meta']
        req_msg = self._msg_type.Request(**data)
        self.logger.debug(f'RPC Request <{self._rpc_name}>')
        _future = self.__exec_in_thread(
            functools.partial(self._on_request, req_msg, meta)
        )
        return _future


class _RPCClient(BaseRPCClient):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        super(_RPCClient, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

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

    def call(self, data: dict, timeout: float = 30) -> dict:
        ## TODO: Evaluate msg type passed here.
        _msg = self.__prepare_request(data)
        _reply_to = _msg['meta']['reply_to']
        _msg = self._serializer.serialize(_msg)
        self._transport.push_msg_to_queue(self._rpc_name, _msg)
        msgq, _msg = self._transport.wait_for_msg(_reply_to, timeout=timeout)
        self._transport.delete_queue(_reply_to)
        if _msg is None:
            return None
        _msg = self._serializer.deserialize(_msg)
        ## TODO: Evaluate response type and raise exception if necessary
        return _msg['data']


class RPCClient(_RPCClient):
    def __init__(self,
                 msg_type: RPCMessage,
                 *args, **kwargs):
        super(RPCClient, self).__init__(*args, **kwargs)
        self._msg_type = msg_type

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

    def call(self, msg: RPCMessage.Request,
             timeout: float = 30) -> RPCMessage.Response:
        ## TODO: Evaluate msg type passed here.
        resp_data = super(RPCClient, self).call(msg.as_dict(), timeout)
        return self._msg_type.Response(**resp_data)


class Publisher(BasePublisher):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 queue_size: int = 10,
                 *args, **kwargs):
        self._queue_size = queue_size
        self._msg_seq = 0

        super(Publisher, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def publish(self, msg: PubSubMessage) -> None:
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()
        _msg = self.__prepare_msg(data)
        _msg = self._serializer.serialize(_msg)
        self.logger.debug(
            f'Publishing Message: <{self._topic}>:{data}')
        self._transport.publish(self._topic, _msg)
        self._msg_seq += 1

    def __prepare_msg(self, data):
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


class Subscriber(BaseSubscriber):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 queue_size: int = 1,
                 *args, **kwargs):
        self._queue_size = queue_size
        super(Subscriber, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def run(self):
        self._subscriber_thread = self._transport.subscribe(self._topic,
                                                            self._on_message)
        self.logger.info(f'Started Subscriber: <{self._topic}>')

    def stop(self):
        """Stop background thread that handle subscribed topic messages"""
        try:
            self._exit_gracefully()
        except Exception as exc:
            self.logger.error(f'Exception thrown in Subscriber.stop(): {exc}')

    def run_forever(self):
        try:
            self.run()
            time.sleep(0.001)
        except Exception as exc:
            raise exc

    def _on_message(self, payload: dict):
        payload = self._serializer.deserialize(payload['data'])
        data = payload['data']
        meta = payload['meta']
        if self.onmessage is not None:
            if self._msg_type is None:
                self.onmessage(OrderedDict(data))
            else:
                self.onmessage(self._msg_type(**data))

    def _exit_gracefully(self):
        self._subscriber_thread.stop()


class ActionServer(BaseActionServer):
    def __init__(self,
                 action_name: str,
                 msg_type: ActionMessage,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        assert isinstance(conn_params, ConnectionParametersBase)
        conn_params = UnixSocketConnectionParameters() if \
            conn_params is None else conn_params

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
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        assert isinstance(conn_params, ConnectionParametersBase)
        conn_params = UnixSocketConnectionParameters() if \
            conn_params is None else conn_params

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


class EventEmitter(BaseEventEmitter):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        super(EventEmitter, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def send_event(self, event: Event) -> None:
        _msg = event.as_dict()
        _msg = self.__prepare_msg(_msg)
        _msg = self._serializer.serialize(_msg)
        # self.logger.debug(
        #     'Firing Event: <{}>:{}'.format(event.uri, _msg))
        self._transport.publish(event.uri, _msg)

    def __prepare_msg(self, data: dict) -> None:
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
