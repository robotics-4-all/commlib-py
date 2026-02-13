#!/usr/bin/env python

import time
import argparse
import threading
from pydantic import Field

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node


class DemoMessage(PubSubMessage):
    """Demo message for testing pub/sub communication."""

    header: MessageHeader = Field(default_factory=lambda: MessageHeader())
    seq: int = 0
    payload: str = ""


def main():
    parser = argparse.ArgumentParser(description="Test PubSub communication")
    parser.add_argument(
        "--broker",
        type=str,
        default="redis",
        choices=["redis", "amqp", "mqtt", "kafka"],
        help="Broker type",
    )
    parser.add_argument("--topic", type=str, default="test.pubsub", help="Topic to use")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of messages to send"
    )

    args = parser.parse_args()

    broker = args.broker

    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters

    print(f"Connecting to {broker} broker...")

    conn_params = ConnectionParameters()

    node = Node(
        node_name="test_pubsub_node", connection_params=conn_params, heartbeats=False
    )

    received_count = 0
    received_event = threading.Event()

    def on_message(msg):
        nonlocal received_count
        print(f"Received message: seq={msg.seq}, payload={msg.payload}")
        received_count += 1
        if received_count >= args.count:
            received_event.set()

    _sub = node.create_subscriber(
        msg_type=DemoMessage, topic=args.topic, on_message=on_message
    )

    pub = node.create_publisher(msg_type=DemoMessage, topic=args.topic)

    node.run()

    # Wait for connection/subscription
    time.sleep(1)

    print(f"Publishing {args.count} messages to {args.topic}...")

    for i in range(args.count):
        msg = DemoMessage(seq=i, payload=f"Message {i}")
        pub.publish(msg)
        time.sleep(0.1)

    print("Waiting for messages...")
    if received_event.wait(timeout=5.0):
        print("SUCCESS: All messages received.")
    else:
        print(f"FAILURE: Timed out. Received {received_count}/{args.count} messages.")

    node.stop()


if __name__ == "__main__":
    main()
