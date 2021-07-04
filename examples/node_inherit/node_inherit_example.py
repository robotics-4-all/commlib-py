#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass
from commlib.node import Node, TransportType
from commlib.utils import Rate


@DataClass
class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class SonarNode(Node):
    count = 0

    def __init__(self, transport_type: TransportType = TransportType.REDIS,
                 sensor_id: str = None, pub_freq: int = 2):
        if transport_type == TransportType.REDIS:
            from commlib.transports.redis import ConnectionParameters
        elif transport_type == TransportType.MQTT:
            from commlib.transports.mqtt import ConnectionParameters
        elif transport_type == TransportType.AMQP:
            from commlib.transports.amqp import ConnectionParameters
        if sensor_id is None:
            sensor_id = int(SonarNode.count)
        self.sensor_id = sensor_id
        self.transport_type = transport_type
        self.pub_freq = pub_freq
        self.topic = f'sensors.sonar.{self.sensor_id}'
        SonarNode.count += 1

        conn_params = ConnectionParameters()
        super().__init__(node_name='sensors.sonar.front',
                         transport_type=self.transport_type,
                         connection_params=conn_params,
                         # heartbeat_uri='nodes.add_two_ints.heartbeat',
                         debug=True)
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
    sonar_node = SonarNode()
    sonar_node.start()
