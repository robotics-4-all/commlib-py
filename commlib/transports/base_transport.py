"""Base transport layer abstraction.

Provides abstract base classes for implementing different transport backends.
"""

import logging
import threading
from typing import Any, Optional

transport_logger = None


class BaseTransport:
    """BaseTransport.
    The `BaseTransport` class provides a base implementation for a transport
    layer in the `commlib` library. It defines common properties and methods
    that should be implemented by concrete transport implementations.
    """

    @classmethod
    def logger(cls) -> logging.Logger:
        global transport_logger
        if transport_logger is None:
            transport_logger = logging.getLogger(__name__)
        return transport_logger

    def __init__(self, conn_params: Any = None, debug: bool = False):
        """__init__.
        Initializes a new instance of the `BaseTransport` class.

        Args:
            conn_params (BaseConnectionParameters): The
                connection parameters for the transport.
            debug (bool, optional): Whether to enable debug
                logging for the transport. Defaults to False.
        """

        self._conn_params = conn_params
        self._debug = debug
        self._connected = False
        self._stopped = False

        # Event-driven connection state management (eliminates busy-wait polling)
        self._connected_event = threading.Event()
        self._disconnected_event = threading.Event()
        self._disconnected_event.set()  # Initially disconnected

    @property
    def log(self):
        return self.logger()

    @property
    def debug(self):
        return self._debug

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def _set_connected(self, connected: bool) -> None:
        """Set connection state and trigger events.

        This method updates the connection state and triggers the appropriate
        threading events to wake up waiting threads. This eliminates busy-wait
        polling for connection state changes.

        Args:
            connected: True if connected, False if disconnected
        """
        self._connected = connected
        if connected:
            self._connected_event.set()
            self._disconnected_event.clear()
        else:
            self._connected_event.clear()
            self._disconnected_event.set()

    def wait_connected(self, timeout: float = 10.0) -> bool:
        """Wait for connection to be established (event-driven).

        Replaces busy-wait polling with event-driven waiting.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if connected within timeout, False otherwise
        """
        return self._connected_event.wait(timeout=timeout)

    def wait_disconnected(self, timeout: float = 10.0) -> bool:
        """Wait for disconnection (event-driven).

        Replaces busy-wait polling with event-driven waiting.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if disconnected within timeout, False otherwise
        """
        return self._disconnected_event.wait(timeout=timeout)

    def connect(self) -> Optional[bool]:
        raise NotImplementedError()

    def disconnect(self) -> None:
        raise NotImplementedError()

    def start(self) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def loop_forever(self) -> None:
        raise NotImplementedError()

    # --- Transport method stubs ---
    # These are implemented by concrete transport subclasses.
    # Declared here so pyright can resolve attribute access on BaseTransport.

    def publish(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def subscribe(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def unsubscribe(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def msubscribe(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def push_msg_to_queue(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def wait_for_msg(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def delete_queue(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def create_queue(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def create_exchange(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def exchange_exists(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def queue_exists(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def bind_queue(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def set_channel_qos(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def consume_from_queue(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def start_consuming(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def add_threadsafe_callback(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def detach_amqp_events_thread(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def create_producer(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def create_consumer(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def publish_data(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    @property
    def channel(self) -> Any:
        raise NotImplementedError()
