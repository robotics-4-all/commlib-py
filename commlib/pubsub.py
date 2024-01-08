import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Optional

from commlib.endpoints import BaseEndpoint
from commlib.msg import PubSubMessage
from commlib.utils import gen_random_id

pubsub_logger = None


class BasePublisher(BaseEndpoint):
    """BasePublisher."""

    @classmethod
    def logger(cls) -> logging.Logger:
        global pubsub_logger
        if pubsub_logger is None:
            pubsub_logger = logging.getLogger(__name__)
        return pubsub_logger

    def __init__(self, topic: str, msg_type: PubSubMessage = None, *args, **kwargs):
        """__init__.

        Args:
            topic (str): topic
            msg_type (PubSubMessage): msg_type
        """
        super().__init__(*args, **kwargs)
        self._topic = topic
        self._msg_type = msg_type
        self._gen_random_id = gen_random_id

    @property
    def topic(self) -> str:
        """topic"""
        return self._topic

    def publish(self, msg: PubSubMessage) -> None:
        """publish.

        Args:
            msg (PubSubMessage): msg

        Returns:
            None:
        """
        raise NotImplementedError()

    def run(self):
        if self._transport is not None:
            self._transport.start()

    def stop(self) -> None:
        if self._transport is not None:
            self._transport.stop()

    def __del__(self):
        self.stop()


class BaseSubscriber(BaseEndpoint):
    """BaseSubscriber."""

    @classmethod
    def logger(cls) -> logging.Logger:
        global pubsub_logger
        if pubsub_logger is None:
            pubsub_logger = logging.getLogger(__name__)
        return pubsub_logger

    def __init__(
        self,
        topic: str,
        msg_type: Optional[PubSubMessage] = None,
        on_message: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        """__init__.

        Args:
            topic (str): topic
            msg_type (PubSubMessage): msg_type
            on_message (callable): on_message
        """
        super().__init__(*args, **kwargs)
        self._topic = topic
        self._msg_type = msg_type
        self.onmessage = on_message
        self._gen_random_id = gen_random_id

        self._executor = ThreadPoolExecutor(max_workers=2)
        self._main_thread = None
        self._t_stop_event = None

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
        """Execute subscriber in a separate thread."""
        self._main_thread = threading.Thread(target=self.run_forever)
        self._main_thread.daemon = True
        self._t_stop_event = threading.Event()
        self._main_thread.start()

    def stop(self) -> None:
        if self._t_stop_event is not None:
            self._t_stop_event.set()
        self._transport.stop()

    def __del__(self):
        self.stop()
