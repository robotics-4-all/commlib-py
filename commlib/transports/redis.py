"""Redis transport implementation.

Provides Redis-based pub/sub and RPC communication with automatic reconnection
and subscription restoration on connection loss.
"""

import functools
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple, Union

import redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError  # pylint: disable=redefined-builtin
from rich import console as _rich_console_mod, pretty

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
from commlib.endpoints import EndpointState
from commlib.exceptions import RPCRequestError
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
from commlib.serializer import JSONSerializer
from commlib.task_queue import (
    BaseTaskProducer,
    BaseTaskWorker,
    TaskEnvelope,
    TaskProgress,
    TaskResult,
)
from commlib.transports.base_transport import BaseTransport
from commlib.utils import gen_timestamp

pretty.install()
console: Any = _rich_console_mod.Console()

redis_logger = None


# Shared Redis connection pool registry
# Reduces connection count by 6-10x by sharing pools across instances
_REDIS_POOL_REGISTRY: Dict[Tuple, Any] = {}
_REDIS_POOL_LOCK = threading.Lock()
_REDIS_POOL_REFCOUNT: Dict[Tuple, int] = {}


def _get_pool_key(conn_params: "ConnectionParameters") -> Tuple:
    """Generate unique key for connection pool.

    Args:
        conn_params: Redis connection parameters

    Returns:
        Tuple key identifying unique connection pool
    """
    if conn_params.unix_socket not in ("", None):
        return ("unix", conn_params.unix_socket, conn_params.db)
    return ("tcp", conn_params.host, conn_params.port, conn_params.db)


def get_or_create_redis_pool(
    conn_params: "ConnectionParameters",
) -> Any:
    """Get or create shared Redis connection pool.

    Shares connection pools across Redis transport instances with the same
    connection parameters. This dramatically reduces connection count.

    Args:
        conn_params: Redis connection parameters

    Returns:
        redis.ConnectionPool: Shared connection pool
    """
    key = _get_pool_key(conn_params)

    with _REDIS_POOL_LOCK:
        if key not in _REDIS_POOL_REGISTRY:
            # Create new pool
            _retry = (
                Retry(
                    ExponentialBackoff(
                        conn_params.reconnect_attempts * conn_params.reconnect_delay
                    ),
                    int(conn_params.reconnect_delay),
                )
                if conn_params.reconnect_attempts > 0
                else None
            )

            if conn_params.unix_socket in ("", None):
                pool = redis.ConnectionPool(
                    host=conn_params.host,
                    port=conn_params.port,
                    username=conn_params.username,
                    password=conn_params.password,
                    db=conn_params.db,
                    decode_responses=False,
                    socket_timeout=conn_params.socket_timeout,
                    health_check_interval=conn_params.healthcheck_interval,
                    max_connections=None,
                )
            else:
                pool = redis.ConnectionPool(
                    unix_socket_path=conn_params.unix_socket,
                    username=conn_params.username,
                    password=conn_params.password,
                    db=conn_params.db,
                    decode_responses=False,
                    socket_timeout=conn_params.socket_timeout,
                    socket_keep_alive=True,
                    health_check_interval=conn_params.healthcheck_interval,
                    max_connections=None,
                )

            _REDIS_POOL_REGISTRY[key] = pool
            _REDIS_POOL_REFCOUNT[key] = 0

        # Increment reference count
        _REDIS_POOL_REFCOUNT[key] += 1
        return _REDIS_POOL_REGISTRY[key]


def release_redis_pool(conn_params: "ConnectionParameters") -> None:
    """Release reference to Redis connection pool.

    Decrements reference count. When count reaches 0, pool is disconnected
    and removed from registry.

    Args:
        conn_params: Redis connection parameters
    """
    key = _get_pool_key(conn_params)

    with _REDIS_POOL_LOCK:
        if key in _REDIS_POOL_REFCOUNT:
            _REDIS_POOL_REFCOUNT[key] -= 1

            if _REDIS_POOL_REFCOUNT[key] <= 0:
                # No more references, clean up
                pool = _REDIS_POOL_REGISTRY.pop(key, None)
                _REDIS_POOL_REFCOUNT.pop(key, None)

                if pool is not None:
                    pool.disconnect()


class ConnectionParameters(BaseConnectionParameters):
    """Connection Parameters."""

    host: str = "localhost"
    port: int = 6379
    unix_socket: str = ""
    db: int = 0
    username: str = ""
    password: str = ""
    socket_timeout: Union[float, None] = None
    healthcheck_interval: Union[float, None] = None


class RedisConnection(redis.Redis):  # type: ignore[reportAttributeAccessIssue]
    """RedisConnection."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)


class RedisTransport(BaseTransport):
    """Redis Transport."""

    _redis_pool = None

    @classmethod
    def set_redis_pool(cls, pool):
        """Set redis pool."""
        cls._redis_pool = pool

    @classmethod
    def get_redis_pool(cls):
        """Get redis pool."""
        return cls._redis_pool

    @classmethod
    def reset_redis_pool(cls) -> None:
        """Disconnect and clear the class-level Redis connection pool.

        Intended for testing and benchmarks that need a clean pool state.
        """
        if cls._redis_pool is not None:
            try:
                cls._redis_pool.disconnect()
            except Exception:  # pylint: disable=broad-except
                pass
        _REDIS_POOL_REGISTRY.clear()
        _REDIS_POOL_REFCOUNT.clear()
        cls._redis_pool = None

    @classmethod
    def logger(cls) -> logging.Logger:
        """Logger."""
        global redis_logger  # pylint: disable=global-statement
        if redis_logger is None:
            redis_logger = logging.getLogger(__name__)
        return redis_logger

    def __init__(
        self,
        *args,
        compression: int = CompressionType.DEFAULT_COMPRESSION,
        serializer: Any = None,
        **kwargs,
    ):
        """
        Initialize the RedisTransport.

        Args:
            compression (CompressionType): The compression type to use for message compression.
                Defaults to CompressionType.DEFAULT_COMPRESSION.
            serializer (Serializer): The serializer to use for message serialization.
                Defaults to JSONSerializer().
            *args: Variable length argument list to be passed to the parent class constructor.
            **kwargs: Arbitrary keyword arguments to be passed to the parent class constructor.
        """
        super().__init__(*args, **kwargs)
        self._serializer = serializer if serializer is not None else JSONSerializer()
        self._compression = compression
        self._rsub: Any = None
        self._redis: Optional[RedisConnection] = None
        self._redis_pubsub_join_timeout = 1  # sec
        self._rsub_thread = None
        self._wait_for_connection_init = 0.1  # sec
        self._wait_for_pubsub_stop = 0.1  # sec
        self._subscription_sleep_interval = 0.001  # sec
        self._subscriptions: Dict[
            str, Callable
        ] = {}  # Track subscriptions for reconnection
        self._retry_count = 0
        self._stopped = False

        if self._redis_pool is None:
            # Use shared connection pool (reduces connections by 6-10x)
            self.set_redis_pool(get_or_create_redis_pool(self._conn_params))
            self._owns_pool = False
        else:
            self._owns_pool = True

    @property
    def pubsub_alive(self):
        """Pubsub alive."""
        return self._rsub_thread.is_alive() if self._rsub_thread else False

    @property
    def is_connected(self) -> bool:
        """Is connected."""
        try:
            if self._redis is None:
                return False
            self._redis.ping()
            return True
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            return False

    @property
    def log(self) -> logging.Logger:
        """Log."""
        return self.logger()

    def _build_conn_pool(self):
        _retry = (
            Retry(
                ExponentialBackoff(
                    self._conn_params.reconnect_attempts
                    * self._conn_params.reconnect_delay
                ),
                self._conn_params.reconnect_delay,
            )
            if self._conn_params.reconnect_attempts > 0
            else None
        )
        _retry_on_error = (
            [ConnectionError, TimeoutError, BusyLoadingError, ConnectionRefusedError]
            if self._conn_params.reconnect_attempts > 0
            else None
        )
        if self._conn_params.unix_socket in ("", None):
            return redis.ConnectionPool(
                host=self._conn_params.host,
                port=self._conn_params.port,
                username=self._conn_params.username,
                password=self._conn_params.password,
                db=self._conn_params.db,
                decode_responses=False,
                socket_timeout=self._conn_params.socket_timeout,
                health_check_interval=self._conn_params.healthcheck_interval,
                # retry=retry,
                # retry_on_error=retry_on_error,
                max_connections=None,
            )
        return redis.ConnectionPool(
            unix_socket_path=self._conn_params.unix_socket,
            username=self._conn_params.username,
            password=self._conn_params.password,
            db=self._conn_params.db,
            decode_responses=False,
            socket_timeout=self._conn_params.socket_timeout,
            socket_keep_alive=True,
            health_check_interval=self._conn_params.healthcheck_interval,
            # retry=retry,
            # retry_on_error=retry_on_error,
            max_connections=None,
        )

    def connect(self) -> None:
        """Connect."""
        self._stopped = False
        if self._conn_params.unix_socket not in ("", None):
            self._redis = RedisConnection(
                connection_pool=self.get_redis_pool(),
            )
        else:
            self._redis = RedisConnection(
                connection_pool=self.get_redis_pool(),
            )
        self._rsub = self._redis.pubsub(
            ignore_subscribe_messages=True,
        )
        try:
            self._redis.ping()
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as e:
            raise ConnectionError(f"Could not connect to Redis server: {e}") from e
        self._retry_count = 0

    def start(self) -> None:
        """
        Starts the transport connection.

        This method ensures that the transport is connected before proceeding.
        If the transport is not connected, it attempts to establish a connection
        and waits until the connection is successfully initialized.

        Raises:
            Exception: If the connection cannot be established after multiple attempts.
        """
        if not self.is_connected:
            try:
                self.connect()
            except (
                RuntimeError,
                ConnectionError,
                TimeoutError,
                ValueError,
                KeyError,
                AttributeError,
                OSError,
            ) as e:
                self.log.error("Could not establish connection to Redis: %s", e)
            time.sleep(self._wait_for_connection_init)
        while not self.is_connected:
            self._attempt_reconnect()

    def _max_retries_exceeded(self) -> bool:
        max_retries = self._conn_params.reconnect_attempts
        if max_retries <= 0:
            return False
        return self._retry_count >= max_retries

    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to Redis."""
        if self._max_retries_exceeded():
            raise ConnectionError("Maximum connection attempts exceeded")
        self._retry_count += 1
        try:
            self.log.info(
                "Attempting to reconnect to Redis (attempt %s/%s)...",
                self._retry_count,
                self._conn_params.reconnect_attempts,
            )
            time.sleep(self._conn_params.reconnect_delay)
            self.connect()
            if self.is_connected:
                self.log.info("Successfully reconnected to Redis")
                self._retry_count = 0  # Reset counter on successful connection
                return True
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as e:
            self.log.warning("Reconnection attempt failed: %s", e)
        return False

    def stop(self) -> None:
        """
        Stops the Redis transport by disconnecting and cleaning up resources.

        This method ensures that the transport is properly stopped by:
        - Stopping the Redis subscription thread if it exists.
        - Closing the Redis subscription object if it exists.
        - Disconnecting and closing the Redis client, ensuring all in-use connections
          are released.

        Note:
            A small delay is introduced to allow the subscription thread to stop
            gracefully.

        Raises:
            Any exceptions raised during the cleanup process will propagate to the caller.
        """
        if not self.is_connected:
            self.log.debug("Attempting to stop transport while not connected")
        self._stopped = True
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        if self._rsub is not None:
            self._rsub.close()
        if self._redis is not None:
            self._redis.close()
            del self._redis

        # Release shared pool reference (if using shared pool)
        if not self._owns_pool:
            release_redis_pool(self._conn_params)

    def delete_queue(self, queue_name: str) -> bool:
        """Delete queue."""
        assert self._redis is not None
        return True if self._redis.delete(queue_name) else False

    def queue_exists(self, queue_name: str) -> bool:
        """Queue exists."""
        assert self._redis is not None
        return True if self._redis.exists(queue_name) else False

    def create_queue(self, queue_name: str) -> bool:
        """Create queue."""
        assert self._redis is not None
        self._redis.rpush(queue_name, "QueueInit")
        return True

    def push_msg_to_queue(self, queue_name: str, data: Dict[str, Any]):
        """Push msg to queue."""
        if not self.is_connected:
            self.log.warning("Transport not connected - Cannot push message to queue!")
            self._attempt_reconnect()
            return self.push_msg_to_queue(queue_name, data)
        assert self._redis is not None
        try:
            payload = self._serializer.serialize(data)
            if self._compression != CompressionType.NO_COMPRESSION:
                payload = inflate_str(payload, int(self._compression))
            self._redis.rpush(queue_name, payload)
        except redis.exceptions.ConnectionError as e:  # type: ignore[reportAttributeAccessIssue]
            self.log.warning("Redis connection error while pushing to queue: %s", e)
            self._attempt_reconnect()
            return self.push_msg_to_queue(queue_name, data)

    def publish(self, queue_name: str, data: Dict[str, Any]):
        """Publish."""
        if not self.is_connected:
            self.log.warning("Transport not connected - Cannot publish message!")
            self._attempt_reconnect()
            return self.publish(queue_name, data)
        assert self._redis is not None
        try:
            payload = self._serializer.serialize(data)
            if self._compression != CompressionType.NO_COMPRESSION:
                payload = inflate_str(payload, int(self._compression))
            self._redis.publish(queue_name, payload)
        except redis.exceptions.ConnectionError as e:  # type: ignore[reportAttributeAccessIssue]
            self.log.warning("Redis connection error while publishing: %s", e)
            self._attempt_reconnect()
            return self.publish(queue_name, data)

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe."""
        if topic in (None, ""):
            self.log.warning("Attempt to subscribe to empty topic - %s", topic)
            return
        _clb = functools.partial(self._on_msg_internal, callback)
        # Track subscription for reconnection
        self._subscriptions[topic] = callback
        if self._rsub is None:
            self.log.warning(
                "Redis pubsub not initialized - Cannot proceed to subscriptions!"
            )
            return
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        self._rsub.psubscribe(**{topic: _clb})
        # Run the subscription in a background thread
        self._rsub_thread = self._rsub.run_in_thread(
            sleep_time=self._subscription_sleep_interval,  # type: ignore[reportArgumentType]
            exception_handler=self.exception_handler,
            daemon=True,
        )
        return self._rsub_thread

    def exception_handler(self, ex, pubsub, thread):
        """Exception handler."""
        if not self._stopped:
            self.log.debug(
                "Redis PubSub error in thread: %s, exception: %s", thread, ex
            )
        thread.stop()
        # thread.join(timeout=self._redis_pubsub_join_timeout)
        pubsub.close()
        pubsub.connection_pool.disconnect(inuse_connections=True)

        # Attempt to reconnect with retries
        self._attempt_pubsub_reconnect()

    def _attempt_pubsub_reconnect(self):
        """Attempt to reconnect the pubsub connection and re-subscribe to topics."""
        if not self._subscriptions:
            self.log.debug("No subscriptions to restore")
            return

        retry_count = self._retry_count
        max_retries = self._conn_params.reconnect_attempts

        # If reconnect_attempts is 0, don't attempt reconnection
        if max_retries <= 0:
            self.log.debug("Reconnection disabled (reconnect_attempts=0)")
            return

        if retry_count >= max_retries:
            self.log.error(
                "Maximum reconnection attempts (%s) reached. "
                "Will not attempt further reconnections.",
                max_retries,
            )
            return

        delay = self._conn_params.reconnect_delay  # Use configured delay

        while self._retry_count < max_retries:
            try:
                self.log.debug(
                    "Attempting pubsub reconnection (attempt %s/%s)...",
                    retry_count + 1,
                    max_retries,
                )

                self._retry_count += 1

                # Re-initialize the pubsub
                self._rsub = None
                time.sleep(self._wait_for_connection_init)

                # Ping to check connection
                if not self.is_connected:
                    time.sleep(delay)
                    self.connect()

                if self.is_connected:
                    # Recreate pubsub
                    self.log.info("Successfully reconnected to Redis")
                    assert self._redis is not None
                    self._rsub = self._redis.pubsub(
                        ignore_subscribe_messages=True,
                    )

                    # Re-subscribe to all topics
                    for topic in self._subscriptions.keys():
                        callback = self._subscriptions[topic]
                        _clb = functools.partial(self._on_msg_internal, callback)
                        self._rsub.psubscribe(**{topic: _clb})

                    # Restart the subscription thread
                    self._rsub_thread = self._rsub.run_in_thread(
                        sleep_time=(  # type: ignore[reportArgumentType]
                            self._subscription_sleep_interval
                        ),
                        exception_handler=self.exception_handler,
                        daemon=True,
                    )

                    self.log.info("Pubsub reconnection successful")
                    return True

            except (
                RuntimeError,
                ConnectionError,
                TimeoutError,
                ValueError,
                KeyError,
                AttributeError,
                OSError,
            ) as e:
                self.log.warning("Pubsub reconnection attempt failed: %s", e)

        self.log.error("Failed to reconnect pubsub after %s attempts", max_retries)
        return False

    def msubscribe(self, topics: Dict[str, Callable]):
        """Msubscribe."""
        _topics = {}
        for topic, callback in topics.items():
            _clb = functools.partial(self._on_msg_internal, callback)
            _topics[topic] = _clb
        if _topics in (None, {}):
            self.log.warning("Attempt to subscribe to empty topics - %s", _topics)
            return
        if self._rsub is None:
            self.log.warning(
                "Redis pubsub not initialized - Cannot proceed to subscriptions!"
            )
            return
        # If already in subscription, close and append new topics
        if self._rsub_thread is not None:
            self._rsub_thread.stop()
            time.sleep(self._wait_for_pubsub_stop)
        self._rsub.psubscribe(**_topics)
        # Run the subscription in a background thread
        self._rsub_thread = self._rsub.run_in_thread(
            0.001,  # type: ignore[reportArgumentType]
            daemon=True,
            exception_handler=self.exception_handler,
        )
        return self._rsub_thread

    def _on_msg_internal(self, callback: Callable, data: Any):
        if self._compression != CompressionType.NO_COMPRESSION:
            # _topic = data['channel']
            data["data"] = deflate(data["data"], int(self._compression))
        callback(data)

    def wait_for_msg(self, queue_name: str, timeout=10):
        """Wait for msg."""
        try:
            if not self.is_connected:
                self.log.warning(
                    "Transport not connected - Cannot push message to queue!"
                )
                self._attempt_reconnect()
                return self.wait_for_msg(queue_name, timeout)
            assert self._redis is not None
            result = self._redis.blpop([queue_name], timeout=timeout)  # type: ignore[union-attr]
            if result is None:
                return "", None
            msgq, payload = result  # type: ignore[misc]
            if isinstance(payload, bytes) and payload == b"QueueInit":
                return self.wait_for_msg(queue_name, timeout)
            if self._compression != CompressionType.NO_COMPRESSION:
                payload = deflate(payload, int(self._compression))
            return msgq, payload
        except redis.exceptions.TimeoutError:  # type: ignore[reportAttributeAccessIssue]
            # Check if it's a timeout or actual connection error
            msgq = ""
            payload = None
            return msgq, payload
        except TypeError:
            msgq = ""
            payload = None
            return msgq, payload
        except redis.exceptions.ConnectionError as e:  # type: ignore[reportAttributeAccessIssue]
            self.log.warning("Redis connection error: %s", e)
            self._attempt_reconnect()
            return self.wait_for_msg(queue_name, timeout)


class RPCService(BaseRPCService):
    """RPCService.
    Redis RPC Service class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseRPCService class
            kwargs: See BaseRPCService class
        """
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        assert self._transport is not None
        self._transport.push_msg_to_queue(reply_to, _resp)

    def _on_request_handle(self, payload):
        try:
            req_msg, _topic = self._unpack_comm_msg(payload)
            self._executor.submit(self._on_request_internal, req_msg)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)

    def _on_request_internal(self, req_msg: CommRPCMessage):
        try:
            if not self._validate_rpc_req_msg(req_msg):
                raise RPCRequestError("Request Message is invalid!")
            if self._msg_type is None:
                assert self.on_request is not None
                resp = self.on_request(req_msg.data)
            else:
                assert self.on_request is not None
                resp = self.on_request(self._msg_type.Request(**req_msg.data))
                # RPCMessage.Response object here
                resp = resp.model_dump()
        except RPCRequestError as exc:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        self._send_response(resp, req_msg.header.reply_to)

    def run_forever(self):
        """
        Continuously runs the transport, processing messages and handling stop events.

        This method starts the transport and enters an infinite loop where it waits for
        messages on the specified RPC queue. When a message is received, it detaches the
        request handler to process the payload. If a stop event is set, it breaks the loop,
        deletes the RPC queue, and stops the transport.

        Note:
            This method blocks indefinitely until a stop event is set.

        Raises:
            Exception: If there is an error starting the transport or processing messages.
        """
        assert self._transport is not None
        self._transport.start()
        self._t_stop_event.clear()
        # if self._transport.queue_exists(self._rpc_name):
        #     self._transport.delete_queue(self._rpc_name)
        # self._transport.create_queue(self._rpc_name)
        while not self._t_stop_event.is_set():
            _msgq, payload = self._transport.wait_for_msg(self._rpc_name)
            if payload is None:
                continue
            self._on_request_handle(payload)


class RPCClient(BaseRPCClient):
    """RPCClient."""

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def call(self, msg: RPCMessage.Request, timeout: float = 10) -> RPCMessage.Response:
        """
        Sends an RPC request message and waits for a response.

        Args:
            msg (RPCMessage.Request): The RPC request message to be sent.
            timeout (float, optional): The max time to wait
                for a response in seconds. Defaults to 10.

        Returns:
            RPCMessage.Response: The response message.
                Returns None if timeout is reached.
        """
        assert self._transport is not None
        try:
            data = self._prepare_call_data(msg)
        except ValueError as e:
            raise RPCRequestError(str(e)) from e
        _msg = self._prepare_request(data)
        _reply_to = _msg["header"]["reply_to"]
        # while not self._transport.queue_exists(self._rpc_name):
        #     time.sleep(0.001)
        self._transport.push_msg_to_queue(self._rpc_name, _msg)
        _, _msg = self._transport.wait_for_msg(_reply_to, timeout=timeout)
        self._transport.delete_queue(_reply_to)
        if _msg is None:
            return None  # type: ignore[return-value]
        data, _header, _uri = self._unpack_comm_msg(_msg)
        # TODO: Evaluate response type and raise exception if necessary
        if self._msg_type is None:
            return data
        return self._msg_type.Response(**data)


class Publisher(BasePublisher):
    """Publisher.
    Redis Publisher (Single Topic).
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        self._msg_seq = 0

        super().__init__(*args, **kwargs)

        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def publish(  # pylint: disable=unused-argument
        self, msg: PubSubMessage, topic: str = "", key: str = ""
    ) -> None:
        """publish.
        Publish message

        Args:
            msg (PubSubMessage): msg
            topic (str): Optional topic override
            key (str): Optional key

        Returns:
            None:
        """
        data = self._prepare_msg(msg)
        _topic = topic if topic else self._topic
        self.log.debug("Publishing Message to topic <%s>", _topic)
        assert self._transport is not None
        self._transport.publish(_topic, data)
        self._msg_seq += 1


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
        super().__init__(topic=None, *args, **kwargs)

    def publish(self, msg: PubSubMessage, topic: str = "", key: str = "") -> None:  # pylint: disable=unused-argument
        """publish.

        Args:
            msg (PubSubMessage): Message to publish
            topic (str): Topic (URI) to send the message
            key (str): Optional key

        Returns:
            None:
        """
        validate_pubsub_topic_strict(topic)
        data = self._prepare_msg(msg)
        self.log.debug("Publishing Message: <%s>:%s", topic, data)
        assert self._transport is not None
        self._transport.publish(topic, data)
        self._msg_seq += 1


class WPublisher:
    """WPublisher.
    Redis Wrapped-Publisher
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
        """Connected."""
        return self._mpub.connected

    def publish(self, msg: Union[PubSubMessage, None]) -> None:
        """Publish."""
        if self._msg_type is not None and not isinstance(msg, PubSubMessage):
            raise ValueError(f'Argument "msg" must be of type {self._msg_type}')
        assert msg is not None
        self._mpub.publish(msg, self._topic)


class Subscriber(BaseSubscriber):
    """Subscriber.
    Redis Subscriber
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            queue_size (int): queue_size
            args:
            kwargs:
        """
        self._subscriber_thread = None
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic_strict(self._topic)

    def stop(self, wait: bool = True):  # pylint: disable=unused-argument
        """
        Stops the subscriber thread if it is running and then calls the
        stop method of the superclass to perform any additional cleanup.

        This method ensures that the subscriber thread is properly stopped
        before the transport is stopped, preventing any potential issues
        with lingering threads.
        """
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Runs the subscriber thread indefinitely, with periodic checks for a stop event.

        This method starts the transport and subscribes to a topic, then enters an
        infinite loop where it periodically checks for a stop event and sends a ping
        to the Redis server to keep the connection alive.

        Args:
            interval (float): The time interval (in seconds) to wait between each
                              iteration of the loop. Default is 0.001 seconds.

        Notes:
            - The method will break out of the loop if the stop event is set.
            - The method sends a ping to the Redis server on each iteration to keep
              the connection alive.
        """
        assert self._transport is not None
        self._transport.start()
        self._subscriber_thread = self._transport.subscribe(
            self._topic, self._on_message
        )
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            if not self._transport.is_connected:
                pass
                # self.log.debug("Transport is not connected...")
            time.sleep(interval)

    def _on_message(self, payload: Dict[str, Any]):
        try:
            data, _uri = self._unpack_comm_msg(payload)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data)
                else:
                    self.onmessage(self._msg_type(**data))
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        _uri = msg["channel"]
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class WSubscriber(BaseSubscriber):
    """WSubscriber class for subscribing to topics and handling messages using a.
    single connection."""

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Initialize the WSubscriber.

        Args:
            args: See BaseSubscriber
            kwargs: See BaseSubscriber
        """
        super().__init__(topic=None, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        self._subs: Dict[str, Callable] = {}
        self._subscriber_threads = []
        self._subscriber_thread = None

    def subscribe(self, topic, callback: Callable) -> None:
        """
        Subscribe to a given topic with a callback function.

        Args:
            topic (str): The topic to subscribe to.
            callback (callable): The function to be called
                when a message is received on the topic.

        Returns:
            None
        """
        validate_pubsub_topic_strict(topic)
        self._subs[topic] = callback

    def stop(self, wait: bool = True):  # pylint: disable=unused-argument
        """
        Stops the transport by stopping all subscriber
        threads and the main subscriber thread if they exist.

        Iterates through all threads in
        ``_subscriber_threads`` and calls their ``stop``
        method. If ``_subscriber_thread`` is not None,
        also calls its ``stop`` method. Finally, calls
        the ``stop`` method of the superclass.
        """
        for sub_thread in self._subscriber_threads:
            sub_thread.stop()
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Start the subscriber and run forever, continuously handling incoming messages.

        Args:
            interval (float, optional): The interval between checking for new messages.
        """
        assert self._transport is not None
        self._transport.start()
        _topics = {}
        for topic, callback in self._subs.items():
            _topics[topic] = functools.partial(self._on_message, callback)
        self._subscriber_thread = self._transport.msubscribe(_topics)
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            if not self._transport.is_connected:
                pass
                # self.log.debug("Transport is not connected...")
            time.sleep(interval)

    def _on_message(self, callback: Callable, payload: Dict[str, Any]):
        """
        Internal method to handle incoming messages and invoke the callback function.

        Args:
            callback (Callable): The callback function to handle the message.
            payload (Dict[str, Any]): The payload of the received message.
        """
        try:
            data, _uri = self._unpack_comm_msg(payload)
            if callback is not None:
                if self._msg_type is None:
                    callback(data)
                else:
                    callback(self._msg_type(**data))
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        """
        Internal method to unpack the communication message.

        Args:
            msg (Dict[str, Any]): The communication message to unpack.

        Returns:
            Tuple: A tuple containing the unpacked data and URI.
        """
        _uri = msg["channel"]
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class PSubscriber(BaseSubscriber):
    """PSubscriber.
    Redis Pattern-based Subscriber.
    """

    def __init__(self, *args, **kwargs):
        self._subscriber_thread: Any = None
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )
        validate_pubsub_topic(self._topic)

    def stop(self, wait: bool = True):  # pylint: disable=unused-argument
        """
        Stops the Redis transport by stopping the subscriber thread if it exists,
        and then calls the stop method of the superclass.

        This method ensures that any active subscriber thread is properly stopped
        before the transport itself is stopped.
        """
        if self._subscriber_thread is not None:
            self._subscriber_thread.stop()
        super().stop()

    def run_forever(self, interval: float = 0.001):
        """
        Starts the transport and subscribes to the topic, then continuously pings
        the Redis subscription to keep the connection alive until a stop event is set.

        Args:
            interval (float): The time to wait between each ping to the Redis subscription.
                              Default is 0.001 seconds.

        The method will run indefinitely until the stop event (`self._t_stop_event`) is set.
        """
        assert self._transport is not None
        self._transport.start()
        self._subscriber_thread = self._transport.subscribe(
            self._topic, self._on_message
        )
        while True:
            if self._t_stop_event is not None:
                if self._t_stop_event.is_set():
                    self.log.debug("Stop event caught in thread")
                    break
            if not self._transport.is_connected:
                pass
                # self.log.debug("Transport is not connected...")
            time.sleep(interval)

    def _on_message(self, payload: Dict[str, Any]) -> None:
        try:
            data, topic = self._unpack_comm_msg(payload)
            if self.onmessage is not None:
                if self._msg_type is None:
                    self.onmessage(data, topic)
                else:
                    self.onmessage(self._msg_type(**data), topic)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ):
            self.log.error("Exception caught in _on_message", exc_info=True)

    def _unpack_comm_msg(self, msg: Dict[str, Any]) -> Tuple:
        """
        Internal method to unpack the communication message.

        Args:
            msg (Dict[str, Any]): The communication message to unpack.

        Returns:
            Tuple: A tuple containing the unpacked data and URI.
        """
        _uri = msg["channel"].decode("utf-8")
        assert self._serializer is not None
        _data = self._serializer.deserialize(msg["data"])
        return _data, _uri


class ActionService(BaseActionService):
    """ActionService.
    Redis Action Server class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionService class.
            kwargs:
        """
        super().__init__(*args, **kwargs)

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
    Redis Action Client class
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args: See BaseActionClient class
            kwargs: See BaseActionClient class
        """
        super().__init__(*args, **kwargs)

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
        )
        self._feedback_sub = Subscriber(
            msg_type=_ActionFeedbackMessage,
            conn_params=self._conn_params,
            topic=self._feedback_topic,
            on_message=self._on_feedback,
        )


class RPCServer(BaseRPCServer):
    """RPC Server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            serializer=self._serializer,
            compression=self._compression,
        )

    def _on_request_handle(
        self, rpc_uri: str, data: Dict[str, Any], header: Dict[str, Any]
    ):
        # Guard against bad requests
        try:
            self._executor.submit(self._on_request_internal, rpc_uri, data, header)
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)

    def _on_request_internal(
        self, rpc_uri: str, data: Dict[str, Any], header: Dict[str, Any]
    ):
        if "reply_to" not in header:
            return
        try:
            _req_msg = CommRPCMessage(
                header=CommRPCHeader(reply_to=header["reply_to"]), data=data
            )

            if not self._validate_rpc_req_msg(_req_msg):
                raise RPCRequestError("Request Message is invalid!")
            if self._base_uri not in (None, ""):
                rpc_uri = rpc_uri.replace(self._base_uri, "")
                rpc_uri = rpc_uri.lstrip(".")
            if self._svc_map[rpc_uri][1] is None:
                resp = self._svc_map[rpc_uri][0](data)
            else:
                resp = self._svc_map[rpc_uri][0](
                    self._svc_map[rpc_uri][1].Request(**data)
                )
                # RPCMessage.Response object here
                resp = resp.model_dump()
        except RPCRequestError as exc:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        except (
            RuntimeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            KeyError,
            AttributeError,
            OSError,
        ) as exc:
            self.log.error(str(exc), exc_info=False)
            resp = {}
        self._send_response(resp, _req_msg.header.reply_to)

    def _send_response(self, data: Dict[str, Any], reply_to: str):
        self._comm_obj.header.timestamp = gen_timestamp()  # pylint: disable=E0237
        self._comm_obj.data = data
        _resp = self._comm_obj.model_dump()
        assert self._transport is not None
        self._transport.push_msg_to_queue(reply_to, _resp)

    def start_endpoints(self):
        """Start endpoints."""
        for uri in self._svc_map:
            if self._base_uri in (None, ""):
                full_uri = uri
            else:
                full_uri = f"{self._base_uri}.{uri}"
            self.log.info("Registering RPC endpoint <%s>", full_uri)
            self._executor.submit(self._monitor_queue_for_requests, full_uri)
            # self._monitor_queue_for_requests(full_uri)
        # self._subscriber_thread = self._transport.msubscribe(
        #     {uri: self._on_request_handle for uri in self._svc_map.keys()})

    def _monitor_queue_for_requests(self, rpc_uri: str, timeout: float = 10):
        """
        Waits for a request message on the specified RPC queue.

        Args:
            timeout (float): The maximum time to wait for a request message in seconds.

        Returns:
            Tuple: A tuple containing the request message and the header.
        """
        assert self._transport is not None
        while not self._t_stop_event.is_set():
            _, payload = self._transport.wait_for_msg(rpc_uri, timeout=timeout)
            if payload is None:
                continue
            data, header = self._unpack_comm_msg(payload)
            self._on_request_handle(rpc_uri, data, header)

    def _unpack_comm_msg(self, payload: str) -> Tuple:
        assert self._serializer is not None
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header


class TaskProducer(BaseTaskProducer):
    """Task Producer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            compression=self._compression,
        )
        self._result_transport = None
        self._result_topic = f"{self._queue_name}.results"
        self._progress_topic = f"{self._queue_name}.progress"

    def run(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Run."""
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        self._transport.start()
        self._result_transport = RedisTransport(
            conn_params=self._conn_params,
            compression=self._compression,
        )
        self._result_transport.start()
        self._result_transport.subscribe(self._result_topic, self._on_result_msg)
        self._result_transport.subscribe(self._progress_topic, self._on_progress_msg)
        self.set_state(EndpointState.CONNECTED)

    def stop(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Stop."""
        if self._result_transport is not None:
            self._result_transport.stop()
        if self._transport is not None:
            self._transport.stop()
        self.set_state(EndpointState.DISCONNECTED)

    def _send_task(self, envelope: TaskEnvelope) -> None:
        assert self._transport is not None
        data = envelope.model_dump()
        self._transport.push_msg_to_queue(self._queue_name, data)

    def _on_result_msg(self, msg: Dict) -> None:
        data = msg.get("data", msg)
        if isinstance(data, bytes):
            data = JSONSerializer.deserialize(data)
        result = TaskResult(**data)
        self._handle_result(result)

    def _on_progress_msg(self, msg: Dict) -> None:
        data = msg.get("data", msg)
        if isinstance(data, bytes):
            data = JSONSerializer.deserialize(data)
        progress = TaskProgress(**data)
        self._handle_progress(progress)


class TaskWorker(BaseTaskWorker):
    """Task Worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = RedisTransport(
            conn_params=self._conn_params,
            compression=self._compression,
        )
        self._result_topic = f"{self._queue_name}.results"
        self._progress_topic = f"{self._queue_name}.progress"
        self._poll_thread = None

    def run(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Run."""
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        self._transport.start()
        self._stop_event.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        self.set_state(EndpointState.CONNECTED)

    def stop(self, wait: bool = True) -> None:  # pylint: disable=unused-argument
        """Stop."""
        self._stop_event.set()
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=5.0)
        if self._transport is not None:
            self._transport.stop()
        self.set_state(EndpointState.DISCONNECTED)

    def _poll_loop(self) -> None:
        assert self._transport is not None
        while not self._stop_event.is_set():
            try:
                _, payload = self._transport.wait_for_msg(self._queue_name, timeout=1)
                if payload is None:
                    continue
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = JSONSerializer.deserialize(payload)
                envelope = TaskEnvelope(**data)
                self._process_task(envelope)
            except (RuntimeError, ConnectionError, OSError) as exc:
                self.log.error("Error polling task queue: %s", exc)
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

    def _publish_result(self, result: TaskResult) -> None:
        assert self._transport is not None
        data = result.model_dump()
        self._transport.publish(self._result_topic, data)

    def _publish_progress(self, progress: TaskProgress) -> None:
        assert self._transport is not None
        data = progress.model_dump()
        self._transport.publish(self._progress_topic, data)

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        super()._send_to_dlq(envelope, error)
        assert self._transport is not None
        data = envelope.model_dump()
        data["error"] = error
        self._transport.push_msg_to_queue(self._config.get_dlq_name(), data)
