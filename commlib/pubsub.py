from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
from typing import OrderedDict, Any

from .serializer import JSONSerializer
from .logger import Logger
from .utils import gen_random_id
from .msg import PubSubMessage


class BasePublisher(object):

    def __init__(self, topic: str = None,
                 msg_type: PubSubMessage = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer=None):
        self._debug = debug
        self._topic = topic
        self._msg_type = msg_type

        if topic is None:
            raise ValueError('Topic Name not defined')

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        self.logger.debug('Created Publisher: <{}>'.format(self._topic))

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def logger(self) -> Logger:
        return self._logger

    def publish(self, msg: PubSubMessage) -> None:
        raise NotImplementedError()


class BaseSubscriber(object):

    def __init__(self, topic: str = None,
                 msg_type: PubSubMessage = None,
                 on_message: callable = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer=None):
        self._debug = debug
        self._topic = topic
        self._msg_type = msg_type

        if topic is None:
            raise ValueError('Topic name cannot be None')

        self.onmessage = on_message

        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        self._executor = ThreadPoolExecutor(max_workers=2)

        self._main_thread = None
        self._t_stop_event = None

    @property
    def topic(self) -> str:
        """topic"""
        return self._topic

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def logger(self) -> Logger:
        return self._logger

    def run_forever(self) -> None:
        raise NotImplementedError()

    def on_message(self, data: OrderedDict) -> None:
        raise NotImplementedError()

    def run(self) -> None:
        """Execute subscriber in a separate thread."""
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()
        self.logger.info(f'Started Subscriber: <{self._topic}>')

    def stop(self) -> None:
        if self._t_stop_event is not None:
            self._t_stop_event.set()
