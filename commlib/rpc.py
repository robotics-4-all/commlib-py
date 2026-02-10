"""RPC client and service implementations.

Provides request-reply pattern for synchronous and asynchronous
remote procedure calls with timeout and error handling.
"""

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
import time
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel

from commlib.endpoints import BaseEndpoint, EndpointState
from commlib.msg import RPCMessage
from commlib.thread_pool import get_io_pool
from commlib.utils import gen_random_id, gen_timestamp

rpc_logger = None


class CommRPCHeader(BaseModel):
    reply_to: str = ""
    timestamp: Optional[int] = gen_timestamp()
    content_type: Optional[str] = "json"
    encoding: Optional[str] = "utf8"
    agent: Optional[str] = "commlib"


class CommRPCMessage(BaseModel):
    header: CommRPCHeader = CommRPCHeader()
    data: Dict[str, Any] = {}


class BaseRPCServer(BaseEndpoint):
    """BaseRPCServer.

    Base class for RPC server implementations.
    Provides infrastructure for handling RPC requests using a thread pool.
    """

    @classmethod
    def logger(cls) -> logging.Logger:
        global rpc_logger
        if rpc_logger is None:
            rpc_logger = logging.getLogger(__name__)
        return rpc_logger

    def __init__(
        self,
        base_uri: str = "",
        svc_map: dict = {},
        workers: int = 4,
        *args,
        **kwargs,
    ):
        """__init__.
        Initializes a BaseRPCService instance with the provided configuration.

        Args:
            base_uri (str): The base URI for the RPC service.
            svc_map (dict): A mapping of service names to their corresponding RPC service implementations.
            workers (int): The number of worker threads to use for the RPC service.

        """

        super().__init__(*args, **kwargs)
        self._base_uri: str = base_uri
        self._svc_map: Dict[str, Any] = svc_map
        self._max_workers: int = workers
        self._gen_random_id = gen_random_id

        # Use shared I/O pool by default (reduces thread count)
        use_shared = kwargs.get("use_shared_pool", True)
        if use_shared:
            self._executor: ThreadPoolExecutor = get_io_pool()
            self._owns_executor = False
        else:
            self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
                max_workers=self._max_workers
            )
            self._owns_executor = True

        self._main_thread = None
        self._t_stop_event: threading.Event = threading.Event()
        self._comm_obj: CommRPCMessage = CommRPCMessage()

    def _validate_rpc_req_msg(self, msg: CommRPCMessage) -> bool:
        """_validate_rpc_req_msg.
        Validates the RPC request message by checking if the message header is present and the reply_to field is not empty or None.

        Args:
            msg (CommRPCMessage): The RPC request message to validate.

        Returns:
            bool: True if the RPC request message is valid, False otherwise.
        """

        if msg.header is None:
            return False
        if msg.header.reply_to in ("", None):
            return False
        return True

    def register_endpoint(
        self, uri: str, callback: Callable, msg_type: Optional[Type[RPCMessage]] = None
    ) -> None:
        self._svc_map[uri] = (callback, msg_type)

    def run_forever(self) -> None:
        self._t_stop_event.clear()
        assert self._transport is not None
        self._transport.start()
        _start_endpoints = getattr(self, "start_endpoints", None)
        if _start_endpoints is not None:
            _start_endpoints()
        while not self._t_stop_event.is_set():
            time.sleep(self._LOOP_INTERVAL)
        self.log.debug("Stop event caught in thread")
        self._transport.stop()

    def run(self, wait: bool = True) -> None:
        """
        Start the subscriber thread in the background without blocking
        the main thread.
        """
        if self._transport is None:
            raise RuntimeError(
                f"Transport not initialized - cannot run {self.__class__.__name__}"
            )
        if not self._transport.is_connected and self._state not in (
            EndpointState.CONNECTED,
            EndpointState.CONNECTING,
        ):
            self._main_thread = threading.Thread(target=self.run_forever)
            self._main_thread.daemon = True
            self._main_thread.start()
            if wait:
                while not self.connected:
                    time.sleep(self._LOOP_INTERVAL)
            self._state = EndpointState.CONNECTED
        else:
            self.log.warning("Transport already connected - Skipping")

    def stop(self, wait: bool = True) -> None:
        if self._t_stop_event:
            self._t_stop_event.set()
        if self._transport is not None:
            self._transport.stop()
        if self._main_thread:
            self._main_thread.join(timeout=1)


class BaseRPCService(BaseEndpoint):
    """ΒaseRPCService.
    Implements a base class for an RPC service that can be run in the background.

    The `BaseRPCService` class provides a foundation for implementing RPC services that can be run in the background.
    It includes functionality for managing worker threads, serializing and deserializing RPC messages,
    and handling incoming RPC requests.

    Subclasses of `BaseRPCService` must implement the `run_forever()` method,
    which is responsible for the main loop of the RPC service.
    The `run()` method starts the RPC service in a background thread,
    and the `stop()` method stops the RPC service.
    """

    @classmethod
    def logger(cls) -> logging.Logger:
        global rpc_logger
        if rpc_logger is None:
            rpc_logger = logging.getLogger(__name__)
        return rpc_logger

    def __init__(
        self,
        rpc_name: str,
        msg_type: Optional[Type[RPCMessage]] = None,
        on_request: Optional[Callable] = None,
        workers: int = 5,
        *args: Any,
        **kwargs: Any,
    ):
        """__init__.
        Initializes a new instance of the `BaseRPCService` class.

        Args:
            rpc_name (str): The name of the RPC service.
            msg_type (RPCMessage, optional): The type of RPC message to use.
            on_request (Callable, optional): A callback function to handle incoming RPC requests.
            workers (int, optional): The maximum number of worker threads to use. Defaults to 5.
            *args: Additional positional arguments to pass to the base class constructor.
            **kwargs: Additional keyword arguments to pass to the base class constructor.

        """

        super().__init__(*args, **kwargs)
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self.on_request = on_request
        self._gen_random_id = gen_random_id
        self._max_workers = workers

        # Use shared I/O pool by default
        use_shared = kwargs.get("use_shared_pool", True)
        if use_shared:
            self._executor = get_io_pool()
            self._owns_executor = False
        else:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
            self._owns_executor = True

        self._main_thread = None
        self._t_stop_event = threading.Event()
        self._comm_obj = CommRPCMessage()

    def _serialize_data(self, payload: Dict[str, Any]) -> str:
        """
        Serializes the given payload dictionary to a string using the configured serializer.

        Args:
            payload (Dict[str, Any]): The dictionary to serialize.

        Returns:
            str: The serialized payload.
        """
        assert self._serializer is not None
        return self._serializer.serialize(payload)

    def _serialize_response(self, message: RPCMessage.Response) -> str:
        """
        Serializes an RPC response message to a string.

        Args:
            message (RPCMessage.Response): The RPC response message to serialize.

        Returns:
            str: The serialized RPC response message.
        """

        return self._serialize_data(message.model_dump())

    def _validate_rpc_req_msg(self, msg: CommRPCMessage) -> bool:
        """_validate_rpc_req_msg.
        Validates the RPC request message by checking if the message header is present and the reply_to field is not empty or None.

        Args:
            msg (CommRPCMessage): The RPC request message to validate.

        Returns:
            bool: True if the RPC request message is valid, False otherwise.
        """

        if msg.header is None:
            return False
        if msg.header.reply_to in ("", None):
            return False
        return True

    def _unpack_comm_msg(self, payload: Any, uri: Optional[str] = None) -> Any:
        """
        Unpack the communication message.

        Args:
            payload (Any): The payload to unpack.
            uri (str, optional): The URI associated with the message.

        Returns:
            Tuple[CommRPCMessage, str]: The unpacked message and URI.
        """
        try:
            assert self._serializer is not None
            _payload = self._serializer.deserialize(payload)
            _data = _payload["data"]
            _header = _payload["header"]
            _req_msg = CommRPCMessage(header=CommRPCHeader(**_header), data=_data)
            if not self._validate_rpc_req_msg(_req_msg):
                raise ValueError("Request Message is invalid!")
        except Exception as e:
            raise ValueError(str(e))
        return _req_msg, uri

    def run_forever(self):
        """run_forever.
        Run the RPC service in background and blocks the main thread.
        """
        raise NotImplementedError()

    def run(self, wait: bool = True) -> None:
        """
        Start the subscriber thread in the background without blocking
        the main thread.
        """
        if self._transport is None:
            raise RuntimeError(
                f"Transport not initialized - cannot run {self.__class__.__name__}"
            )
        if not self._transport.is_connected and self._state not in (
            EndpointState.CONNECTED,
            EndpointState.CONNECTING,
        ):
            self._main_thread = threading.Thread(target=self.run_forever)
            self._main_thread.daemon = True
            self._main_thread.start()

            if wait:
                while not self.connected:
                    time.sleep(self._LOOP_INTERVAL)

            self._state = EndpointState.CONNECTED
        else:
            self.log.warning("Transport already connected - Skipping")

    def stop(self, wait: bool = True) -> None:
        """
        Stop the RPC service and the main thread.

        This method sets the `_t_stop_event` flag, which is used to signal the main thread to stop running. It then calls the `stop()` method of the parent class to perform any additional cleanup or shutdown logic.
        """
        if self._t_stop_event:
            self._t_stop_event.set()
        super().stop(wait=wait)
        if self._executor:
            self._executor.shutdown(wait=wait, cancel_futures=True)


class BaseRPCClient(BaseEndpoint):
    """RPCClient Base class.
    Inherit to implement transport-specific RPCClient.
    """

    @classmethod
    def logger(cls) -> logging.Logger:
        global rpc_logger
        if rpc_logger is None:
            rpc_logger = logging.getLogger(__name__)
        return rpc_logger

    def __init__(
        self,
        rpc_name: str,
        msg_type: Optional[Type[RPCMessage]] = None,
        workers: int = 5,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initializes a new instance of the `BaseRPCClient` class.

        Args:
            rpc_name (str): The name of the RPC service.
            msg_type (RPCMessage): The type of RPC message to use.
            workers (int): The number of worker threads to use for asynchronous RPC calls.
            *args: Additional arguments to pass to the parent class constructor.
            **kwargs: Additional keyword arguments to pass to the parent class constructor.

        Attributes:
            _rpc_name (str): The name of the RPC service.
            _msg_type (RPCMessage): The type of RPC message to use.
            _gen_random_id (callable): A function to generate a random ID for RPC messages.
            _max_workers (int): The maximum number of worker threads to use for asynchronous RPC calls.
            _executor (ThreadPoolExecutor): The thread pool executor used for asynchronous RPC calls.
            _comm_obj (CommRPCMessage): An instance of the `CommRPCMessage` class.
        """

        super().__init__(*args, **kwargs)
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self._gen_random_id = gen_random_id
        self._max_workers = workers

        # Use shared I/O pool by default
        use_shared = kwargs.get("use_shared_pool", True)
        if use_shared:
            self._executor = get_io_pool()
            self._owns_executor = False
        else:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
            self._owns_executor = True

        self._comm_obj = CommRPCMessage()

    def call(
        self, msg: RPCMessage.Request, timeout: float = 30.0
    ) -> RPCMessage.Response:
        """call.
        Synchronous RPC Call.

        Args:
            msg (RPCMessage.Request): msg
            timeout (float): timeout

        Returns:
            RPCMessage.Response:
        """
        raise NotImplementedError()

    def call_async(
        self,
        msg: RPCMessage.Request,
        timeout: float = 30.0,
        on_response: Optional[Callable] = None,
    ) -> Future:
        """call_async.
        Asynchronously call an RPC method and return a Future object.

        Args:
            msg (RPCMessage.Request): The RPC request message.
            timeout (float): The timeout for the RPC call in seconds.
            on_response (callable): An optional callback function to be called when the RPC response is received.

        Returns:
            Future: A Future object representing the asynchronous RPC call.
        """

        _future = self._executor.submit(self.call, msg, timeout)
        if on_response is not None:
            _future.add_done_callback(partial(self._done_callback, on_response))
        return _future

    def _done_callback(self, on_response: Callable, _future: Future) -> Any:
        """_done_callback.
        Handles the completion of an asynchronous RPC call.

        This function is used as a callback for the Future object returned by `call_async()`. It checks the status of the Future and, if successful, calls the provided `on_response` callback with the result.

        Args:
            on_response (callable): A callback function to be called with the RPC response.
            _future (Future): The Future object representing the asynchronous RPC call.
        """

        if _future.cancelled():
            pass
            # TODO: Implement Calcellation logic
        elif _future.done():
            error = _future.exception()
            if error:
                pass
                # TODO: Implement Exception logic
            else:
                result = _future.result()
                on_response(result)
                return result

    def _serialize_data(self, payload: Dict[str, Any]) -> str:
        """
        Serialize the provided payload dictionary into a string representation.

        Args:
            payload (Dict[str, Any]): The dictionary to be serialized.

        Returns:
            str: The serialized representation of the payload.
        """

        assert self._serializer is not None
        return self._serializer.serialize(payload)

    def _serialize_request(self, message: RPCMessage.Request) -> str:
        """
        Serialize the provided RPC request message into a string representation.

        Args:
            message (RPCMessage.Request): The RPC request message to be serialized.

        Returns:
            str: The serialized representation of the RPC request message.
        """

        return self._serialize_data(message.model_dump())

    def _prepare_request(
        self, data: Dict[str, Any], reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare the RPC request message.

        Args:
            data (Dict[str, Any]): The data to include in the request.
            reply_to (str, optional): The reply-to address. If None, a random ID is generated.

        Returns:
            Dict[str, Any]: The prepared request message as a dictionary.
        """
        self._comm_obj.header.timestamp = gen_timestamp()
        if reply_to:
            self._comm_obj.header.reply_to = reply_to
        else:
            self._comm_obj.header.reply_to = self._gen_queue_name()
        self._comm_obj.data = data
        return self._comm_obj.model_dump()

    def _unpack_comm_msg(self, payload: Any, uri: Optional[str] = None) -> Any:
        """
        Unpack the communication message.

        Args:
            payload (Any): The payload to unpack.
            uri (str, optional): The URI associated with the message.

        Returns:
            Tuple[Any, Any, str]: The unpacked data, header, and URI.
        """
        assert self._serializer is not None
        _payload = self._serializer.deserialize(payload)
        _data = _payload["data"]
        _header = _payload["header"]
        return _data, _header, uri

    def _prepare_call_data(self, msg: RPCMessage.Request) -> Dict[str, Any]:
        if self._msg_type is None and isinstance(msg, dict):
            return msg
        elif self._msg_type is not None and isinstance(msg, self._msg_type.Request):
            return msg.model_dump()
        else:
            raise ValueError("Invalid message type passed to RPC call")

    def _gen_queue_name(self):
        return f"rpc-{self._gen_random_id()}"
