import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel

from commlib.connection import BaseConnectionParameters
from commlib.endpoints import BaseEndpoint
from commlib.msg import RPCMessage
from commlib.serializer import JSONSerializer, Serializer
from commlib.utils import gen_random_id, gen_timestamp

rpc_logger = None


class CommRPCHeader(BaseModel):
    reply_to: str = ''
    timestamp: Optional[int] = gen_timestamp()


class CommRPCMessage(BaseModel):
    header: CommRPCHeader = CommRPCHeader()
    data: Dict[str, Any] = {}


class BaseRPCServer(BaseEndpoint):
    @classmethod
    def logger(cls) -> logging.Logger:
        global rpc_logger
        if rpc_logger is None:
            rpc_logger = logging.getLogger(__name__)
        return rpc_logger

    def __init__(self,
                 base_uri: str = '',
                 svc_map: dict = {},
                 workers: int = 2,
                 *args, **kwargs):
        """__init__.

        Args:
            workers (int): Number of workers to start listening
        """
        super().__init__(*args, **kwargs)
        self._base_uri = base_uri
        self._svc_map = svc_map
        self._max_workers = workers
        self._gen_random_id = gen_random_id
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._main_thread = None
        self._t_stop_event = None
        self._comm_obj = CommRPCMessage()

    def run_forever(self):
        """run_forever.
        Run the RPC service in background and blocks the main thread.
        """
        raise NotImplementedError()

    def run(self):
        """run.
        Run the RPC service in background.
        """
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self) -> None:
        self._transport.stop()


class BaseRPCService(BaseEndpoint):
    """RPCService Base class.
    Inherit to implement transport-specific RPCService.

    Args:
        - rpc_name (str)
    """
    @classmethod
    def logger(cls) -> logging.Logger:
        global rpc_logger
        if rpc_logger is None:
            rpc_logger = logging.getLogger(__name__)
        return rpc_logger

    def __init__(self,
                 rpc_name: str,
                 msg_type: RPCMessage = None,
                 on_request: Callable = None,
                 workers: int = 5,
                 *args, **kwargs):
        """__init__.

        Args:
            rpc_name (str): rpc_name
            msg_type (RPCMessage): msg_type
            on_request (callable): on_request
            workers (int): workers
        """
        super().__init__(*args, **kwargs)
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self.on_request = on_request
        self._gen_random_id = gen_random_id
        self._max_workers = workers
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._main_thread = None
        self._t_stop_event = None
        self._comm_obj = CommRPCMessage()

    def _serialize_data(self, payload: Dict[str, Any]) -> str:
        return self._serializer.serialize(payload)

    def _serialize_response(self, message: RPCMessage.Response) -> str:
        return self._serialize_data(message.dict())

    def _validate_rpc_req_msg(self, msg: CommRPCMessage) -> bool:
        if msg.header is None:
            return False
        elif msg.header.reply_to in ('', None):
            return False
        return True

    def run_forever(self):
        """run_forever.
        Run the RPC service in background and blocks the main thread.
        """
        raise NotImplementedError()

    def run(self):
        """run.
        Run the RPC service in background.
        """
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self):
        """stop.
        Stop the RPC Service.
        """
        if self._t_stop_event is not None:
            self._t_stop_event.set()
        if self._transport is not None:
            self._transport.stop()

    def __del__(self):
        self.stop()


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

    def __init__(self,
                 rpc_name: str,
                 msg_type: RPCMessage = None,
                 workers: int = 5,
                 *args, **kwargs):
        """__init__.

        Args:
            rpc_name (str): rpc_name
            msg_type (RPCMessage): msg_type
        """
        super().__init__(*args, **kwargs)
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self._gen_random_id = gen_random_id
        self._max_workers = workers
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._comm_obj = CommRPCMessage()

    def call(self, msg: RPCMessage.Request,
             timeout: float = 30.0
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

    def call_async(self, msg: RPCMessage.Request,
                   timeout: float = 30.0,
                   on_response: callable = None):
        """call_async.
        Asynchrouns RPC Call. The on_response callback is fired when result is
        received by the client.

        Args:
            msg (RPCMessage.Request): msg
            timeout (float): timeout
            on_response (callable): on_response
        """
        _future = self._executor.submit(self.call, msg, timeout)
        if on_response is not None:
            _future.add_done_callback(
                partial(self._done_callback, on_response)
            )
        return _future

    def _done_callback(self, on_response: callable, _future):
        if _future.cancelled():
            pass
            ## TODO: Implement Calcellation logic
        elif _future.done():
            error = _future.exception()
            if error:
                pass
                ## TODO: Implement Exception logic
            else:
                result = _future.result()
                on_response(result)
                return result

    def _serialize_data(self, payload: Dict[str, Any]) -> str:
        return self._serializer.serialize(payload)

    def _serialize_request(self, message: RPCMessage.Request) -> str:
        return self._serialize_data(message.dict())

    def run(self):
        if self._transport is not None:
            self._transport.start()

    def stop(self) -> None:
        if self._transport is not None:
            self._transport.stop()

    def __del__(self):
        self.stop()
