from enum import Enum
from commlib.logger import Logger
from commlib.connection import BaseConnectionParameters
from commlib.transports import BaseTransport
from commlib.serializer import Serializer, JSONSerializer
from commlib.compression import CompressionType

e_logger = None


class BaseEndpoint:
    _transport: BaseTransport = None

    @classmethod
    def logger(cls) -> Logger:
        global e_logger
        if e_logger is None:
            e_logger = Logger(__name__)
        return e_logger

    def __init__(self,
                 debug: bool = False,
                 serializer: Serializer = JSONSerializer,
                 conn_params: BaseConnectionParameters = None,
                 compression: CompressionType = CompressionType.NO_COMPRESSION
                 ):
        self._debug = debug
        self._serializer = serializer
        self._compression = compression
        self._conn_params = conn_params

    @property
    def log(self):
        return self.logger()

    @property
    def debug(self):
        return self._debug


class EndpointType(Enum):
    """EndpointType.
    Types of supported Endpoints.
    """
    RPCService = 1
    RPCClient = 2
    Publisher = 3
    Subscriber = 4
    ActionService = 5
    ActionClient = 6
    MPublisher = 7
    PSubscriber = 8


class TransportType(Enum):
    """TransportType.
    Types of supported Transports
    """
    AMQP = 1
    REDIS = 2
    MQTT = 3


def endpoint_factory(etype: EndpointType, etransport: TransportType):
    """endpoint_factory.
    Create an instance of an endpoint
        (RPCClient, RPCService, Publisher, Subscriber etc..),
        by simply giving its type and transport (MQTT, AMQP, Redis)

    Args:
        etype (EndpointType): Endpoint type
        etransport (TransportType): Transport type
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
