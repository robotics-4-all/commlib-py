from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
from concurrent import futures
from functools import partial

from .serializer import JSONSerializer
from .logger import Logger
from .utils import gen_random_id
from .msg import RPCMessage


class BaseRPCService(object):
    """RPCService Base class.
    Inherit to implement transport-specific RPCService.

    Args:
        - rpc_name (str)
    """

    def __init__(self, rpc_name: str = None,
                 msg_type: RPCMessage = None,
                 on_request: callable = None,
                 logger: Logger = None,
                 debug: bool = True,
                 workers: int = 2,
                 serializer=None):
        if rpc_name is None:
            raise ValueError('rpc_name cannot be None')
        if msg_type is None:
            raise ValueError('msg_type cannot be None')
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self._num_workers = workers
        self._debug = debug
        self.on_request = on_request

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__, self._debug) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None
        self.logger.debug('Created RPC Service <{}>'.format(self._rpc_name))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def run_forever(self):
        raise NotImplementedError()

    def run(self):
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self):
        if self._t_stop_event is not None:
            self._t_stop_event.set()


class BaseRPCClient(object):
    """RPCClient Base class.
    Inherit to implement transport-specific RPCClient.

    Args:
        rpc_name (str): The name of the RPC.
        logger (Logger): Logger instance.
        debug (bool): Debug-mode.
        serializer (): Serializer class.
    """

    def __init__(self,
                 rpc_name: str = None,
                 msg_type: RPCMessage = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer=None,
                 max_workers=5):
        if rpc_name is None:
            raise ValueError('rpc_name cannot be None')
        if msg_type is None:
            raise ValueError('msg_type cannot be None')
        self._rpc_name = rpc_name
        self._msg_type = msg_type
        self._debug = debug

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__, debug=self._debug) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        self._executor = futures.ThreadPoolExecutor(max_workers=max_workers)

        self.logger.debug('Created RPC Client: <{}>'.format(self._rpc_name))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def call(self, msg: RPCMessage.Request, timeout: float = 30):
        raise NotImplementedError()

    def call_async(self, msg: RPCMessage.Request,
                   timeout: float = 30.0,
                   on_response: callable = None):
        _future = self._executor.submit(self.call, msg, timeout)
        if on_response is not None:
            _future.add_done_callback(
                partial(self._done_callback, on_response)
            )
        return _future

    def _done_callback(self, on_response, _future):
        if _future.cancelled():
            self.logger.debug('Future object was cancelled')
            ## TODO: Implement Calcellation logic
        elif _future.done():
            error = _future.exception()
            if error:
                self.logger.debug('Future threw exception')
                ## TODO: Implement Exception logic
            else:
                result = _future.result()
                on_response(result)
                return result
