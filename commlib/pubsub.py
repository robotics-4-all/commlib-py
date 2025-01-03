import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Optional

from commlib.endpoints import BaseEndpoint, EndpointState
from commlib.msg import PubSubMessage
from commlib.utils import gen_random_id

pubsub_logger = None


TOPIC_REGEX = r'^[a-zA-Z0-9\/\.\-\_]+$'
TOPIC_PATTERN_REGEX = r'^[a-zA-Z0-9\/\*\.\-\_]+$'


def validate_pubsub_topic(topic: str) -> None:
    """
    Validates a given pub/sub topic.

    This method checks if the provided topic is valid based on predefined rules.
    A topic is considered invalid if it is one of the following: '.', '*', '-', '_', None,
    or if it does not match the regular expression defined by TOPIC_PATTERN_REGEX.

    Args:
        topic (str): The pub/sub topic to be validated.

    Raises:
        ValueError: If the topic is invalid.
    """
    if topic is None:
        return
    if topic in ('.', '*', '-', '_', "", " ") or not re.match(TOPIC_PATTERN_REGEX, topic):
        raise ValueError(f"Invalid topic: {topic}")

def validate_pubsub_topic_strict(topic: str) -> None:
    """
    Validate a Pub/Sub topic name.

    This method checks if the provided topic name is valid according to the
    specified rules. A topic name is considered invalid if it is one of the
    following: '.', '*', '-', '_', or None, or if it does not match the
    regular expression defined by TOPIC_REGEX.

    Args:
        topic (str): The topic name to validate.

    Raises:
        ValueError: If the topic name is invalid.
    """
    if topic is None:
        return
    if topic in ('.', '-', '_', "", " ") or not re.match(TOPIC_REGEX, topic):
        raise ValueError(f"Invalid topic: {topic}")


class BasePublisher(BaseEndpoint):
    """BasePublisher."""

    @classmethod
    def logger(cls) -> logging.Logger:
        global pubsub_logger
        if pubsub_logger is None:
            pubsub_logger = logging.getLogger(__name__)
        return pubsub_logger

    def __init__(self, topic: str, msg_type: PubSubMessage = None,
                 *args, **kwargs):
        """__init__.
        Initializes a new instance of the `BaseSubscriber` class.

        Args:
            topic (str): The topic to subscribe to.
            msg_type (PubSubMessage, optional): The type of message to expect for this subscription.
            *args: Additional positional arguments to pass to the base class constructor.
            **kwargs: Additional keyword arguments to pass to the base class constructor.
        """

        super().__init__(*args, **kwargs)
        self._topic: str = topic
        self._msg_type: PubSubMessage = msg_type
        self._gen_random_id: str = gen_random_id

        validate_pubsub_topic_strict(self._topic)

    @property
    def topic(self) -> str:
        """topic"""
        return self._topic

    def publish(self, msg: PubSubMessage) -> None:
        raise NotImplementedError()


class BaseSubscriber(BaseEndpoint):
    """BaseSubscriber."""
    LOOP_INTERVAL = 0.001

    @classmethod
    def logger(cls) -> logging.Logger:
        global pubsub_logger
        if pubsub_logger is None:
            pubsub_logger = logging.getLogger(__name__)
        return pubsub_logger

    def __init__(self, topic: str, msg_type: Optional[PubSubMessage] = None,
                 on_message: Optional[Callable] = None, workers: int = 2,
                 *args, **kwargs):
        """__init__.
        Initializes a new instance of the `BaseSubscriber` class.

        Args:
            topic (str): The topic to subscribe to.
            msg_type (Optional[PubSubMessage]): The type of message to expect for this subscription.
            on_message (Optional[Callable]): A callback function to be called when a message is received.
            *args: Additional positional arguments to pass to the base class constructor.
            **kwargs: Additional keyword arguments to pass to the base class constructor.
        """

        super().__init__(*args, **kwargs)
        self._topic = topic
        self._msg_type = msg_type
        self.onmessage = on_message
        self._gen_random_id = gen_random_id
        self._workers = workers
        self._executor = ThreadPoolExecutor(max_workers=workers)
        self._main_thread = None
        self._t_stop_event = None

        validate_pubsub_topic(self._topic)

    @property
    def topic(self) -> str:
        """topic"""
        return self._topic

    @property
    def executor(self) -> ThreadPoolExecutor:
        """topic"""
        return self._executor

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
        """
        Start the subscriber thread in the background without blocking
        the main thread.
        """
        if self._transport is None:
            raise RuntimeError(
                f"Transport not initialized - cannot run {self.__class__.__name__}")
        if not self._transport.is_connected and \
            self._state not in (EndpointState.CONNECTED,
                                EndpointState.CONNECTING):
            self._main_thread = threading.Thread(target=self.run_forever)
            self._main_thread.daemon = True
            self._t_stop_event = threading.Event()
            self._main_thread.start()
            self._state = EndpointState.CONNECTED
        else:
            self.logger().warning("Transport already connected - Skipping")

    def stop(self) -> None:
        """
        Stops the pub/sub service by setting the stop event and calling the parent class's stop method.

        If the stop event (`_t_stop_event`) is not None, it sets the event to signal that the service should stop.
        Then, it calls the `stop` method of the superclass to perform any additional stopping procedures.
        """
        if self._t_stop_event is not None:
            self._t_stop_event.set()
        super().stop()
