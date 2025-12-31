#!/usr/bin/env python

import sys

from commlib.node import Node


def on_message(msg, topic):
    print(f"Message at topic <{topic}>: {msg}")


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
    
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port


    node = Node(
        node_name="example5_listener", connection_params=conn_params, debug=True
    )

    sub = node.create_psubscriber(topic="topic.*", on_message=on_message)

    topicA = "topic.a"
    topicB = "topic.b"

        if args.timeout:
        import threading
        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
