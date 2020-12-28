#!/usr/bin/env python

import time

import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.msg import PubSubMessage, RPCMessage, DataClass

from commlib.bridges import (
    RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType, PTopicBridge
)


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def on_message(msg: SonarMessage, topic: str):
    print(f'[Broker-B] - Data received at topic - {topic}:{msg}')


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
    br.run()

    pub = rcomm.MPublisher(conn_params=bA_params,
                           msg_type=SonarMessage,
                           debug=True)

    sub = mcomm.PSubscriber(
        conn_params=bB_params,
        topic=f'{bB_namespace}.{bA_uri}',
        on_message=on_message
    )
    sub.run()

    count = 0
    msg = SonarMessage()
    while count < 5:
        pub.publish(msg, p1)
        pub.publish(msg, p2)
        time.sleep(1)
        msg.distance += 1
    br.stop()
    sub.stop()
