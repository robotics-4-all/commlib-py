from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from concurrent.futures import ThreadPoolExecutor
import threading
import uuid

from .serializer import JSONSerializer
from .logger import Logger


class BaseRPCServer(object):
    def __init__(self, conn_params, rpc_name, on_request,
                 logger=None, debug=True, workers=2,
                 serializer=None):
        self._rpc_name = rpc_name
        self._num_workers = workers
        self._debug = debug
        self.on_request = on_request

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None
        self.logger.info('Created RPC Server: <{}>'.format(self._rpc_name))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

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
    def __init__(self, rpc_name=None, msg_type=None, logger=None,
                 debug=True, serializer=None):
        if rpc_name is None:
            raise ValueError()
        self._rpc_name = rpc_name
        self._debug = debug

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self.logger.info('Created RPC Client: <{}>'.format(self._rpc_name))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def call(self, data, timeout):
        raise NotImplementedError()
