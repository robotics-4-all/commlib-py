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


class BasePublisher(object):
    def __init__(self, topic=None, msg_type=None, logger=None,
                 debug=True, serializer=None):
        self._debug = debug
        self._topic = topic

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        assert isinstance(self._logger, Logger)
        self.logger.info('Created Publisher: <{}>'.format(self._topic))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def publish(self, payload):
        raise NotImplementedError()


class BaseSubscriber(object):
    def __init__(self, topic=None, msg_type=None, on_message=None,
                 logger=None, debug=True, serializer=None):
        self._debug = debug
        self._topic = topic

        self._onmessage = on_message

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        assert isinstance(self._logger, Logger)

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None
        self.logger.info('Created Subscriber: <{}>'.format(self._topic))

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
        """Execute subscriber in a separate thread."""
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self):
        self._t_stop_event.set()

