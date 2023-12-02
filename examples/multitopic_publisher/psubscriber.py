#!/usr/bin/env python

import sys

from commlib.node import Node


def on_message(msg, topic):
    print(f"Message at topic <{topic}>: {msg}")


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
        node_name="example5_listener", connection_params=conn_params, debug=True
    )

    sub = node.create_psubscriber(topic="topic.*", on_message=on_message)

    topicA = "topic.a"
    topicB = "topic.b"

    node.run_forever()
