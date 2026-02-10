#!/usr/bin/env python

import sys
import time

from commlib.node import Node

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
        node_name="example5_publisher", connection_params=conn_params, debug=True
    )

    pub = node.create_mpublisher()

    node.run()

    topicA = "topic.a"
    topicB = "topic.b"
    count = 0
    while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
        count += 1
        pub.publish({"a": count}, topicA)
        pub.publish({"b": count}, topicB)
        time.sleep(1)
