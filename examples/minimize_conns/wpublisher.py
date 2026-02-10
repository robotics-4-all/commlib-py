#!/usr/bin/env python

import sys
import time

from pydantic import Field

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node


class SonarMessage(PubSubMessage):
    header: MessageHeader = Field(default_factory=lambda: MessageHeader())
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


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


    node = Node(
        node_name="example5_publisher",
        connection_params=conn_params,
        debug=True,
        heartbeats=False,
    )

    mpub = node.create_mpublisher()

    topicA = "sonar.left"
    topicB = "sonar.right"
    topicC = "sonar.front"

    wpub_1 = node.create_wpublisher(mpub, topicA)
    wpub_2 = node.create_wpublisher(mpub, topicB)
    wpub_3 = node.create_wpublisher(mpub, topicC)

    node.run()

    sonar_left_range = 1
    sonar_right_range = 1
    sonar_front_range = 1

    while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
        sonar_left_msg = SonarMessage(range=sonar_left_range)
        sonar_right_msg = SonarMessage(range=sonar_right_range)
        sonar_front_mst = SonarMessage(range=sonar_front_range)
        wpub_1.publish(sonar_left_msg)
        wpub_2.publish(sonar_right_msg)
        wpub_3.publish(sonar_front_mst)
        time.sleep(0.5)
        sonar_left_range += 1
        sonar_right_range += 1
        sonar_front_range += 1
