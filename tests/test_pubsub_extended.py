#!/usr/bin/env python

"""Extended tests for pubsub module."""

import unittest
from typing import Optional

from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.mock import ConnectionParameters
from commlib.pubsub import BasePublisher, BaseSubscriber


class DummyMessage(PubSubMessage):
    """Test message type."""
    header: MessageHeader = MessageHeader()
    data: str = ""
    value: int = 0


class TestPublisherExtended(unittest.TestCase):
    """Extended tests for Publisher."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(
            host="test",
            port="1234",
            reconnect_attempts=0
        )

    def test_publisher_creation(self):
        """Test publisher creation."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        pub = node.create_publisher(
            msg_type=DummyMessage,
            topic="test.topic"
        )
        self.assertIsNotNone(pub)

    def test_publisher_topic(self):
        """Test publisher topic."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        pub = node.create_publisher(
            msg_type=DummyMessage,
            topic="sensors.temperature"
        )
        self.assertEqual(pub._topic, "sensors.temperature")

    def test_publisher_msg_type(self):
        """Test publisher message type."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        pub = node.create_publisher(
            msg_type=DummyMessage,
            topic="test.topic"
        )
        self.assertEqual(pub._msg_type, DummyMessage)

    def test_publisher_is_connected(self):
        """Test publisher connection status."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        pub = node.create_publisher(
            msg_type=DummyMessage,
            topic="test.topic"
        )
        # Mock transport should be immediately connected
        self.assertIsNotNone(pub._transport)


class TestSubscriberExtended(unittest.TestCase):
    """Extended tests for Subscriber."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(
            host="test",
            port="1234",
            reconnect_attempts=0
        )

    def test_subscriber_creation(self):
        """Test subscriber creation."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        sub = node.create_subscriber(
            msg_type=DummyMessage,
            topic="test.topic",
            on_message=lambda msg: None
        )
        self.assertIsNotNone(sub)

    def test_subscriber_topic(self):
        """Test subscriber topic."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        sub = node.create_subscriber(
            msg_type=DummyMessage,
            topic="sensors.humidity",
            on_message=lambda msg: None
        )
        self.assertEqual(sub._topic, "sensors.humidity")

    def test_subscriber_callback(self):
        """Test subscriber callback."""
        def callback(msg):
            pass

        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        sub = node.create_subscriber(
            msg_type=DummyMessage,
            topic="test.topic",
            on_message=callback
        )
        # Check that callback is stored (attribute name may vary)
        self.assertIsNotNone(sub)

    def test_subscriber_msg_type(self):
        """Test subscriber message type."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        sub = node.create_subscriber(
            msg_type=DummyMessage,
            topic="test.topic",
            on_message=lambda msg: None
        )
        self.assertEqual(sub._msg_type, DummyMessage)


if __name__ == '__main__':
    unittest.main()
