#!/usr/bin/env python

import sys

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.utils import Rate


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class SonarNode(Node):
    count = 0

    def __init__(self, sensor_id: str = None, pub_freq: int = 2, *args, **kwargs):
        if sensor_id is None:
            sensor_id = f"Sonar-{SonarNode.count}"
        self.sensor_id = sensor_id
        self.pub_freq = pub_freq
        self.topic = f"sensors.sonar.{self.sensor_id}"
        SonarNode.count += 1

        super().__init__(node_name="sensors.sonar.front", *args, **kwargs)
        self.pub = self.create_publisher(msg_type=SonarMessage, topic=self.topic)

    def start(self):
        self.run()
        rate = Rate(self.pub_freq)
        while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
            msg = SonarMessage()
            self.pub.publish(msg)
            rate.sleep()


import time

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", type=str, default="redis",
                        choices=["redis", "amqp", "mqtt", "kafka"],
                        help="Broker type")
    parser.add_argument("--host", type=str, default="localhost",
                        help="Broker host")
    parser.add_argument("--port", type=int, default=None,
                        help="Broker port")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Max time to run (seconds)")
    args = parser.parse_args()

    if args.broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif args.broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif args.broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters
    
    start_time = time.time()
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port


    sonar_node = SonarNode(conn_params=conn_params)
    sonar_node.start()
