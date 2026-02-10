#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest
from unittest.mock import MagicMock

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node
from commlib.transports.mock import ConnectionParameters


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


class TestNode(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.connparams = ConnectionParameters(host="test", port="1234")

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_node_create_wrong_transport(self):
        try:
            node = Node(
                node_name="sensors.sonar.front", connection_params=self.connparams
            )
            self.assertTrue(1, 0)
        except ValueError as e:
            print(str(e))
            if str(e) == "ValueError: Transport type is not supported!":
                self.assertTrue(1, 1)
            else:
                self.assertTrue(1, 0)

    def test_node_create_publisher(self):
        node = Node(node_name="sensors.sonar.front", connection_params=self.connparams)
        node.create_publisher(msg_type=SonarMessage, topic="sensors.sonar.front")
        self.assertTrue(len(node._publishers), 1)

    def test_node_create_subscriber(self):
        node = Node(node_name="sensors.sonar.front", connection_params=self.connparams)

        def on_message(msg):
            pass
        node.create_subscriber(msg_type=SonarMessage,
                               topic="sensors.sonar.front",
                               on_message=on_message)
        self.assertTrue(len(node._subscribers), 1)

    def test_node_on_connected_callback(self):
        """Test that on_connected callback is called when node starts."""
        mock_callback = MagicMock()
        node = Node(
            node_name="test_node",
            connection_params=self.connparams,
            on_connected=mock_callback
        )

        # Create a dummy publisher so the node has an endpoint to connect
        node.create_publisher(msg_type=SonarMessage, topic="test_topic")

        # Run node synchronously (wait=True)
        node.run(wait=True)

        # Verify callback was called
        mock_callback.assert_called_once()

        node.stop()

    def test_node_on_connected_callback_async(self):
        """Test that on_connected callback is called when node starts asynchronously."""
        mock_callback = MagicMock()
        node = Node(
            node_name="test_node_async",
            connection_params=self.connparams,
            on_connected=mock_callback
        )

        # Create a dummy publisher so the node has an endpoint to connect
        node.create_publisher(msg_type=SonarMessage, topic="test_topic_async")

        # Run node asynchronously (wait=False)
        node.run(wait=False)

        # Wait a bit for the async thread to execute
        time.sleep(0.1)

        # Verify callback was called
        mock_callback.assert_called_once()

        node.stop()
