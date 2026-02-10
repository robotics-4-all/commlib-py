"""Mock transport for testing.

Provides a mock transport implementation for unit testing and benchmarking
without actual message brokers. Uses in-memory message passing.
"""

import threading
from typing import Any, Callable, Dict, Optional
from commlib.connection import BaseConnectionParameters
from commlib.endpoints import EndpointState
from commlib.msg import PubSubMessage, RPCMessage
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.rpc import BaseRPCClient, BaseRPCService

from commlib.transports.base_transport import BaseTransport


# Global in-memory message bus for mock transport
_MOCK_MESSAGE_BUS: Dict[str, list] = {}
_MOCK_SUBSCRIBERS: Dict[str, list] = {}
_MOCK_BUS_LOCK = threading.Lock()


class ConnectionParameters(BaseConnectionParameters):
    """Mock connection parameters (no actual connection needed)."""

    host: str = "mock"
    port: int = 0


class MockTransport(BaseTransport):
    """Mock transport with in-memory message passing."""

    def __init__(
        self,
        conn_params: Optional[BaseConnectionParameters] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(conn_params, *args, **kwargs)

    def start(self):
        """Start the mock transport."""
        self._set_connected(True)

    def stop(self):
        """Stop the mock transport."""
        self._set_connected(False)

    def connect(self):
        """Connect to mock transport."""
        self.start()

    def disconnect(self):
        """Disconnect from mock transport."""
        self.stop()

    def publish(self, topic: str, message: Any):
        """Publish message to in-memory bus.

        Args:
            topic: Topic to publish to
            message: Message to publish
        """
        with _MOCK_BUS_LOCK:
            if topic not in _MOCK_MESSAGE_BUS:
                _MOCK_MESSAGE_BUS[topic] = []
            _MOCK_MESSAGE_BUS[topic].append(message)

            # Notify subscribers
            if topic in _MOCK_SUBSCRIBERS:
                for callback in _MOCK_SUBSCRIBERS[topic]:
                    try:
                        callback(message)
                    except Exception:
                        pass  # Ignore callback errors

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic on in-memory bus.

        Args:
            topic: Topic to subscribe to
            callback: Callback function for messages
        """
        with _MOCK_BUS_LOCK:
            if topic not in _MOCK_SUBSCRIBERS:
                _MOCK_SUBSCRIBERS[topic] = []
            _MOCK_SUBSCRIBERS[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Optional[Callable] = None):
        """Unsubscribe from topic.

        Args:
            topic: Topic to unsubscribe from
            callback: Specific callback to remove (or None for all)
        """
        with _MOCK_BUS_LOCK:
            if topic in _MOCK_SUBSCRIBERS:
                if callback is None:
                    _MOCK_SUBSCRIBERS[topic].clear()
                elif callback in _MOCK_SUBSCRIBERS[topic]:
                    _MOCK_SUBSCRIBERS[topic].remove(callback)


class Publisher(BasePublisher):
    """Mock publisher with in-memory message passing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport(self._conn_params)

    def publish(self, msg: PubSubMessage):
        """Publish message to mock transport.

        Args:
            msg: Message to publish
        """
        if self._transport is None:
            return
        if not self._transport.is_connected:
            self._transport.start()

        # Serialize message
        if isinstance(msg, PubSubMessage):
            data = msg.model_dump()
        else:
            data = msg

        # Publish to in-memory bus
        self._transport.publish(self._topic, data)


class Subscriber(BaseSubscriber):
    """Mock subscriber with in-memory message passing."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport(self._conn_params)
        self._callback_registered = False

    def run(self, wait: bool = True) -> None:
        """Start the subscriber.

        Args:
            wait: Not used in mock (kept for API compatibility)
        """
        if self._transport is None:
            raise RuntimeError(
                f"Transport not initialized - cannot run {self.__class__.__name__}"
            )

        if not self._transport.is_connected:
            self._transport.start()

        # Register callback with mock bus
        if not self._callback_registered and self.onmessage is not None:
            _onmessage = self.onmessage
            _msg_type = self._msg_type

            def wrapper(data: Any) -> None:
                if _msg_type is not None:
                    try:
                        msg = _msg_type(**data)
                        _onmessage(msg)
                    except Exception:
                        pass  # Ignore errors
                else:
                    _onmessage(data)

            self._transport.subscribe(self._topic, wrapper)
            self._callback_registered = True

        self._state = EndpointState.CONNECTED

    def stop(self, wait: bool = True) -> None:
        """Stop the subscriber.

        Args:
            wait: Not used in mock (kept for API compatibility)
        """
        if self._t_stop_event is not None:
            self._t_stop_event.set()

        if self._transport is not None and self._transport.is_connected:
            self._transport.stop()

        self._state = EndpointState.DISCONNECTED


class RPCService(BaseRPCService):
    """Mock RPC service."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport(self._conn_params)

    def run(self, wait: bool = True) -> None:
        """Start the RPC service.

        Args:
            wait: Not used in mock (kept for API compatibility)
        """
        if self._transport is None:
            raise RuntimeError(
                f"Transport not initialized - cannot run {self.__class__.__name__}"
            )

        if not self._transport.is_connected:
            self._transport.start()
            self._state = EndpointState.CONNECTED

    def stop(self, wait: bool = True) -> None:
        """Stop the RPC service.

        Args:
            wait: Not used in mock (kept for API compatibility)
        """
        if self._t_stop_event is not None:
            self._t_stop_event.set()

        if self._transport is not None and self._transport.is_connected:
            self._transport.stop()

        self._state = EndpointState.DISCONNECTED


class RPCClient(BaseRPCClient):
    """Mock RPC client."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport(self._conn_params)

    def call(
        self, msg: RPCMessage.Request, timeout: float = 30.0
    ) -> RPCMessage.Response:
        """Make RPC call (mock implementation).

        Args:
            msg: Request message
            timeout: Timeout in seconds (not used in mock)

        Returns:
            Response message (empty for mock)
        """
        if self._transport is None:
            raise RuntimeError("Transport not initialized")
        if not self._transport.is_connected:
            self._transport.start()

        # Return empty response for mock
        if self._msg_type is not None:
            return self._msg_type.Response()
        return RPCMessage.Response()


def clear_mock_bus():
    """Clear the mock message bus (useful for testing)."""
    global _MOCK_MESSAGE_BUS, _MOCK_SUBSCRIBERS
    with _MOCK_BUS_LOCK:
        _MOCK_MESSAGE_BUS.clear()
        _MOCK_SUBSCRIBERS.clear()
