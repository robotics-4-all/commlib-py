#!/usr/bin/env python

import sys

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


def on_message(msg):
    # pass
    print(f"Received front sonar data: {msg}")


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
    conn_params = ConnectionParameters()

    node = Node(
        node_name="sensors.sonar.front",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )

    _ = node.create_subscriber(
        msg_type=SonarMessage, topic="sensors.sonar.front", on_message=on_message
    )

    node.run_forever(sleep_rate=1)
