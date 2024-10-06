#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest
from typing import Optional

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


class TestPubSub(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.connparams = ConnectionParameters(
            host="test", port="1234",
            reconnect_attempts=0,
            )

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_subscriber_double_run(self):
        """Test something."""
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=True)
        sub = node.create_subscriber(msg_type=SonarMessage,
                                     topic='sonar.front',
                                     on_message=lambda msg: print(msg))
        sub.run()
        sub.run()

        self.assertTrue(1, 1)

    def test_publisher_double_run(self):
        """Test something."""
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=True)
        pub = node.create_publisher(msg_type=SonarMessage,
                                    topic='sonar.front')
        pub.run()
        pub.run()

        self.assertTrue(1, 1)
