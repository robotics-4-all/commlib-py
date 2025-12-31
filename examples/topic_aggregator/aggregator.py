#!/usr/bin/env python

import sys

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.aggregation import TopicAggregator


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


    input_topics = ["goaldsl.1.event", "goaldsl.2.event"]
    output_topic = "goaldsl.events"
    processors = {
        "goaldsl.1.event": [
            lambda msg: {
                "position": {
                    "x": msg["x"], "y": msg["y"], "z": 0
                },
                "orientation": {
                    "x": 0, "y": 0, "z": msg["theta"]
                }
            }
        ]
    }
    topicmerge = TopicAggregator(conn_params, input_topics, output_topic,
                                 data_processors=processors)
    topicmerge.start()
