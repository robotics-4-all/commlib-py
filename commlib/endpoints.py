from enum import Enum


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
