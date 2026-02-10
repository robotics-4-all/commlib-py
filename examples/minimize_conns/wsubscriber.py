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

        if args.timeout:
        import threading
        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
