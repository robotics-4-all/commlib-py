#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader
from commlib.connection import ConnectionParametersBase
from commlib.node import Node
from commlib.utils import Rate


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class SonarNode(Node):
    count = 0

    def __init__(self,
                 sensor_id: str = None, pub_freq: int = 2,
                 *args, **kwargs):
        if sensor_id is None:
            sensor_id = f'Sonar-{SonarNode.count}'
        self.sensor_id = sensor_id
        self.pub_freq = pub_freq
        self.topic = f'sensors.sonar.{self.sensor_id}'
        SonarNode.count += 1

        super().__init__(node_name='sensors.sonar.front',
            *args, **kwargs)
        self.pub = self.create_publisher(msg_type=SonarMessage,
                                         topic=self.topic)

    def start(self):
        self.run()
        rate = Rate(self.pub_freq)
        while True:
            msg = SonarMessage()
            self.pub.publish(msg)
            rate.sleep()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    sonar_node = SonarNode(conn_params=conn_params)
    sonar_node.start()
