#!/usr/bin/env python

import time

import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.msg import PubSubMessage, DataClass

from commlib.bridges import TopicBridgeType, PTopicBridge


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


if __name__ == '__main__':
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = 'sensors.*'
    bB_namespace = 'myrobot'
    p1 = 'sensors.sonar.front'
    p2 = 'sensors.ir.rear'

    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()

    br = PTopicBridge(TopicBridgeType.REDIS_TO_MQTT,
                      bA_uri,
                      bB_namespace,
                      bA_params,
                      bB_params,
                      msg_type=SonarMessage,
                      debug=True)
    br.run_forever()
