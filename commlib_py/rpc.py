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
from .logger import create_logger


class AbstractRPCServer(object):
    def __init__(self, rpc_name, msg_type=None, logger=None, debug=True,
                 on_request=None, workers=2, serializer=None):
        self._rpc_name = rpc_name
        self._num_workers = workers
        self._debug = debug
        self.on_request = on_request

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer()

        self._logger = create_logger(self.__class__.__name__) if \
            logger is None else logger

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None

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
        self._t_stop_event.set()
