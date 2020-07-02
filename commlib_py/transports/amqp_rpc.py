# -*- coding: utf-8 -*-
# Copyright (C) 2020  Panayiotou, Konstantinos <klpanagi@gmail.com>
# Author: Panayiotou, Konstantinos <klpanagi@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import sys
import functools

if sys.version_info[0] >= 3:
    unicode = str

import time
import uuid
import json
import threading

from commlib_py.transports.amqp_transport import (
    AMQPTransport, ExchangeTypes, MessageProperties, ConnectionParameters
)

from commlib_py.serializer import JSONSerializer, ContentType
from commlib_py.logger import create_logger


class AMQPRPCServer(object):
    """AMQP RPC Server class.
    Implements an AMQP RPC Server.

    Args:
        rpc_name (str): The name of the RPC.
        exchange (str): The exchange to bind the RPC.
            Defaults to (AMQT default).
        on_request (function): The on-request callback function to register.
    """
    def __init__(self, rpc_name,conn_params=None, exchange='',
                 on_request=None, serializer=None,
                 debug=True, logger=None):
        """Constructor. """
        self._name = rpc_name
        self._rpc_name = rpc_name
        self._debug = debug

        self._logger = create_logger(self.__class__.__name__) if \
            logger is None else logger

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer()

        self._transport = AMQPTransport(conn_params, self._debug, self._logger)

        self._exchange = exchange
        # Bind on_request callback
        self.on_request = on_request

    @property
    def logger(self):
        return self._logger

    @property
    def connection(self):
        return self._transport.connection

    @property
    def channel(self):
        return self._transport.channel

    def is_alive(self):
        """Returns True if connection is alive and False otherwise."""
        if self.connection is None:
            return False
        elif self.connection.is_open:
            return True
        else:
            return False

    def run_forever(self, raise_if_exists=True):
        """Run RPC Server in normal mode. Blocking function."""
        self._transport.connect()
        if self._rpc_exists() and raise_if_exists:
            raise ValueError(
                'RPC <{}> allready registered on broker.'.format(
                    self._rpc_name))
        self._rpc_queue = self._transport.create_queue(self._rpc_name)
        self._transport.set_channel_qos()
        self._transport.consume_fromm_queue(self._rpc_queue,
                                            self._on_request_wrapper)
        try:
            self._transport.start_consuming()
        except Exception as exc:
            self.logger.error(exc, exc_info=True)
            raise exc

    def run(self, raise_if_exists=True):
        """Run RPC Server in a separate thread."""
        self.loop_thread = threading.Thread(target=self.run)
        self.loop_thread.daemon = True
        self.loop_thread.start()

    def _rpc_exists(self):
        return self._transport.queue_exists(self._rpc_name)

    def _on_request_wrapper(self, ch, method, properties, body):
        _msg = {}
        _ctype = None
        _cencoding = None
        _ts_send = None
        _ts_broker = None
        _dmode = None
        _corr_id = None
        try:
            _corr_id = properties.correlation_id
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            _ts_broker = properties.headers['timestamp_in_ms']
            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp
            # _ts_broker = properties.timestamp
        except Exception:
            self.logger.error("Could not calculate latency",
                              exc_info=True)

        try:
            _msg = self._deserialize_data(body, _ctype, _cencoding)
        except Exception:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            # Return data as is. Let callback handle with encoding...
            _msg = body


        if self.on_request is not None:
            _meta = {
                'channel': ch,
                'method': method,
                'properties': {
                    'content_type': _ctype,
                    'content_encoding': _cencoding,
                    'timestamp_broker': _ts_broker,
                    'timestamp_producer': _ts_send,
                    'delivery_mode': _dmode,
                    'correlation_id': _corr_id
                }
            }
            self.logger.debug(_msg)
            self.logger.debug(_meta)
            resp = self.on_request(_msg, _meta)
        else:
            resp = {
                'error': 'Not Implemented',
                'status': 501
            }

        try:
            _payload = None
            _encoding = None
            _type = None

            if isinstance(resp, dict):
                _payload = self._serializer.serialize(resp).encode('utf-8')
                _encoding = self._serializer.CONTENT_ENCODING
                _type = self._serializer.CONTENT_TYPE
            elif isinstance(resp, str):
                _type = 'text/plain'
                _encoding = 'utf8'
                _payload = resp
            elif isinstance(resp, bytes):
                _type = 'application/octet-stream'
                _encoding = 'utf8'
                _payload = resp

        except Exception as e:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            _payload = {
                'status': 501,
                'error': 'Internal server error: {}'.format(str(e))
            }

        _msg_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            correlation_id=_corr_id
        )

        ch.basic_publish(
            exchange=self._exchange,
            routing_key=properties.reply_to,
            properties=_msg_props,
            body=_payload)
        # Acknowledge receiving the message.
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _deserialize_data(self, data, content_type, content_encoding):
        """Deserialize wire data.

        Args:
            data (str|dict): Data to deserialize.
            content_encoding (str): The content encoding.
            content_type (str): The content type. Defaults to `utf8`.
        """
        _data = None
        if content_encoding is None:
            content_encoding = 'utf8'
        if content_type == ContentType.json:
            _data = JSONSerializer.deserialize(data)
        elif content_type == ContentType.text:
            _data = data.decode(content_encoding)
        elif content_type == ContentType.raw_bytes:
            _data = data
        else:
            self.logger.warning(
                    'Content-Type was not set in headers or is invalid!' + \
                            ' Deserializing using default JSON serializer')
            ## TODO: Not the proper way!!!!
            _data = JSONSerializer.deserialize(data)
        return _data

    def close(self):
        """Stop RPC Server.
        Safely close channel and connection to the broker.
        """
        if not self.channel:
            return
        if self.channel.is_closed:
            self.logger.warning('Channel was already closed!')
            return False
        self._transport.stop_consuming()
        # super(RpcServer, self).close()
        self._transport.delete_queue(self._rpc_queue)
        return True

    def stop(self):
        """Stop RPC Server.
        Safely close channel and connection to the broker.
        """
        return self.close()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, value, traceback):
        self.close()


class AMQPRPCClient(object):
    """AMQP RPC Client class.

    Args:
        rpc_name (str): The name of the RPC.
        **kwargs: The Keyword arguments to pass to  the base class
            (AMQPTransportSync).
    """
    def __init__(self, rpc_name, conn_params=None, debug=False,
                 logger=None, use_corr_id=False, serializer=None):
        """Constructor."""
        self._name = rpc_name
        self._rpc_name = rpc_name
        self._corr_id = None
        self._response = None
        self._exchange = ExchangeTypes.Default
        self._mean_delay = 0
        self._delay = 0
        self.onresponse = None
        self._use_corr_id = use_corr_id

        self._logger = create_logger(self.__class__.__name__) if \
            logger is None else logger

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer()

        self._transport = AMQPTransport(conn_params, self._debug, self._logger)

        self._serializer = JSONSerializer()

        self._transport.connect()

        self._consumer_tag = self.channel.basic_consume(
            'amq.rabbitmq.reply-to',
            self._on_response,
            exclusive=False,
            consumer_tag=None,
            auto_ack=True)

    @property
    def logger(self):
        return self._logger

    @property
    def connection(self):
        return self._transport.connection

    @property
    def channel(self):
        return self._transport.channel

    @property
    def mean_delay(self):
        """The mean delay of the communication. Internally calculated."""
        return self._mean_delay

    @property
    def delay(self):
        """The last recorded delay of the communication.
            Internally calculated.
        """
        return self._delay

    def _on_response(self, ch, method, properties, body):
        _ctype = None
        _cencoding = None
        _ts_send = None
        _ts_broker = 0
        _dmode = None
        _msg = None
        _meta = None
        try:
            if self._use_corr_id:
                _corr_id = properties.correlation_id
                if self._corr_id != _corr_id:
                    return
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            if hasattr(self, 'headers'):
                if 'timestamp_in_ms' in properties.headers:
                    _ts_broker = properties.headers['timestamp_in_ms']

            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp

            _meta = {
                'channel': ch,
                'method': method,
                'properties': {
                    'content_type': _ctype,
                    'content_encoding': _cencoding,
                    'timestamp_broker': _ts_broker,
                    'timestamp_producer': _ts_send,
                    'delivery_mode': _dmode
                }
            }
        except Exception:
            self.logger.error("Error parsing response from rpc server.",
                              exc_info=True)

        try:
            _msg = self._deserialize_data(body, _ctype, _cencoding)
        except Exception:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            _msg = body


        self._response = _msg
        self._response_meta = _meta

        if self.onresponse is not None:
            self.onresponse(_msg, _meta)

    def gen_corr_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4())

    def call(self, msg, timeout=5.0):
        """Call RPC.

        Args:
            msg (dict|Message): The message to send.
            timeout (float): Response timeout. Set this value carefully
                based on application criteria.
        """
        self._response = None
        if self._use_corr_id:
            self._corr_id = self.gen_corr_id()
        if isinstance(msg, Message):
            data = msg.to_dict()
        else:
            data = msg
        self._send_data(data)
        start_t = time.time()
        self._wait_for_response(timeout)
        ## TODO: Validate correlation_id
        elapsed_t = time.time() - start_t
        self._delay = elapsed_t

        if self._response is None:
            resp = {'error': 'RPC Response timeout'}
        else:
            resp = self._response
        return resp

    def _wait_for_response(self, timeout):
        self.logger.debug('Waiting for response from [%s]...', self._rpc_name)
        self.connection.process_data_events(time_limit=timeout)

    def _deserialize_data(self, data, content_type, content_encoding):
        """Deserialize wire data.

        Args:
            data: Data to deserialize.
            content_encoding (str): The content encoding.
            content_type (str): The content type. Defaults to `utf8`
        """
        _data = None
        if content_encoding is None:
            content_encoding = 'utf8'
        if content_type == ContentType.json:
            _data = JSONSerializer.deserialize(data)
        elif content_type == ContentType.text:
            _data = data.decode(content_encoding)
        elif content_type == ContentType.raw_bytes:
            _data = data
        return _data

    def _send_data(self, data):
        _payload = None
        _encoding = None
        _type = None

        if isinstance(data, dict):
            _payload = self._serializer.serialize(data).encode('utf-8')
            _encoding = self._serializer.CONTENT_ENCODING
            _type = self._serializer.CONTENT_TYPE
        elif isinstance(data, str):
            _type = 'text/plain'
            _encoding = 'utf8'
            _payload = data
        elif isinstance(data, bytes):
            _type = 'application/octet-stream'
            _encoding = 'utf8'
            _payload = data

        # Direct reply-to implementation
        _rpc_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            correlation_id=self._corr_id,
            # timestamp=(1.0 * (time.time() + 0.5) * 1000),
            message_id=0,
            # user_id="",
            # app_id="",
            reply_to='amq.rabbitmq.reply-to'
        )

        self.channel.basic_publish(
            exchange=self._exchange,
            routing_key=self._rpc_name,
            mandatory=False,
            properties=_rpc_props,
            body=_payload)

