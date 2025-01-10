#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest
from typing import Optional

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters


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
            host="localhost", port="1883",
            username="", password="", ssl=False,
            reconnect_attempts=0)

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_subscriber_strict_topic(self):
        """
        Test the creation of subscribers with strict and wildcard topics.

        This test verifies that a Node can create subscribers for specific topics
        and wildcard topics, and that messages are correctly received by the
        subscribers.

        Steps:
        1. Create a Node instance with the specified connection parameters.
        2. Create a subscriber (sub1) for the strict topic 'sonar.front' and
           define a callback to print received messages.
        3. Run the Node to start processing.
        4. Create another subscriber (sub2) for the wildcard topic 'sonar.front.*'
           and define a callback to print received messages.

        The test ensures that both subscribers are created successfully and are
        able to receive messages on their respective topics.
        """
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=False)
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='sonar.front',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.fail(str(e))
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='sonar.front.123',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.fail(str(e))
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='sonar.front.*',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: sonar.front.*")
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='sonar.front.#',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: sonar.front.#")
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='.',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: .")
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='*',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: *")
        try:
            _ = node.create_subscriber(msg_type=SonarMessage,
                                       topic='#',
                                       on_message=lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: #")
        node.run(wait=True)
        # node.stop()

    def test_wsubscriber_strict_topic(self):
        """
        Test the creation of wsubscribers with strict and wildcard topics.

        This test verifies that a Node can create wsubscribers for specific topics
        and wildcard topics, and that messages are correctly received by the
        wsubscribers.

        Steps:
        1. Create a Node instance with the specified connection parameters.
        2. Create a subscriber (sub1) for the strict topic 'sonar.front' and
           define a callback to print received messages.
        3. Run the Node to start processing.
        4. Create another subscriber (sub2) for the wildcard topic 'sonar.front.*'
           and define a callback to print received messages.

        The test ensures that both subscribers are created successfully and are
        able to receive messages on their respective topics.
        """
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=False)
        sub = node.create_wsubscriber(msg_type=SonarMessage)
        try:
            sub.subscribe('sonar.front', lambda msg: print(msg))
        except ValueError as e:
            self.fail(str(e))
        try:
            sub.subscribe('sonar.front.123', lambda msg: print(msg))
        except ValueError as e:
            self.fail(str(e))
        try:
            sub.subscribe('sonar.front.*', lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: sonar.front.*")
        try:
            sub.subscribe('sonar.front.#', lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: sonar.front.#")
        try:
            sub.subscribe('.', lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: .")
        try:
            sub.subscribe('*', lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: *")
        try:
            sub.subscribe('#', lambda msg: print(msg))
        except ValueError as e:
            self.assertEqual(str(e), "Invalid topic: #")
        node.run(wait=True)
        # node.stop()
