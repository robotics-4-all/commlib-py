from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from .transports.amqp import RPCClient as AMQPRPCClient
from .transports.amqp import RPCServer as AMQPRPCServer
from .transports.amqp import Publisher as AMQPPublisher
from .transports.amqp import Subscriber as AMQPSubscriber

import commlib_py.transports.amqp as amqp
import commlib_py.transports.redis as redis

from enum import Enum


class EndpointType(Enum):
    RPCServer = 1
    RPCClient = 2
    Publisher = 3
    Subscriber = 4


class TransportType(Enum):
    AMQP = 1
    REDIS = 2


def endpoint_factory(self, etype, etransport):
    if etype == EndpointType.RPCServer and etransport == TransportType.AMQP:
        return redis.RPCServer
    elif etype == EndpointType.RPCClient and etransport == TransportType.AMQP:
        return redis.RPCClient
    elif etype == EndpointType.Publisher and etransport == TransportType.AMQP:
        return redis.Publisher
    elif etype == EndpointType.Subscriber and etransport == TransportType.AMQP:
        return redis.Subscriber
    elif etype == EndpointType.RPCServer and etransport == TransportType.REDIS:
        return redis.RPCServer
    elif etype == EndpointType.RPCClient and etransport == TransportType.REDIS:
        return redis.RPCClient
    elif etype == EndpointType.Publisher and etransport == TransportType.REDIS:
        return redis.Publisher
    elif etype == EndpointType.Subscriber and etransport == TransportType.REDIS:
        return redis.Subscriber
