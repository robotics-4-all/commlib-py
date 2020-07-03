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

from commlib_py.serializer import JSONSerializer
from commlib_py.logger import create_logger
from commlib_py.rpc import AbstractRPCServer, AbstractRPCClient
from commlib_py.pubsub import AbstractPublisher, AbstractSubscriber


class ConnectionParameters(object):
    __slots__ = ['host', 'port', 'unix_socket', 'db']

    def __init__(self, host=None, port=6379,
                 unix_socket='/tmp/redis.sock', db=0):
        self.host = host
        self.port = port
        self.unix_socket = unix_socket
        self.db = db


class RPCServer(AbstractRPCServer):
    def __init__(self, conn_params=None, *args, **kwargs):
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(RPCServer, self).__init__(*args, **kwargs)
        if conn_params.host is None:
            self.redis = redis.Redis(unix_socket_path=conn_params.unix_socket,
                                     db=conn_params.db)
        else:
            self.redis = redis.Redis(host=conn_params.host,
                                     port=conn_params.port,
                                     db=conn_params.db)

    def _rm_msg_queue(self, queue_name):
        self.logger.debug('Removing message queue: <{}>'.format(queue_name))
        self.redis.delete(queue_name)

    def _send_response(self, data, reply_to):
        header = {
            'timestamp': datetime.datetime.now(
                datetime.timezone.utc).timestamp(),
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
        self.redis.rpush(reply_to, _resp)

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
        self._rm_msg_queue(self._rpc_name)
        self.logger.info('RPC Server listening on: <{}>'.format(self._rpc_name))
        while True:
            msgq, payload = self.redis.blpop(self._rpc_name)
            self.__detach_request_handler(payload)
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.logger.debug('Stop event caught in thread')
                    self._rm_msg_queue(self._rpc_name)
                    break
            time.sleep(0.001)

    def stop(self):
        self._t_stop_event.set()

    def __detach_request_handler(self, payload):
        payload = payload.decode()
        payload = self._serializer.deserialize(payload)
        data = payload['data']
        header = payload['header']
        _future = self._executor.submit(self._on_request, data, header)
        return _future


class RPCClient(AbstractRPCClient):
    def __init__(self, conn_params=None, *args, **kwargs):
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(RPCClient, self).__init__(*args, **kwargs)
        if conn_params.host is None:
            self.redis = redis.Redis(unix_socket_path=conn_params.unix_socket,
                                     db=conn_params.db)
        else:
            self.redis = redis.Redis(host=conn_params.host,
                                     port=conn_params.port,
                                     db=conn_params.db)

    def __gen_queue_name(self):
        return 'rpc-{}'.format(self._gen_random_id())

    def _rm_msg_queue(self, queue_name):
        self.redis.delete(queue_name)

    def __prepare_request(self, data):
        _reply_to = self.__gen_queue_name()
        header = {
            'timestamp': datetime.datetime.now(
                datetime.timezone.utc).timestamp(),
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
        self.redis.rpush(
            self._rpc_name, self._serializer.serialize(_msg))
        msgq, msg = self.redis.blpop(_reply_to, timeout=timeout)
        self._rm_msg_queue(_reply_to)
        msg = msg.decode()
        msg = self._serializer.deserialize(msg)
        return msg


class Publisher(AbstractPublisher):
    def __init__(self, conn_params=None, queue_size=10, *args, **kwargs):
        self._queue_size = queue_size
        self._msg_seq = 0

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(Publisher, self).__init__(*args, **kwargs)
        if conn_params.host is None:
            self.redis = redis.Redis(unix_socket_path=conn_params.unix_socket,
                                     db=conn_params.db)
        else:
            self.redis = redis.Redis(host=conn_params.host,
                                     port=conn_params.port,
                                     db=conn_params.db)

    def publish(self, payload):
        _msg = self.__prepare_msg(payload)
        _msg = self._serializer.serialize(_msg)
        self.logger.debug('Publishing Message: <{}>:{}'.format(self._topic,
                                                            payload))
        self.redis.publish(self._topic, _msg)
        self._msg_seq += 1

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def __prepare_msg(self, data):
        header = {
            'timestamp': datetime.datetime.now(
                datetime.timezone.utc).timestamp(),
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


class Subscriber(AbstractSubscriber):
    def __init__(self, conn_params=None, queue_size=1, *args, **kwargs):
        self._queue_size = queue_size

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        super(Subscriber, self).__init__(*args, **kwargs)

        if conn_params.host is None:
            self.redis = redis.Redis(unix_socket_path=conn_params.unix_socket,
                                     db=conn_params.db)
        else:
            self.redis = redis.Redis(host=conn_params.host,
                                     port=conn_params.port,
                                     db=conn_params.db)
        self._rsub = self.redis.pubsub()
        self._event_loop_thread = None

    @property
    def topic(self):
        """topic"""
        return self._topic

    def _gen_random_id(self):
        """Generate a random string id."""
        return str(uuid.uuid4()).replace('-', '')

    def run(self):
        self._sub = self._rsub.subscribe(
            **{self._topic: self._on_message})
        self._rsub.get_message()
        self._event_loop_thread = self._rsub.run_in_thread(0.001)

    def stop(self):
        self._event_loop_thread.stop()

    def run_forever(self):
        try:
            self.run()
            time.sleep(0.001)
        except Exception as exc:
            raise exc

    def _on_message(self, payload):
        print(type(payload))
        self.logger.debug(
            'Received Message: <{}>:{}'.format(self._topic, payload))
        payload = self._serializer.deserialize(payload)
        data = payload['data']
        header = payload['header']
        if self._onmessage is not None:
            self._onmessage(data, header)
