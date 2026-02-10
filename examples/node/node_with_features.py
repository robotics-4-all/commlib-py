#!/usr/bin/env python

import sys
import time

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


def on_message(msg):
    print(f"Received front sonar data: {msg}")


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


    nodeA = Node(
        node_name="obstacle_avoidance_node",
        connection_params=conn_params,
    )

    nodeA.create_subscriber(
        msg_type=SonarMessage, topic="sensors.sonar.front", on_message=on_message
    )

    nodeA.run()

    nodeB = Node(
        node_name="front_sonar_node",
        connection_params=conn_params,
        ctrl_services=True,  # Create start/stop control services
    )

    pub = nodeB.create_publisher(msg_type=SonarMessage, topic="sensors.sonar.front")

    nodeB.run()

    msg = SonarMessage()
    while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
        msg.range = msg.range + 0.1
        pub.publish(msg)
        time.sleep(1)
