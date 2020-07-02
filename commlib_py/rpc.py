from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from concurrent.futures import ThreadPoolExecutor
import threading
import time
import uuid
import json
import hashlib

from .serializer import JSONSerializer
from .logger import create_logger


class AbstractRPCServer(object):
    def __init__(self, rpc_name, msg_type=None, logger=None,
                 callback=None, workers=2):
        self._serializer = JSONSerializer()
        self._rpc_name = rpc_name
        self._num_workers = workers
        self._callback = callback

        self.log = create_logger(self._rpc_name)
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def on_request_clb(self, msg):
        raise NotImplementedError()

    def run_forever(self):
        raise NotImplementedError()

    def run(self):
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self):
        self._t_stop_event.set()
