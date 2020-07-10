from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)


import functools
import sys

if sys.version_info[0] >= 3:
    unicode = str

import time
import atexit
import signal
import json
import uuid
import hashlib
import datetime

import redis

from commlib_py.logger import Logger
from commlib_py.rpc import BaseRPCServer, BaseRPCClient
from commlib_py.pubsub import BasePublisher, BaseSubscriber
from commlib_py.action import BaseActionServer, BaseActionClient


class Credentials(object):
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password


class ConnectionParameters(object):
    __slots__ = ['db', 'creds']

    def __init__(self, db=0, creds=None):
        self.db = db

        if creds is None:
            creds = Credentials()
        self.creds = creds


class TCPConnectionParameters(ConnectionParameters):
    def __init__(self, host='localhost', port=6379, *args, **kwargs):
        super(TCPConnectionParameters, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port


class UnixSocketConnectionParameters(ConnectionParameters):
    def __init__(self, unix_socket='/tmp/redis.sock', *args, **kwargs):
        super(UnixSocketConnectionParameters, self).__init__(*args, **kwargs)
        self.unix_socket = unix_socket


class RedisConnection(redis.Redis):
    def __init__(self, *args, **kwargs):
        super(RedisConnection, self).__init__(*args, **kwargs)


class RedisTransport(object):
    def __init__(self, conn_params=None, logger=None):
        conn_params = UnixSocketConnectionParameters() if \
            conn_params is None else conn_params
        if isinstance(conn_params, UnixSocketConnectionParameters):
            self._redis = RedisConnection(
                unix_socket_path=conn_params.unix_socket,
                db=conn_params.db, decode_responses=True)
        elif isinstance(conn_params, TCPConnectionParameters):
            self._redis = RedisConnection(host=conn_params.host,
                                          port=conn_params.port,
                                          db=conn_params.db,
                                          decode_responses=True)

        self._conn_params = conn_params
        self.logger = Logger(self.__class__.__name__) if \
            logger is None else logger
        assert isinstance(self.logger, Logger)
        self._rsub = self._redis.pubsub()

    def delete_queue(self, queue_name):
        self.logger.debug('Removing message queue: <{}>'.format(queue_name))
        self._redis.delete(queue_name)

    def push_msg_to_queue(self, queue_name, payload):
        self._redis.rpush(queue_name, payload)

    def publish(self, queue_name, payload):
        self._redis.publish(queue_name, payload)

    def subscribe(self, topic, callback):
        self._sub = self._rsub.subscribe(
            **{topic: callback})
        self._rsub.get_message()
        return self._rsub.run_in_thread(0.001)

    def wait_for_msg(self, queue_name, timeout=10):
        try:
            msgq, payload = self._redis.blpop(queue_name, timeout=timeout)
        except Exception as exc:
            self.logger.error(exc)
            msgq = ''
            payload = None
        return msgq, payload


class RPCServer(BaseRPCServer):
    def __init__(self, conn_params=None, *args, **kwargs):
        super(RPCServer, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def _send_response(self, data, reply_to):
        header = {
            'timestamp': int(datetime.datetime.now(
                datetime.timezone.utc).timestamp() * 1000000),
            'properties': {
                'content_type': self._serializer.CONTENT_TYPE,
                'content_encoding': self._serializer.CONTENT_ENCODING
            }
        }
        _resp = {
            'data': data,
            'header': header
        }
        _resp = self._serializer.serialize(_resp)
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request(self, data, meta):
        if self.on_request is not None:
            resp = self.on_request(data, meta)
        else:
            resp = {
                'status': 500,
                'error': 'Not Implemented'
            }
        if not isinstance(resp, dict):
            raise ValueError()
        reply_to = meta['reply_to']

        self._send_response(resp, reply_to)

    def run_forever(self):
        self._transport.delete_queue(self._rpc_name)
        self.logger.info('RPC Server listening on: <{}>'.format(self._rpc_name))
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
        header = payload['header']
        self.logger.debug('RPC Request <{}>'.format(self._rpc_name))
        _future = self._executor.submit(self._on_request, data, header)
        return _future


class RPCClient(BaseRPCClient):
    def __init__(self, conn_params=None, *args, **kwargs):
        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def __gen_queue_name(self):
        return 'rpc-{}'.format(self._gen_random_id())

    def __prepare_request(self, data):
        _reply_to = self.__gen_queue_name()
        header = {
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
            'header': header
        }
        return _req

    def call(self, data, timeout=60):
        _msg = self.__prepare_request(data)
        _reply_to = _msg['header']['reply_to']
        _msg = self._serializer.serialize(_msg)
        self._transport.push_msg_to_queue(self._rpc_name, _msg)
        msgq, _msg = self._transport.wait_for_msg(_reply_to, timeout=timeout)
        self._transport.delete_queue(_reply_to)
        if _msg is None:
            return None
        _msg = self._serializer.deserialize(_msg)
        return _msg['data']


class Publisher(BasePublisher):
    def __init__(self, conn_params=None, queue_size=10, *args, **kwargs):
        self._queue_size = queue_size
        self._msg_seq = 0

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(Publisher, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def publish(self, payload):
        _msg = self.__prepare_msg(payload)
        _msg = self._serializer.serialize(_msg)
        self.logger.debug(
            'Publishing Message: <{}>:{}'.format(self._topic, payload))
        self._transport.publish(self._topic, _msg)
        self._msg_seq += 1

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def __prepare_msg(self, data):
        header = {
            'timestamp': int(datetime.datetime.now(
                datetime.timezone.utc).timestamp() * 1000000),
            'properties': {
                'content_type': self._serializer.CONTENT_TYPE,
                'content_encoding': self._serializer.CONTENT_ENCODING
            }
        }
        _msg = {
            'data': data,
            'header': header
        }
        return _msg


class Subscriber(BaseSubscriber):
    def __init__(self, conn_params=None, queue_size=1, *args, **kwargs):
        self._queue_size = queue_size

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(Subscriber, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)
        self._event_loop_thread = None

    @property
    def topic(self):
        """topic"""
        return self._topic

    def _gen_random_id(self):
        """Generate a random string id."""
        return str(uuid.uuid4()).replace('-', '')

    def run(self):
        self._subscriber_thread = self._transport.subscribe(self._topic,
                                                            self._on_message)

    def stop(self):
        self._subscriber_thread.stop()

    def run_forever(self):
        try:
            self.run()
            time.sleep(0.001)
        except Exception as exc:
            raise exc

    def _on_message(self, payload):
        self.logger.info(
            'Received Message: <{}>:{}'.format(self._topic, payload))
        payload = self._serializer.deserialize(payload['data'])
        data = payload['data']
        header = payload['header']
        if self._onmessage is not None:
            self._onmessage(data, header)


class ActionServer(BaseActionServer):
    def __init__(self, conn_params=None, *args, **kwargs):
        assert isinstance(conn_params, ConnectionParameters)
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(ActionServer, self).__init__(*args, **kwargs)

        self._goal_rpc = RPCServer(rpc_name=self._goal_rpc_uri,
                                   conn_params=conn_params,
                                   on_request=self._handle_send_goal,
                                   logger=self._logger,
                                   debug=self.debug)
        self._cancel_rpc = RPCServer(rpc_name=self._cancel_rpc_uri,
                                     conn_params=conn_params,
                                     on_request=self._handle_cancel_goal,
                                     logger=self._logger,
                                     debug=self.debug)
        self._result_rpc = RPCServer(rpc_name=self._result_rpc_uri,
                                     conn_params=conn_params,
                                     on_request=self._handle_get_result,
                                     logger=self._logger,
                                     debug=self.debug)
        self._feedback_pub = Publisher(topic=self._feedback_topic,
                                       conn_params=conn_params,
                                       logger=self._logger,
                                       debug=self.debug)
        self._status_pub = Publisher(topic=self._status_topic,
                                     conn_params=conn_params,
                                     logger=self._logger,
                                     debug=self.debug)


class ActionClient(BaseActionClient):
    def __init__(self, conn_params=None, *args, **kwargs):
        assert isinstance(conn_params, ConnectionParameters)
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(ActionClient, self).__init__(*args, **kwargs)

        self._goal_client = RPCClient(rpc_name=self._goal_rpc_uri,
                                      conn_params=conn_params,
                                      logger=self._logger,
                                      debug=self.debug)
        self._cancel_client = RPCClient(rpc_name=self._cancel_rpc_uri,
                                        conn_params=conn_params,
                                        logger=self._logger,
                                        debug=self.debug)
        self._result_client = RPCClient(rpc_name=self._result_rpc_uri,
                                        conn_params=conn_params,
                                        logger=self._logger,
                                        debug=self.debug)
