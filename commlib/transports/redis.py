import datetime
import functools
import sys
import time
from typing import Any, Dict, Tuple, Callable

import redis

from commlib.action import (BaseActionClient, BaseActionService,
                            _ActionCancelMessage, _ActionFeedbackMessage,
                            _ActionGoalMessage, _ActionResultMessage,
                            _ActionStatusMessage)
from commlib.events import BaseEventEmitter, Event
from commlib.exceptions import RPCClientTimeoutError, SubscriberError
from commlib.logger import Logger
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import BaseRPCClient, BaseRPCService
from commlib.serializer import Serializer, JSONSerializer
from commlib.compression import CompressionType, inflate_str, deflate
from commlib.utils import gen_timestamp
from commlib.connection import ConnectionParametersBase

redis_logger = None


class ConnectionParameters(ConnectionParametersBase):
    host: str = 'localhost'
    port: int = 6379
    unix_socket: str = ''
    db: int = 0
    username: str = ''
    password: str = ''


class RedisConnection(redis.Redis):
    """RedisConnection.
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super(RedisConnection, self).__init__(*args, **kwargs)


class RedisTransport(object):
    @classmethod
    def logger(cls) -> Logger:
        global redis_logger
        if redis_logger is None:
            redis_logger = Logger('redis')
        return redis_logger

    def __init__(self,
                 conn_params: Any = None,
                 compression: CompressionType = CompressionType.DEFAULT_COMPRESSION,
                 serializer: Serializer = JSONSerializer()):
        """__init__.

        Args:
            conn_params (Any): conn_params
            serializer (Serializer): serializer
            compression (CompressionType): compression
        """
        conn_params = ConnectionParameters() if \
            conn_params is None else conn_params
        self._conn_params = conn_params
        self._serializer = serializer
        self._compression = compression

        try:
            self.connect()
        except Exception as e:
            self.log.error(
                f'Failed to connect to Redis <redis://' + \
                f'{self._conn_params.host}:{self._conn_params.port}>')
            raise e
        self.log.debug('Redis Transport initiated:')
        self.log.debug(
            f'- Broker: mqtt://' + \
            f'{self._conn_params.host}:{self._conn_params.port}'
        )
        self.log.debug(f'- Data Serialization: {self._serializer}')
        self.log.debug(f'- Data Compression: {self._compression}')

    @property
    def log(self) -> Logger:
        """logger.

        Args:

        Returns:
            Logger:
        """
        return self.logger()

    def connect(self):
        if self._conn_params.unix_socket not in ('', None):
            self._redis = RedisConnection(
                unix_socket_path=self._conn_params.unix_socket,
                username=self._conn_params.username,
                password=self._conn_params.password,
                db=self._conn_params.db,
                decode_responses=True)
        else:
            self._redis = RedisConnection(
                host=self._conn_params.host,
                port=self._conn_params.port,
                username=self._conn_params.username,
                password=self._conn_params.password,
                db=self._conn_params.db,
                decode_responses=False)

        self._rsub = self._redis.pubsub()

    def delete_queue(self, queue_name: str) -> bool:
        # self.log.debug('Removing message queue: <{}>'.format(queue_name))
        return True if self._redis.delete(queue_name) else False

    def queue_exists(self, queue_name: str) -> bool:
        return True if self._redis.exists(queue_name) else False

    def push_msg_to_queue(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        if self._compression != CompressionType.NO_COMPRESSION:
            payload = inflate_str(payload)
        self._redis.rpush(queue_name, payload)

    def publish(self, queue_name: str, data: Dict[str, Any]):
        payload = self._serializer.serialize(data)
        if self._compression != CompressionType.NO_COMPRESSION:
            payload = inflate_str(payload)
        self._redis.publish(queue_name, payload)

    def subscribe(self, topic: str, callback: Callable):
        _clb = functools.partial(self._on_msg_internal, callback)
        self._sub = self._rsub.psubscribe(
            **{topic: _clb})
        self._rsub.get_message()
        t = self._rsub.run_in_thread(0.001, daemon=True)
        return t

    def _on_msg_internal(self, callback: Callable, data: Any):
        if self._compression != CompressionType.NO_COMPRESSION:
            # _topic = data['channel']
            data['data'] = deflate(data['data'])
        callback(data)

    def wait_for_msg(self, queue_name: str, timeout=10):
        try:
            msgq, payload = self._redis.blpop(queue_name, timeout=timeout)
            if self._compression != CompressionType.NO_COMPRESSION:
                payload = deflate(payload)
        except Exception as exc:
            self.log.error(exc, exc_info=True)
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
                                         serializer=self._serializer,
                                         compression=self._compression)

    def _send_response(self, data, reply_to):
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.dict()
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request(self, data: dict, header: dict):
        try:
            if self._msg_type is None:
                resp = self.on_request(data)
            else:
                resp = self.on_request(self._msg_type.Request(**data))
                ## RPCMessage.Response object here
                resp = resp.dict()
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
    """RPCClient.
    """

    def __init__(self,
                 conn_params: ConnectionParameters = None,
                 *args, **kwargs):
        """__init__.

        Args:
            conn_params (ConnectionParameters): conn_params
            args:
            kwargs:
        """
        super(RPCClient, self).__init__(*args, **kwargs)
        self._transport = RedisTransport(conn_params=conn_params,
                                         serializer=self._serializer,
                                         compression=self._compression)

    def _gen_queue_name(self):
        return f'rpc-{self._gen_random_id()}'

    def _prepare_request(self, data):
        self._comm_obj.header.timestamp = gen_timestamp()   #pylint: disable=E0237
        self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.dict()

    def call(self, msg: RPCMessage.Request,
             timeout: float = 30) -> RPCMessage.Response:
        ## TODO: Evaluate msg type passed here.
        if self._msg_type is None:
            data = msg
        else:
            data = msg.dict()

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
                                         serializer=self._serializer,
                                         compression=self._compression)

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
            data = msg.dict()
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
            data = msg.dict()
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
                                         serializer=self._serializer,
                                         compression=self._compression)

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
        conn_params = ConnectionParameters() if \
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
        conn_params = gonnectionParameters() if \
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

        self._transport = RedisTransport(conn_params=conn_params)

    def send_event(self, event: Event) -> None:
        """send_event.

        Args:
            event (Event): The Event to send.

        Returns:
            None:
        """
        _msg = event.dict()
        self.log.debug(f'Firing Event: {event.name}:<{event.uri}>')
        self._transport.publish(event.uri, _msg)
