"""Protocol Transports sub-package"""

__author__ = """klpanagi"""
__email__ = "klpanagi@gmail.com"


from enum import Enum


class TransportType(Enum):
    AMQP = 1
    REDIS = 2
    MQTT = 3
    KAFKA = 4


def connection_params_for_transport(transport: TransportType):
    if transport == TransportType.MQTT:
        from commlib.transports.mqtt import ConnectionParameters

        return ConnectionParameters
    elif transport == TransportType.REDIS:
        from commlib.transports.redis import ConnectionParameters

        return ConnectionParameters
    elif transport == TransportType.AMQP:
        from commlib.transports.amqp import ConnectionParameters

        return ConnectionParameters
    elif transport == TransportType.KAFKA:
        from commlib.transports.kafka import ConnectionParameters

        return ConnectionParameters
