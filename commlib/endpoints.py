"""Communication endpoints and factories.

Provides base endpoint classes and factory functions for creating
endpoint instances with various transport backends.
"""

import logging
from enum import Enum
import time

from commlib.compression import CompressionType
from commlib.connection import BaseConnectionParameters
from commlib.serializer import JSONSerializer, Serializer
from commlib.transports import TransportType
from commlib.transports.base_transport import BaseTransport

e_logger = None


class EndpointState(Enum):
    """
    Enum representing the state of an endpoint.

    Attributes:
        DISCONNECTED (int): The endpoint is disconnected (value 0).
        CONNECTED (int): The endpoint is connected (value 1).
        CONNECTING (int): The endpoint is in the process of connecting (value 2).
        DISCONNECTING (int): The endpoint is in the process of disconnecting (value 3).
    """

    DISCONNECTED = 0
    CONNECTED = 1
    CONNECTING = 2
    DISCONNECTING = 3


class BaseEndpoint:
    """
    Defines the base class for all endpoints in the commlib library.

    The `BaseEndpoint` class provides common functionality for all endpoint types, such as:
    - Logging
    - Serialization
    - Connection parameters
    - Compression

    Subclasses of `BaseEndpoint` should implement the specific functionality for their
    endpoint type, such as RPC, publish/subscribe, etc.
    """

    @classmethod
    def logger(cls) -> logging.Logger:
        global e_logger
        if e_logger is None:
            e_logger = logging.getLogger(__name__)
        return e_logger

    def __init__(
        self,
        debug: bool = False,
        serializer: Serializer = JSONSerializer,
        conn_params: BaseConnectionParameters = None,
        compression: CompressionType = CompressionType.NO_COMPRESSION,
    ):
        """__init__.
        Initializes a new instance of the `BaseEndpoint` class.

        Args:
            debug (bool, optional): A flag indicating whether debug mode is enabled. Defaults to `False`.
            serializer (Serializer, optional): The serializer to use for data serialization. Defaults to `JSONSerializer`.
            conn_params (BaseConnectionParameters, optional): The connection parameters to use for the transport. Defaults to `None`.
            compression (CompressionType, optional): The compression type to use for the transport. Defaults to `CompressionType.NO_COMPRESSION`.
        """

        self._debug = debug
        self._serializer = serializer
        self._compression = compression
        self._conn_params = conn_params
        self._state = EndpointState.DISCONNECTED
        self._transport: BaseTransport = None

    @property
    def connected(self):
        return self._transport.is_connected

    @property
    def log(self):
        return self.logger()

    @property
    def debug(self):
        return self._debug

    def run(self, wait: bool = True) -> None:
        """
        Starts the subscriber and connects to the transport if it is not already connected.

        If the transport is not initialized, raises a `RuntimeError`.

        If the transport is not connected and the subscriber is not in the `CONNECTED` or `CONNECTING` state, it starts the transport.

        Finally, it sets the subscriber state to `CONNECTED`.
        """
        if self._transport is None:
            raise RuntimeError(f"Transport not initialized - cannot run {self.__class__.__name__}")
        if not self.connected:
            self._transport.start()
            if wait:
                while not self.connected:
                    time.sleep(0.001)
            self._state = EndpointState.CONNECTED
        else:
            self.log.warning("Transport already connected - Skipping")

    def stop(self, wait: bool = True) -> None:
        """
        Stops the subscriber and disconnects from the transport if it is connected.

        If the transport is not initialized, raises a `RuntimeError`.

        If the transport is connected and the subscriber is not in the `DISCONNECTED` or `DISCONNECTING` state, it stops the transport.
        """
        if self._transport is None:
            raise RuntimeError(f"Transport not initialized - cannot stop {self.__class__.__name__}")
        if self._transport.is_connected:
            self._transport.stop()
            if wait:
                while self.connected:
                    time.sleep(0.001)
            self._state = EndpointState.DISCONNECTED
        else:
            self.log.warning(
                "Transport is not connected - cannot stop %s",
                self.__class__.__name__,
            )


class EndpointType(Enum):
    """
    Enum representing different types of endpoints in a communication library.

    Attributes:
        RPCService (int): Represents a Remote Procedure Call (RPC) service endpoint.
        RPCClient (int): Represents a Remote Procedure Call (RPC) client endpoint.
        Publisher (int): Represents a publisher endpoint for publishing messages.
        Subscriber (int): Represents a subscriber endpoint for receiving messages.
        ActionService (int): Represents an action service endpoint.
        ActionClient (int): Represents an action client endpoint.
        MPublisher (int): Represents a multi-publisher endpoint.
        PSubscriber (int): Represents a persistent subscriber endpoint.
    """

    RPCService = 1
    RPCClient = 2
    Publisher = 3
    Subscriber = 4
    ActionService = 5
    ActionClient = 6
    MPublisher = 7
    PSubscriber = 8


def endpoint_factory(etype: EndpointType, etransport: TransportType):
    """
    Factory function to create endpoint instances based on the specified endpoint type and transport type.

    Args:
        etype (EndpointType): The type of the endpoint to create.
            Possible values include:
            - EndpointType.RPCService
            - EndpointType.RPCClient
            - EndpointType.Publisher
            - EndpointType.Subscriber
            - EndpointType.ActionService
            - EndpointType.ActionClient
            - EndpointType.MPublisher
            - EndpointType.PSubscriber
        etransport (TransportType): The type of transport to use for the endpoint.
            Possible values include:
            - TransportType.AMQP
            - TransportType.REDIS
            - TransportType.MQTT

    Returns:
        The corresponding endpoint class based on the provided endpoint type and transport type.

    Raises:
        ValueError: If an unsupported transport type or endpoint type is provided.
    """
    if etransport == TransportType.AMQP:
        import commlib.transports.amqp as comm
    elif etransport == TransportType.REDIS:
        import commlib.transports.redis as comm
    elif etransport == TransportType.MQTT:
        import commlib.transports.mqtt as comm
    else:
        raise ValueError()
    if etype == EndpointType.RPCService:
        return comm.RPCService
    elif etype == EndpointType.RPCClient:
        return comm.RPCClient
    elif etype == EndpointType.Publisher:
        return comm.Publisher
    elif etype == EndpointType.Subscriber:
        return comm.Subscriber
    elif etype == EndpointType.ActionService:
        return comm.ActionService
    elif etype == EndpointType.ActionClient:
        return comm.ActionClient
    elif etype == EndpointType.MPublisher:
        return comm.MPublisher
    elif etype == EndpointType.PSubscriber:
        return comm.PSubscriber
