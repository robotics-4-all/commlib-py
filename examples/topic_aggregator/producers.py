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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        broker = "redis"
    else:
        broker = str(sys.argv[1])
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters(
        host="localhost",
        # port=1883,
        username="",
        password="",
        ssl=False,
    )

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
            msg_1.x += 1
            msg_2.theta += 2
            pub.publish(msg_1, topic_1)
            pub.publish(msg_2, topic_2)
            time.sleep(1)
    except Exception as e:
        print(e)
        node.stop()
