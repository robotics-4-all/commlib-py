from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict, Any, Callable

from .serializer import Serializer, JSONSerializer
from .logger import Logger
from .utils import gen_random_id
from .msg import PubSubMessage
from .compression import CompressionType


class BasePublisher(object):
    """BasePublisher.
    """

    def __init__(self, topic: str = None,
                 msg_type: PubSubMessage = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer: Serializer = JSONSerializer,
                 compression: CompressionType = CompressionType.NO_COMPRESSION):
        """__init__.

        Args:
            topic (str): topic
            msg_type (PubSubMessage): msg_type
            logger (Logger): logger
            debug (bool): debug
            serializer:
        """
        if topic is None:
            raise ValueError('Topic Name not defined')

        self._debug = debug
        self._topic = topic
        self._msg_type = msg_type
        self._serializer = serializer
        self._compression = compression

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        self._gen_random_id = gen_random_id

        self.logger.debug(f'Initiated Publisher <{self._topic}>')

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def logger(self) -> Logger:
        return self._logger

    def publish(self, msg: PubSubMessage) -> None:
        """publish.

        Args:
            msg (PubSubMessage): msg

        Returns:
            None:
        """
        raise NotImplementedError()


class BaseSubscriber(object):
    """BaseSubscriber.
    """

    def __init__(self, topic: str = None,
                 msg_type: PubSubMessage = None,
                 on_message: Callable = None,
                 logger: Logger = None,
                 debug: bool = True,
                 serializer: Serializer = JSONSerializer,
                 compression: CompressionType = CompressionType.NO_COMPRESSION):
        """__init__.

        Args:
            topic (str): topic
            msg_type (PubSubMessage): msg_type
            on_message (callable): on_message
            logger (Logger): logger
            debug (bool): debug
            serializer:
        """
        if topic is None:
            raise ValueError('Topic name cannot be None')
        self._debug = debug
        self._topic = topic
        self._msg_type = msg_type
        self._compression = compression
        self._serializer = serializer
        self.onmessage = on_message

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
        """run_forever.
        Start subscriber thread in background and blocks main thread.

        Args:

        Returns:
            None:
        """
        raise NotImplementedError()

    def on_message(self, data: Dict) -> None:
        """on_message.

        Args:
            data (Dict): data

        Returns:
            None:
        """
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
