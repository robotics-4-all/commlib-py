#!/usr/bin/env python

import sys

from commlib.node import Node


def clb_1(msg):
    print(f"Sonar Left 1: {msg}")


def clb_2(msg):
    print(f"Sonar Right: {msg}")

def clb_3(msg):
    print(f"Sonar Front: {msg}")


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
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="example5_listener", connection_params=conn_params,
        debug=True, heartbeats=False
    )

    sub = node.create_wsubscriber()

    topicA = "sonar.left"
    topicB = "sonar.right"
    topicC = "sonar.front"

    sub.subscribe(topicA, clb_1)
    sub.subscribe(topicB, clb_2)
    sub.subscribe(topicC, clb_3)

    node.run_forever()
