#!/usr/bin/env python

"""Integration tests for Kafka pub/sub endpoints.

Requires a running Kafka broker. Set COMMLIB_KAFKA_HOST and
COMMLIB_KAFKA_PORT environment variables if not localhost:29092.
"""

import os
import time
import threading
import unittest

import pytest

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.kafka import ConnectionParameters


class SensorMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    temperature: float = 0.0
    humidity: float = 0.0


@pytest.mark.kafka
@pytest.mark.integration
class TestKafkaPubSub(unittest.TestCase):
    def setUp(self):
        kafka_host = os.getenv("COMMLIB_KAFKA_HOST", "localhost")
        kafka_port = int(os.getenv("COMMLIB_KAFKA_PORT", "29092"))
        self.conn_params = ConnectionParameters(host=kafka_host, port=kafka_port)

    def test_publisher_subscriber_basic(self):
        received = []
        ready = threading.Event()

        def on_message(msg):
            received.append(msg)
            ready.set()

        node = Node(
            node_name="kafka_pubsub_test",
            connection_params=self.conn_params,
            heartbeats=False,
        )

        sub = node.create_subscriber(
            msg_type=SensorMessage,
            topic="kafka.test.sensor",
            on_message=on_message,
        )
        pub = node.create_publisher(
            msg_type=SensorMessage,
            topic="kafka.test.sensor",
        )

        node.run()
        time.sleep(2.0)

        msg = SensorMessage(temperature=25.5, humidity=60.0)
        pub.publish(msg)

        ready.wait(timeout=10.0)
        self.assertGreaterEqual(len(received), 1)

        node.stop()

    def test_mpublisher_psubscriber(self):
        received = []
        ready = threading.Event()

        def on_message(msg, topic=None):
            received.append(msg)
            if len(received) >= 2:
                ready.set()

        node = Node(
            node_name="kafka_mpub_test",
            connection_params=self.conn_params,
            heartbeats=False,
        )

        psub = node.create_psubscriber(
            msg_type=SensorMessage,
            topic="kafka.test.multi.*",
            on_message=on_message,
        )
        mpub = node.create_mpublisher(msg_type=SensorMessage)

        node.run()
        time.sleep(2.0)

        mpub.publish(
            SensorMessage(temperature=20.0, humidity=50.0),
            "kafka.test.multi.a",
        )
        mpub.publish(
            SensorMessage(temperature=30.0, humidity=70.0),
            "kafka.test.multi.b",
        )

        ready.wait(timeout=10.0)
        self.assertGreaterEqual(len(received), 2)

        node.stop()


if __name__ == "__main__":
    unittest.main()
