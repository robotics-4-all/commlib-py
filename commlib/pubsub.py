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
from .utils import gen_random_id


class BasePublisher(object):

    def __init__(self, topic: str = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer=None):
        self._debug = debug
        self._topic = topic

        if topic is None:
            raise ValueError('Topic Name not defined')

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        assert isinstance(self._logger, Logger)
        self.logger.debug('Created Publisher: <{}>'.format(self._topic))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def publish(self, payload):
        raise NotImplementedError()


class BaseSubscriber(object):

    def __init__(self,topic: str = None,
                 on_message: callable = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer=None):
        self._debug = debug
        self._topic = topic

        if topic is None:
            raise ValueError()

        self._onmessage = on_message

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        assert isinstance(self._logger, Logger)

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None
        self.logger.debug('Created Subscriber: <{}>'.format(self._topic))

    @property
    def topic(self):
        """topic"""
        return self._topic

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def run_forever(self):
        raise NotImplementedError()

    def run(self):
        """Execute subscriber in a separate thread."""
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self):
        if self._t_stop_event is not None:
            self._t_stop_event.set()
