"""Protocol Transports sub-package"""

__author__ = """klpanagi"""
__email__ = "klpanagi@gmail.com"


from enum import Enum


class TransportType(Enum):
    AMQP = 1
    REDIS = 2
    MQTT = 3
    KAFKA = 4
