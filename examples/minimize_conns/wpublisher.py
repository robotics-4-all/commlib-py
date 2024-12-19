#!/usr/bin/env python

import sys
import time

from commlib.node import Node

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
        node_name="example5_publisher", connection_params=conn_params, debug=True
    )

    mpub = node.create_mpublisher()

    mpub.run()

    topicA = "topic.a"
    topicB = "topic.b"

    wpub_1 = node.create_wpublisher(mpub, topicA)
    wpub_2 = node.create_wpublisher(mpub, topicB)

    while True:
        wpub_1.publish({"a": 1})
        wpub_2.publish({"b": 1})
        time.sleep(1)
