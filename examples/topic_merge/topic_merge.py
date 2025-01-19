#!/usr/bin/env python

import sys

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.aggregation import TopicMerge


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

    input_topics = ["goaldsl.1.event"]
    output_topic = "goaldsl.1.event"
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
    topicmerge = TopicMerge(conn_params, input_topics, output_topic,
                            data_processors=processors)
    topicmerge.start()
