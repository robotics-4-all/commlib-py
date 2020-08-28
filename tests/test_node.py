#!/usr/bin/env python

import unittest
import time

from commlib.node import Node, TransportType


class TestNodeAMQP(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        self.n = Node(transport_type=TransportType.AMQP)

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_create_publisher(self):
        topic = 'testtopic'
        p = self.n.create_publisher(topic=topic)

    def test_create_subscriber(self):
        topic = 'testtopic'

        def on_msg(msg, meta):
            print(msg)

        s = self.n.create_subscriber(topic=topic, on_message=on_msg)
        s.run()

    def test_create_rpc(self):
        rpc_name = 'testrpc'

        def on_request(msg, meta):
            print(msg)

        s = self.n.create_rpc(rpc_name=rpc_name, on_request=on_request)
        s.run()


class TestNodeRedis(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        self.n = Node(transport_type=TransportType.REDIS)

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_create_publisher(self):
        topic = 'testtopic'
        p = self.n.create_publisher(topic=topic)

    def test_create_subscriber(self):
        topic = 'testtopic'

        def on_msg(msg, meta):
            print(msg)

        s = self.n.create_subscriber(topic=topic, on_message=on_msg)
        s.run()

    def test_create_rpc(self):
        rpc_name = 'testrpc'

        def on_request(msg, meta):
            print(msg)

        s = self.n.create_rpc(rpc_name=rpc_name, on_request=on_request)
        s.run()
