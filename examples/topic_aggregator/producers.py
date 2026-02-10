#!/usr/bin/env python

import sys
import time

from pydantic import Field

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node


# class Position(PubSubMessage):
#     header: MessageHeader = Field(default_factory=lambda: MessageHeader())
#     position: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
#     orientation: dict = Field(default_factory=lambda: {"roll": 0, "pitch": 0, "yaw": 0})


class Position(PubSubMessage):
    header: MessageHeader = Field(default_factory=lambda: MessageHeader())
    x: float = 0
    y: float = 0
    z: float = 0
    theta: float = 0


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
        node_name="goaldsl_clients",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )

    pub = node.create_mpublisher(msg_type=Position)

    node.run()

    try:
        msg_1 = Position()
        msg_2 = Position()
        topic_1 = "goaldsl.1.event"
        topic_2 = "goaldsl.2.event"
        while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
            msg_1.x += 1
            msg_2.theta += 2
            pub.publish(msg_1, topic_1)
            pub.publish(msg_2, topic_2)
            time.sleep(1)
    except Exception as e:
        print(e)
        node.stop()
