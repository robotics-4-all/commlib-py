import functools
import json
import logging
import time
import uuid
from collections import deque
from threading import Event as ThreadEvent
from threading import Semaphore, Thread
from typing import Dict

import pika

from commlib.action import (
    BaseActionClient, BaseActionService, _ActionCancelMessage,
    _ActionFeedbackMessage, _ActionGoalMessage,
    _ActionResultMessage, _ActionStatusMessage
)
from commlib.events import BaseEventEmitter, Event
from commlib.exceptions import *
from commlib.logger import Logger
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import BaseRPCClient, BaseRPCService
from commlib.utils import gen_timestamp

# Reduce log level for pika internal logger
logging.getLogger("pika").setLevel(logging.WARN)


class MessageProperties(pika.BasicProperties):
    """Message Properties/Attribures used for sending and receiving messages.

    Args:
        content_type (str):
        content_encoding (str):
        timestamp (str):

    """

    def __init__(self, content_type: str = None,
                 content_encoding: str = None,
                 timestamp: float = None,
                 correlation_id: str = None,
                 reply_to: str = None,
                 message_id: str = None,
                 user_id: str = None,
                 app_id: str = None):
        """__init__.

        Args:
            content_type (str): content_type
            content_encoding (str): content_encoding
            timestamp (float): timestamp
            correlation_id (str): correlation_id
            reply_to (str): reply_to
            message_id (str): message_id
            user_id (str): user_id
            app_id (str): app_id
        """
        if timestamp is None:
            timestamp = gen_timestamp()
        super(MessageProperties, self).__init__(
            content_type=content_type,
            content_encoding=content_encoding,
            timestamp=timestamp,
            correlation_id=correlation_id,
            reply_to=reply_to,
            message_id=str(message_id) if message_id is not None else None,
            user_id=str(user_id) if user_id is not None else None,
            app_id=str(app_id) if app_id is not None else None
        )


class Credentials:
    """Connection credentials for authn/authz.

    Args:
        username (str): The username.
        password (str): The password (Basic Authentication).
    """

    __slots__ = ['username', 'password']

    def __init__(self, username: str = 'guest', password: str = 'guest'):
        """__init__.

        Args:
            username (str): username
            password (str): password
        """
        self.username = username
        self.password = password

    def make_pika(self):
        """make_pika.
        Create Pika Credentials instance.
        """
        return pika.PlainCredentials(username=self.username,
                                     password=self.password)


class ConnectionParameters():
    """AMQP Connection parameters.
    AMQP connection parameters class
    """

    __slots__ = [
        'host', 'port', 'secure', 'vhost', 'reconnect_attempts', 'retry_delay',
        'timeout', 'heartbeat_timeout', 'blocked_connection_timeout', 'creds',
        'channel_max'
    ]

    def __init__(self,
                 host: str = '127.0.0.1',
                 port: int = 5672,
                 vhost: str = '/',
                 creds: Credentials = None,
                 secure: bool = False,
                 reconnect_attempts: int = 10,
                 retry_delay: float = 2.0,
                 timeout: float = 120,
                 blocked_connection_timeout: float = None,
                 heartbeat_timeout: int = 60,
                 channel_max: int = 128):
        """__init__.

        Args:
            host (str): Hostname of AMQP broker to connect to.
            port (int): AMQP broker listening port.
            creds (Credentials): Auth Credentials - Credentials instance.
            secure (bool): Enable SSL/TLS (AMQPS) - Not supported!!
            reconnect_attempts (int): The reconnection attempts to make before
                droping and raising an Exception.
            retry_delay (float): Time delay between reconnect attempts.
            timeout (float): Socket Connection timeout value.
            timeout (float): Blocked Connection timeout value.
                Set the timeout, in seconds, that the connection may remain blocked
                (triggered by Connection.Blocked from broker). If the timeout
                expires before connection becomes unblocked, the connection will
                be torn down.
            heartbeat_timeout (int): Controls AMQP heartbeat
                timeout negotiation during connection tuning. An integer value
                always overrides the value proposed by broker. Use 0 to deactivate
                heartbeats and None to always accept the broker's proposal.
                The value passed for timeout is also used to calculate an interval
                at which a heartbeat frame is sent to the broker. The interval is
                equal to the timeout value divided by two.
            channel_max (int): The max permissible number of channels per
                connection. Defaults to 128.
        """
        self.host = host
        self.port = port
        self.secure = secure
        self.vhost = vhost
        self.reconnect_attempts = reconnect_attempts
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.blocked_connection_timeout = blocked_connection_timeout
        self.heartbeat_timeout = heartbeat_timeout
        self.channel_max = channel_max

        if creds is None:
            creds = Credentials()
        self.creds = creds

    @property
    def credentials(self):
        return self.creds

    def make_pika(self):
        return pika.ConnectionParameters(
            host=self.host,
            port=str(self.port),
            credentials=self.creds.make_pika(),
            connection_attempts=self.reconnect_attempts,
            retry_delay=self.retry_delay,
            blocked_connection_timeout=self.blocked_connection_timeout,
            socket_timeout=self.timeout,
            virtual_host=self.vhost,
            heartbeat=self.heartbeat_timeout,
            channel_max=self.channel_max)

    def __str__(self):
        _properties = {
            'host': self.host,
            'port': self.port,
            'vhost': self.vhost,
            'reconnect_attempts': self.reconnect_attempts,
            'retry_delay': self.retry_delay,
            'timeout': self.timeout,
            'blocked_connection_timeout': self.blocked_connection_timeout,
            'heartbeat_timeout': self.heartbeat_timeout,
            'channel_max': self.channel_max
        }
        _str = json.dumps(_properties)
        return _str


class Connection(pika.BlockingConnection):
    """Connection. qThin wrapper around pika.BlockingConnection"""
    def __init__(self, conn_params: ConnectionParameters):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
        """
        self._connection_params = conn_params
        self._pika_connection = None
        self._transport = None
        self._events_thread = None
        self._t_stop_event = None
        super(Connection, self).__init__(
            parameters=self._connection_params.make_pika())

    def stop_amqp_events_thread(self):
        """stop_amqp_events_thread.
        Stops the background thead that handles internal amqp events.
        """
        if self._t_stop_event is not None:
            self._t_stop_event.set()
            self._events_thread = None

    def detach_amqp_events_thread(self):
        """detach_amqp_events_thread.
        Starts a thread in background to handle with internal amqp events.
            Useful for use with producers in complex applications where
            the program might sleep for several seconds. In this case,
            if the amqp events thread is not started, the main thread
            will be blocked and messages will not leave to the wire at
            the expected time.
        """
        if self._events_thread is not None:
            if self._events_thread.is_alive():
                return
        self._events_thread = Thread(target=self._ensure_events_processed)
        self._events_thread.daemon = True
        self._t_stop_event = ThreadEvent()
        self._events_thread.start()

    def _ensure_events_processed(self):
        """_ensure_events_processed.
        """
        try:
            while True:
                self.sleep(1)
                if self._t_stop_event.is_set():
                    break
        except Exception as exc:
            print(f'Exception thrown while processing amqp events - {exc}')


    def set_transport_ref(self, transport):
        self._transport = transport


class ExchangeType:
    """AMQP Exchange Types."""
    Topic = 'topic'
    Direct = 'direct'
    Fanout = 'fanout'
    Default = ''


class AMQPTransport:
    """AMQPT Transport implementation.
    """

    def __init__(self, conn_params: ConnectionParameters,
                 debug: bool = False,
                 logger: Logger = None,
                 connection: Connection = None):
        """Constructor."""
        # So that connections do not go zombie

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        self._connection = connection
        self._conn_params = conn_params
        self._debug = debug
        self._channel = None
        self._closing = False

        self._logger = Logger(self.__class__.__name__, debug=self._debug) if \
            logger is None else logger

        # Create a new connection
        if self._connection is None:
            self._connection = Connection(self._conn_params)

    @property
    def logger(self):
        return self._logger

    @property
    def channel(self):
        return self._channel

    @property
    def connection(self):
        return self._connection

    def connect(self):
        self.create_channel()

    def _on_connect(self):
        ch = self._connection.channel()
        self._channel = ch

    def create_channel(self):
        """Connect to the AMQP broker. Creates a new channel."""
        try:
            # Create a new communication channel
            self._channel = self._connection.channel()
            # self.add_threadsafe_callback(self._on_connect)
            self.logger.debug(
                    'Connected to AMQP broker @ [{}:{}, vhost={}]'.format(
                        self._conn_params.host,
                        self._conn_params.port,
                        self._conn_params.vhost))
        except pika.exceptions.ConnectionClosed:
            self.logger.debug('Connection timed out. Reconnecting...')
            self.connect()
        except pika.exceptions.AuthenticationError:
            self.logger.debug('Authentication Error. Reconnecting...')
        except pika.exceptions.AMQPConnectionError as e:
            self.logger.debug(f'Connection Error ({e}). Reconnecting...')
            self.connect()

    def add_threadsafe_callback(self, cb, *args, **kwargs):
        self.connection.add_callback_threadsafe(
            functools.partial(cb, *args, **kwargs)
        )

    def process_amqp_events(self, timeout=0):
        """Force process amqp events, such as heartbeat packages."""
        self.connection.process_data_events(timeout)
        # self.add_threadsafe_callback(self.connection.process_data_events)

    def detach_amqp_events_thread(self):
        self.connection.detach_amqp_events_thread()

    def _signal_handler(self, signum, frame):
        """TODO"""
        self.logger.debug(f'Signal received: {signum}')
        self._graceful_shutdown()

    def _graceful_shutdown(self):
        if not self._connection:
            return
        if not self._channel:
            return
        if self._channel.is_closed:
            # self.logger.warning('Channel is allready closed')
            return
        self.logger.debug('Invoking a graceful shutdown...')
        if self.channel.is_open:
            self.add_threadsafe_callback(self.channel.close)
        self.logger.debug('Channel closed!')

    def exchange_exists(self, exchange_name):
        resp = self._channel.exchange_declare(
            exchange=exchange_name,
            passive=True,  # Perform a declare or just to see if it exists
        )
        self.logger.debug(f'Exchange exists result: {resp}')
        return resp

    def create_exchange(self,
                        exchange_name: str,
                        exchange_type: ExchangeType, internal=None):
        """
        Create a new exchange.

        @param exchange_name: The name of the exchange (e.g. com.logging).
        @type exchange_name: string

        @param exchange_type: The type of the exchange (e.g. 'topic').
        @type exchange_type: string
        """
        self._channel.exchange_declare(
            exchange=exchange_name,
            durable=True,  # Survive reboot
            passive=False,  # Perform a declare or just to see if it exists
            internal=internal,  # Can only be published to by other exchanges
            exchange_type=exchange_type
        )

        self.logger.debug(
            f'Created exchange: [name={exchange_name}, type={exchange_type}]')

    def create_queue(self,
                     queue_name: str= '',
                     exclusive: str = True,
                     queue_size: int = 10,
                     message_ttl: int = 60000,
                     overflow_behaviour: int = 'drop-head',
                     expires: int = 600000):
        """
        Create a new queue.

        @param queue_name: The name of the queue.
        @type queue_name: string

        @param exclusive: Only allow access by the current connection.
        @type exclusive: bool

        @param queue_size: The size of the queue
        @type queue_size: int

        @param message_ttl: Per-queue message time-to-live
            (https://www.rabbitmq.com/ttl.html#per-queue-message-ttl)
        @type message_ttl: int

        @param overflow_behaviour: Overflow behaviour - 'drop-head' ||
            'reject-publish'.
            https://www.rabbitmq.com/maxlength.html#overflow-behaviour
        @type overflow_behaviour: str

        @param expires: Queues will expire after a period of time only
            when they are not used (e.g. do not have consumers).
            This feature can be used together with the auto-delete
            queue property. The value is expressed in milliseconds (ms).
            Default value is 10 minutes.
            https://www.rabbitmq.com/ttl.html#queue-ttl
        """
        args = {
            'x-max-length': queue_size,
            'x-overflow': overflow_behaviour,
            'x-message-ttl': message_ttl,
            'x-expires': expires
        }

        result = self._channel.queue_declare(
            exclusive=exclusive,
            queue=queue_name,
            durable=False,
            auto_delete=True,
            arguments=args)
        queue_name = result.method.queue
        self.logger.debug(
            f'Created queue [{queue_name}] [size={queue_size}, ttl={message_ttl}]')
        return queue_name

    def delete_queue(self, queue_name):
        self._channel.queue_delete(queue=queue_name)

    def queue_exists(self, queue_name):
        """Check if a queue exists, given its name.

        Args:
            queue_name (str): The name of the queue.

        Returns:
            int: True if queue exists False otherwise.
        """
        # resp = self._channel.queue_declare(queue_name, passive=True,
        #                                    callback=self._queue_exists_clb)
        try:
            _ = self._channel.queue_declare(queue_name, passive=True)
        except pika.exceptions.ChannelClosedByBroker as exc:
            self.create_channel()
            if exc.reply_code == 404:  # Not Found
                return False
            else:
                self.logger.warning(f'Queue exists <{queue_name}>')
                return True

    def bind_queue(self, exchange_name, queue_name, bind_key):
        """
        Bind a queue to and exchange using a bind-key.

        @param exchange_name: The name of the exchange (e.g. com.logging).
        @type exchange_name: string

        @param queue_name: The name of the queue.
        @type queue_name: string

        @param bind_key: The binding key name.
        @type bind_key: string
        """
        try:
            self._channel.queue_bind(
                exchange=exchange_name, queue=queue_name, routing_key=bind_key)
        except Exception:
            raise AMQPError('Error while trying to bind queue to exchange')

    def set_channel_qos(self, prefetch_count=1, global_qos=False):
        self._channel.basic_qos(prefetch_count=prefetch_count,
                                global_qos=global_qos)

    def consume_fromm_queue(self, queue_name, callback):
        consumer_tag = self._channel.basic_consume(queue_name, callback)
        return consumer_tag

    def start_consuming(self):
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

    def close(self):
        self._graceful_shutdown()

    def disconnect(self):
        self._graceful_shutdown()

    # def __del__(self):
    #     self._graceful_shutdown()


class RPCService(BaseRPCService):
    """AMQP RPC Service class.
    Implements an AMQP RPC Service.

    Args:
        rpc_name (str): The name of the RPC.
        exchange (str): The exchange to bind the RPC.
            Defaults to (AMQT default).
        on_request (function): The on-request callback function to register.
    """
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 exchange: str = '',
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            exchange (str): exchange
            args:
            kwargs:
        """
        self._exchange = exchange
        self._closing = False
        super(RPCService, self).__init__(*args, **kwargs)

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params
        self._transport = AMQPTransport(conn_params, self.debug, self.logger)

    def run_forever(self, raise_if_exists: bool = False):
        """Run RPC Service in normal mode. Blocking operation."""
        # if self._rpc_exists() and raise_if_exists:
        #     raise ValueError(
        #         'RPC <{}> allready registered on broker.'.format(
        #             self._rpc_name))
        self._transport.connect()
        self._rpc_queue = self._transport.create_queue(self._rpc_name)
        self._transport.set_channel_qos()
        self._transport.consume_fromm_queue(self._rpc_queue,
                                            self._on_request_handle)
        try:
            self._transport.start_consuming()
        except pika.exceptions.ConnectionClosedByBroker as exc:
            self.logger.error(exc, exc_info=True)
        except pika.exceptions.AMQPConnectionError as exc:
            self.logger.error(exc, exc_info=True)
        except Exception as exc:
            self.logger.error(exc, exc_info=True)
            raise AMQPError('Error while trying to consume from queue')

    def _rpc_exists(self):
        return self._transport.queue_exists(self._rpc_name)

    def _on_request_handle(self, ch, method, properties, body):
        _data = {}
        _ctype = None
        _cencoding = None
        _ts_send = None
        _dmode = None
        _corr_id = None
        _reply_to = None
        _delivery_tag = None
        try:
            _reply_to = properties.reply_to
            _delivery_tag = method.delivery_tag
            _corr_id = properties.correlation_id
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp
        except Exception:
            self.logger.error("Exception Thrown in on_request_handle",
                              exc_info=True)
        try:
            _data = self._serializer.deserialize(body)
        except Exception:
            self.logger.error("Could not deserialize data", exc_info=True)
            # Return data as is. Let callback handle with encoding...
            _data = {}
            self._send_response(_data, ch, _corr_id, _reply_to, _delivery_tag)
            return
        resp = self._invoke_onrequest_callback(_data)
        self._send_response(resp, ch, _corr_id, _reply_to, _delivery_tag)

    def _invoke_onrequest_callback(self, data: dict):
        if self._msg_type is None:
            try:
                resp = self.on_request(data)
            except Exception as exc:
                self.logger.error(str(exc), exc_info=False)
                resp = {}
        else:
            try:
                msg = self._msg_type.Request(**data)
                resp = self.on_request(msg)
            except Exception as exc:
                self.logger.error(str(exc), exc_info=False)
                resp = self._msg_type.Response()
            resp = resp.as_dict()
        return resp

    def _send_response(self, data: dict, channel, correlation_id: str,
                       reply_to: str, delivery_tag: str):
        _payload = None
        _encoding = None
        _type = None
        try:
            _encoding = self._serializer.CONTENT_ENCODING
            _type = self._serializer.CONTENT_TYPE
            _payload = self._serializer.serialize(data).encode(_encoding)
        except Exception as e:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            _payload = {
                'status': 501,
                'error': f'Internal server error: {e}'
            }

        _msg_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            correlation_id=correlation_id
        )

        channel.basic_publish(
            exchange=self._exchange,
            routing_key=reply_to,
            properties=_msg_props,
            body=_payload)
        # Acknowledge receiving the message.
        channel.basic_ack(delivery_tag=delivery_tag)

    def close(self) -> bool:
        """Stop RPC Service.
        Safely close channel and connection to the broker.
        """
        if self._closing:
            return False
        self._closing = True
        if not self._transport.channel:
            return False
        if self._transport.channel.is_closed:
            self.logger.warning('Channel was already closed!')
            return False
        self._transport.add_threadsafe_callback(
            self._transport.delete_queue, self._rpc_queue)
        self._transport.add_threadsafe_callback(
            self._transport.stop_consuming)
        self._transport.add_threadsafe_callback(
            self._transport.close)
        super(RPCService, self).stop()
        return True

    def stop(self) -> bool:
        """Stop RPC Service.
        Safely close channel and connection to the broker.
        """
        return self.close()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, value, traceback):
        self.close()


class RPCClient(BaseRPCClient):
    """AMQP RPC Client class.

    Args:
        rpc_name (str): The name of the RPC.
        **kwargs: The Keyword arguments to pass to  the base class
            (BaseRPCClient).
    """
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 connection: Connection = None,
                 use_corr_id=False,
                 *args, **kwargs):
        """Constructor."""
        self._use_corr_id = use_corr_id
        self._corr_id = None
        self._response = None
        self._exchange = ExchangeType.Default
        self._mean_delay = 0
        self._delay = 0

        super(RPCClient, self).__init__(*args, **kwargs)

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        self._transport = AMQPTransport(conn_params, self._debug,
                                        self._logger, connection)
        self._transport.connect()

        ## Register on_request cabblack handle
        self._transport.add_threadsafe_callback(
            self._transport.channel.basic_consume,
            'amq.rabbitmq.reply-to',
            self._on_response_handle,
            exclusive=True,
            consumer_tag=None,
            auto_ack=True
        )

        if connection is None:
            self.run()

    @property
    def mean_delay(self) -> float:
        """The mean delay of the communication. Internally calculated."""
        return self._mean_delay

    @property
    def delay(self) -> float:
        """The last recorded delay of the communication.
            Internally calculated.
        """
        return self._delay

    def run(self):
        self._transport.detach_amqp_events_thread()

    def gen_corr_id(self) -> str:
        """Generate correlationID."""
        return str(uuid.uuid4())

    def call(self, msg: RPCMessage.Request, timeout: float = 10.0):
        """Call RPC.

        Args:
            timeout (float): Response timeout. Set this value carefully
                based on application criteria.
        """
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()

        self._response = None
        if self._use_corr_id:
            self._corr_id = self.gen_corr_id()

        start_t = time.time()
        self._transport.connection.add_callback_threadsafe(
            functools.partial(self._send_msg, data)
        )
        resp = self._wait_for_response(timeout=timeout)
        elapsed_t = time.time() - start_t
        self._delay = elapsed_t
        if self._msg_type is None:
            return resp
        else:
            return self._msg_type.Response(**resp)

    def _wait_for_response(self, timeout: float = 10.0):
        start_t = time.time()
        while self._response is None:
            elapsed_t = time.time() - start_t
            if elapsed_t >= timeout:
                return None
            time.sleep(0.001)
        return self._response

    def _on_response_handle(self, ch, method, properties, body):
        _ctype = None
        _cencoding = None
        _ts_send = None
        _dmode = None
        _data = None
        try:
            if self._use_corr_id:
                _corr_id = properties.correlation_id
                if self._corr_id != _corr_id:
                    return
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp
        except Exception:
            self.logger.error("Error parsing response from rpc server.",
                              exc_info=True)

        try:
            _data = self._serializer.deserialize(body)
        except Exception:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            _data = {}
        self._response = _data

    def _send_msg(self, data: dict) -> None:
        _payload = None
        _encoding = None
        _type = None

        _encoding = self._serializer.CONTENT_ENCODING
        _type = self._serializer.CONTENT_TYPE
        _payload = self._serializer.serialize(data).encode(_encoding)

        # Direct reply-to implementation
        _rpc_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            correlation_id=self._corr_id,
            timestamp=gen_timestamp(),
            reply_to='amq.rabbitmq.reply-to'
        )

        self._transport.add_threadsafe_callback(
            self._transport.channel.basic_publish,
            exchange=self._exchange,
            routing_key=self._rpc_name,
            mandatory=False,
            properties=_rpc_props,
            body=_payload
        )


class Publisher(BasePublisher):
    """Publisher class.

    Args:
        topic (str): The topic uri to publish data.
        exchange (str): The exchange to publish data.
        **kwargs: The keyword arguments to pass to the base class
            (BasePublisher).
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 connection: Connection = None,
                 exchange: str = 'amq.topic',
                 *args, **kwargs):
        """Constructor."""
        self._topic_exchange = exchange
        super(Publisher, self).__init__(*args, **kwargs)

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        self._transport = AMQPTransport(conn_params, self._debug,
                                        self._logger, connection)
        self._transport.connect()
        self._transport.create_exchange(self._topic_exchange,
                                        ExchangeType.Topic)
        if connection is None:
            self.run()

    def run(self) -> None:
        self._transport.detach_amqp_events_thread()

    def publish(self, msg: PubSubMessage) -> None:
        """ Publish message once.

        Args:
            msg (PubSubMessage): Message to publish.
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.as_dict()
        ## Thread Safe solution
        self._transport.add_threadsafe_callback(self._send_msg, data,
                                                self._topic)

    def _send_msg(self, msg: Dict, topic: str):
        _payload = None
        _encoding = None
        _type = None

        _encoding = self._serializer.CONTENT_ENCODING
        _type = self._serializer.CONTENT_TYPE
        _payload = self._serializer.serialize(msg).encode(_encoding)

        msg_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            message_id=0,
        )

        # In amqp '#' defines one or more words.
        topic = topic.replace('*', '#')

        self._transport._channel.basic_publish(
            exchange=self._topic_exchange,
            routing_key=topic,
            properties=msg_props,
            body=_payload)


class MPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        super(MPublisher, self).__init__(topic='*', *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        """ Publish message once.

        Args:
            msg (PubSubMessage): Message to publish.
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.as_dict()
        ## Thread Safe solution
        self._transport.add_threadsafe_callback(self._send_msg, data, topic)


class Subscriber(BaseSubscriber):
    """Subscriber class.
    Implements the Subscriber endpoint of the PubSub communication pattern.

    Args:
        topic (str): The topic uri.
        on_message (function): The callback function. This function
            is fired when messages arrive at the registered topic.
        exchange (str): The name of the exchange. Defaults to `amq.topic`
        queue_size (int): The maximum queue size of the topic.
        message_ttl (int): Message Time-to-Live as specified by AMQP.
        overflow (str): queue overflow behavior. Specified by AMQP Protocol.
            Defaults to `drop-head`.
        **kwargs: The keyword arguments to pass to the base class
            (BaseSubscriber).
    """

    FREQ_CALC_SAMPLES_MAX = 100

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 exchange: str = 'amq.topic',
                 queue_size: int = 10,
                 message_ttl: int = 60000,
                 overflow: str = 'drop-head',
                 *args, **kwargs):
        """Constructor."""
        self._topic_exchange = exchange
        self._queue_size = queue_size
        self._message_ttl = message_ttl
        self._overflow = overflow
        self._queue_name = None
        self._closing = False
        self._transport = None

        super(Subscriber, self).__init__(*args, **kwargs)

        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        self._transport = AMQPTransport(conn_params, self.debug, self.logger)

        self._last_msg_ts = None
        self._msg_freq_fifo = deque(maxlen=self.FREQ_CALC_SAMPLES_MAX)
        self._hz = 0
        self._sem = Semaphore()

    @property
    def hz(self) -> float:
        """Incoming message frequency."""
        return self._hz

    def run_forever(self) -> None:
        """Start Subscriber. Blocking method."""
        self._transport.connect()
        _exch_ex = self._transport.exchange_exists(self._topic_exchange)
        if _exch_ex.method.NAME != 'Exchange.DeclareOk':
            self._transport.create_exchange(self._topic_exchange,
                                            ExchangeType.Topic)

        # Create a queue. Set default idle expiration time to 5 mins
        self._queue_name = self._transport.create_queue(
            queue_size=self._queue_size,
            message_ttl=self._message_ttl,
            overflow_behaviour=self._overflow,
            expires=300000)

        # Bind queue to the Topic exchange
        self._transport.bind_queue(self._topic_exchange, self._queue_name,
                                   self._topic)
        self._consume()

    def close(self) -> None:
        if self._closing:
            return False
        elif not self._transport:
            return False
        elif not self._transport.channel:
            return False
        elif self._transport.channel.is_closed:
            self.logger.warning('Channel was already closed!')
            return False
        self._closing = True
        super(Subscriber, self).stop()
        self._transport.add_threadsafe_callback(
            self._transport.delete_queue, self._queue_name)
        self._transport.add_threadsafe_callback(
            self._transport.stop_consuming)
        self._transport.add_threadsafe_callback(
            self._transport.close)

    def _consume(self, reliable: bool = False) -> None:
        """Start AMQP consumer."""
        self._transport._channel.basic_consume(
            self._queue_name,
            self._on_msg_callback_wrapper,
            exclusive=False,
            auto_ack=(not reliable))
        try:
            self._transport.start_consuming()
        except KeyboardInterrupt as exc:
            # Log error with traceback
            self.logger.error(exc, exc_info=False)
        except Exception as exc:
            self.logger.error(exc, exc_info=False)
            raise AMQPError('Could not consume from message queue')

    def _on_msg_callback_wrapper(self, ch, method, properties, body):
        _data = {}
        _ctype = None
        _cencoding = None
        _ts_send = None
        _dmode = None

        try:
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp
        except Exception:
            self.logger.debug("Failed to read message properties",
                              exc_info=True)
        try:
            _data = self._serializer.deserialize(body)
        except Exception:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            # Return data as is. Let callback handle with encoding...
            _data = {}
        try:
            self._sem.acquire()
            self._calc_msg_frequency()
            self._sem.release()
        except Exception:
            self.logger.warn("Could not calculate message rate",
                             exc_info=True)

        try:
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, _data)
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**_data))
                _clb()
        except Exception:
            self.logger.error('Error in on_msg_callback', exc_info=True)

    def _calc_msg_frequency(self) -> None:
        ts = time.time()
        if self._last_msg_ts is not None:
            diff = ts - self._last_msg_ts
            if diff < 10e-3:
                self._last_msg_ts = ts
                return
            else:
                hz = 1.0 / float(diff)
                self._msg_freq_fifo.appendleft(hz)
                hz_list = [s for s in self._msg_freq_fifo if s != 0]
                _sum = sum(hz_list)
                self._hz = _sum / len(hz_list)
        self._last_msg_ts = ts

    def stop(self) -> None:
        self.close()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, value, traceback):
        self.close()


class PSubscriber(Subscriber):

    def __init__(self, *args, **kwargs):
        kwargs['topic'] = kwargs['topic'].replace('*', '#')
        super(PSubscriber, self).__init__(*args, **kwargs)

    def _on_msg_callback_wrapper(self, ch, method, properties, body):
        _data = {}
        _ctype = None
        _cencoding = None
        _ts_send = None
        _dmode = None

        try:
            _ctype = properties.content_type
            _cencoding = properties.content_encoding
            _dmode = properties.delivery_mode
            _ts_send = properties.timestamp
        except Exception:
            self.logger.debug("Error reading message properties",
                              exc_info=True)

        try:
            _data = self._serializer.deserialize(body)
        except Exception:
            self.logger.error("Could not deserialize data",
                              exc_info=True)
            # Return data as is. Let callback handle with encoding...
            _data = {}
        try:
            _topic = method.routing_key
            _topic = _topic.replace('#', '').replace('*', '')
        except Exception:
            self.logger.error('Routing key could not be retrieved for message',
                              exc_info=True)
            return

        try:
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage,
                                             _data,
                                             _topic)
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**_data),
                                             _topic)
                _clb()
        except Exception:
            self.logger.error('Error in on_msg_callback', exc_info=True)


class ActionService(BaseActionService):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection parameters
            args: See BaseActionService parent class
            kwargs: See BaseActionService parent class
        """
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        # self._conn = Connection(conn_params)

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
        # self._conn.detach_amqp_events_thread()


class ActionClient(BaseActionClient):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.
        Action Client constructor.

        Args:
            conn_params (ConnectionParameters): Broker Connection parameters
            args: See BaseActionClient parent class
            kwargs: See BaseActionClient parent class
        """
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params

        # self._conn = Connection(conn_params)

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
                 exchange: str = 'amq.topic',
                 connection: Connection = None,
                 *args, **kwargs):
        super(EventEmitter, self).__init__(*args, **kwargs)

        self._transport = AMQPTransport(conn_params=conn_params,
                                        connection=connection,
                                        logger=self._logger)
        self._transport.connect()
        self._exchange = exchange

        if connection is None:
            self.run()

    def run(self) -> None:
        self._transport.detach_amqp_events_thread()

    def send_event(self, event: Event):
        _data = event.as_dict()
        self._logger.debug(f'Sending Event <{event.uri}>')
        self._transport.add_threadsafe_callback(
            functools.partial(self._send_data, event.uri, _data)
        )

    def _send_data(self, topic: str, data: dict) -> None:
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

        msg_props = MessageProperties(
            content_type=_type,
            content_encoding=_encoding,
            message_id=0,
        )

        self._transport._channel.basic_publish(
            exchange=self._exchange,
            routing_key=topic,
            properties=msg_props,
            body=_payload)
