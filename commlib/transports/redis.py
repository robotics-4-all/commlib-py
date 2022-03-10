import datetime
import functools
import sys
import time
from typing import Any, Dict, Tuple

import redis

from commlib.action import (BaseActionClient, BaseActionService,
                            _ActionCancelMessage, _ActionFeedbackMessage,
                            _ActionGoalMessage, _ActionResultMessage,
                            _ActionStatusMessage)
from commlib.events import BaseEventEmitter, Event
from commlib.exceptions import RPCClientTimeoutError, SubscriberError
from commlib.logger import Logger
from commlib.msg import DataClass, DataField, Object, PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import BaseRPCClient, BaseRPCService
from commlib.serializer import Serializer, JSONSerializer
from commlib.utils import gen_timestamp


class Credentials(object):
    def __init__(self, username: str = '', password: str = ''):
        self.username = username

        self.password = password


class ConnectionParametersBase(object):
    __slots__ = ['db', 'creds']

    def __init__(self, db: int = 0, creds: Credentials = None):
        self.db = db

        if creds is None:
            creds = Credentials()
        self.creds = creds

    @property
    def credentials(self):
        return self.creds


class TCPConnectionParameters(ConnectionParametersBase):
    """TCPConnectionParameters.
    Redis TCP connection parameters
    """

    def __init__(self,
                 host: str = 'localhost',
                 port: str = 6379,
                 *args, **kwargs):
        """__init__.

        Args:
            host (str): host
            port (str): port
            args: See ConnectionParametersBase class
            kwargs: See ConnectionParametersBase class
        """
        super(TCPConnectionParameters, self).__init__(*args, **kwargs)
        self.host = host
        self.port = port


class UnixSocketConnectionParameters(ConnectionParametersBase):
    def __init__(self,
                 unix_socket: str = '/tmp/redis.sock',
                 *args, **kwargs):
        """__init__.

        Args:
            unix_socket (str): unix_socket
            args: See ConnectionParametersBase class
            kwargs: See ConnectionParametersBase class
        """
        super(UnixSocketConnectionParameters, self).__init__(*args, **kwargs)
        self.unix_socket = unix_socket


class ConnectionParameters(TCPConnectionParameters):
    def __init__(self, *args, **kwargs):
        super(ConnectionParameters, self).__init__(*args, **kwargs)


class RedisConnection(redis.Redis):
    def __init__(self, *args, **kwargs):
        super(RedisConnection, self).__init__(*args, **kwargs)


class RedisTransport(object):
    def __init__(self,
                 conn_params: Any = None,
                 serializer: Serializer = JSONSerializer(),
                 logger: Any = None):
        """__init__.

        Args:
            conn_params (Any): conn_params
            serializer (Serializer): serializer
            logger (Any): logger
        """
        conn_params = TCPConnectionParameters() if \
            conn_params is None else conn_params
        self._conn_params = conn_params

        self._serializer = serializer

        self.logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        try:
            self.connect()
        except Exception as e:
            self.logger.error(
                f'Failed to connect to Redis broker <{self._conn_params.host}' +
                f'{self._conn_params.port}>')
            raise e
        else:
            self.logger.debug(
                f'Connected to Redis <{self._conn_params.host}:{self._conn_params.port}>')


    def connect(self):
        if isinstance(self._conn_params, UnixSocketConnectionParameters):
            self._redis = RedisConnection(
                unix_socket_path=self._conn_params.unix_socket,
                username=self._conn_params.credentials.username,
                password=self._conn_params.credentials.password,
                db=self._conn_params.db,
                decode_responses=True)
        elif isinstance(self._conn_params, TCPConnectionParameters):
            self._redis = RedisConnection(
                host=self._conn_params.host,
                port=self._conn_params.port,
                username=self._conn_params.credentials.username,
                password=self._conn_params.credentials.password,
                db=self._conn_params.db,
                decode_responses=True)

        self._rsub = self._redis.pubsub()


    def delete_queue(self, queue_name: str) -> bool:
        # self.logger.debug('Removing message queue: <{}>'.format(queue_name))
        return True if self._redis.delete(queue_name) else False

    def queue_exists(self, queue_name: str) -> bool:
        return True if self._redis.exists(queue_name) else False

    def push_msg_to_queue(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        self._redis.rpush(queue_name, payload)

    def publish(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        self._redis.publish(queue_name, payload)

    def subscribe(self, topic: str, callback: callable):
        self._sub = self._rsub.psubscribe(
            **{topic: callback})
        self._rsub.get_message()
        t = self._rsub.run_in_thread(0.001, daemon=True)
        return t

    def wait_for_msg(self, queue_name: str, timeout=10):
        try:
            msgq, payload = self._redis.blpop(queue_name, timeout=timeout)
        except Exception as exc:
            self.logger.error(exc, exc_info=True)
            msgq = ''
            payload = None
        return msgq, payload


class RPCService(BaseRPCService):
    """RPCService.
    Redis RPC Service class
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args: See BaseRPCService class
            kwargs: See BaseRPCService class
        """
        super(RPCService, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def _send_response(self, data, reply_to):
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.as_dict()
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request(self, data: dict, header: dict):
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

    def run_forever(self):
        if self._transport.queue_exists(self._rpc_name):
            self._transport.delete_queue(self._rpc_name)
        while True:
            msgq, payload = self._transport.wait_for_msg(self._rpc_name,
                                                         timeout=0)

            self._detach_request_handler(payload)
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.logger.debug('Stop event caught in thread')
                    self._transport.delete_queue(self._rpc_name)
                    break
            time.sleep(0.001)

    def stop(self):
        self._t_stop_event.set()

    def _detach_request_handler(self, payload):
        data, header = self._unpack_comm_msg(payload)
        self.logger.debug(f'RPC Request <{self._rpc_name}>')
        _future = self.__exec_in_thread(
            functools.partial(self._on_request, data, header)
        )
        return _future

    def _unpack_comm_msg(self, payload: str) -> Tuple:
        _payload = self._serializer.deserialize(payload)
        _data = _payload['data']
        _header = _payload['header']
        return _data, _header

    def __exec_in_thread(self, on_request):
        _future = self._executor.submit(on_request)
        return _future


class RPCClient(BaseRPCClient):
    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def _gen_queue_name(self):
        return f'rpc-{self._gen_random_id()}'

    def _prepare_request(self, data):
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.as_dict()

    def call(self, msg: RPCMessage.Request,
             timeout: float = 30) -> RPCMessage.Response:
        ## TODO: Evaluate msg type passed here.
        if self._msg_type is None:
            data = msg
        else:
            data = msg.as_dict()

        _msg = self._prepare_request(data)
        _reply_to = _msg['header']['reply_to']
        self._transport.push_msg_to_queue(self._rpc_name, _msg)
        _, _msg = self._transport.wait_for_msg(_reply_to, timeout=timeout)
        self._transport.delete_queue(_reply_to)
        if _msg is None:
            return None
        data, header = self._unpack_comm_msg(_msg)
        ## TODO: Evaluate response type and raise exception if necessary
        if self._msg_type is None:
            return data
        else:
            return self._msg_type.Response(**data)

    def _unpack_comm_msg(self, payload: str) -> Tuple:
        _payload = self._serializer.deserialize(payload)
        _data = _payload['data']
        _header = _payload['header']
        return _data, _header


class Publisher(BasePublisher):
    """Publisher.
    MQTT Publisher (Single Topic).
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 queue_size: int = 10,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            queue_size (int): queue_size
            args:
            kwargs:
        """
        self._queue_size = queue_size
        self._msg_seq = 0

        super(Publisher, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

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
            data = msg.as_dict()
        self.logger.debug(f'Publishing Message to topic <{self._topic}>')
        self._transport.publish(self._topic, data)
        self._msg_seq += 1

    def _publish(self, data, topic) -> None:
        pass


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
        super(MPublisher, self).__init__(topic='*', *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str) -> None:
        """publish.

        Args:
            msg (PubSubMessage): Message to publish
            topic (str): Topic (URI) to send the message

        Returns:
            None:
        """
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError('Argument "msg" must be of type PubSubMessage')
        elif isinstance(msg, dict):
            data = msg
        elif isinstance(msg, PubSubMessage):
            data = msg.as_dict()
        self.logger.debug(
            f'Publishing Message: <{topic}>:{data}')
        self._transport.publish(topic, data)
        self._msg_seq += 1


class Subscriber(BaseSubscriber):
    """Subscriber.
    Redis Subscriber
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 queue_size: int = 1,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            queue_size (int): queue_size
            args:
            kwargs:
        """
        self._queue_size = queue_size
        super(Subscriber, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

    def run(self):
        self._subscriber_thread = self._transport.subscribe(self._topic,
                                                            self._on_message)
        self.logger.debug(f'Started Subscriber: <{self._topic}>')

    def stop(self):
        """Stop background thread that handle subscribed topic messages"""
        try:
            self._exit_gracefully()
        except Exception as exc:
            self.logger.error(f'Exception thrown in Subscriber.stop(): {exc}')

    def run_forever(self):
        self.run()
        while True:
            time.sleep(0.001)

    def _on_message(self, payload: Dict[str, Any]):
        try:
            data, uri = self._unpack_comm_msg(payload)
            if self.onmessage is not None:
                if self._msg_type is None:
                    _clb = functools.partial(self.onmessage, data)
                else:
                    _clb = functools.partial(self.onmessage,
                                             self._msg_type(**data))
                _clb()
        except Exception:
            self.logger.error('Exception caught in _on_message', exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        _uri = msg['channel']
        _data = self._serializer.deserialize(msg['data'])
        return _data, _uri

    def _exit_gracefully(self):
        self._subscriber_thread.stop()


class PSubscriber(Subscriber):
    """PSubscriber.
    Redis Pattern-based Subscriber.
    """

    def _on_message(self, payload: Dict[str, Any]) -> None:
        try:
            data, topic = self._unpack_comm_msg(payload)
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


class ActionService(BaseActionService):
    """ActionService.
    Redis Action Server class
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection Parameters
            args: See BaseActionService class.
            kwargs:
        """
        conn_params = UnixSocketConnectionParameters() if \
            conn_params is None else conn_params

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
    Redis Action Client class
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection Parameters
            args: See BaseActionClient class
            kwargs: See BaseActionClient class
        """
        conn_params = UnixSocketConnectionParameters() if \
            conn_params is None else conn_params

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
    Redis EventEmitter class
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): Broker Connection Parameters
            args: See BaseEventEmitter class
            kwargs: See BaseEventEmitter class
        """
        super(EventEmitter, self).__init__(*args, **kwargs)

        self._transport = RedisTransport(conn_params=conn_params,
                                         logger=self._logger)

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
