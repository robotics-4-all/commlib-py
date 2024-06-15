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

    def test_rpc_service_double_run(self):
        """Test something."""
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=True)
        rpc = node.create_rpc(msg_type=SonarMessage,
                              rpc_name='sonar.front',
                              on_request=lambda msg: print(msg))
        rpc.run()
        rpc.run()

        self.assertTrue(1, 1)

    def test_rpc_client_double_run(self):
        """Test something."""
        node = Node(node_name='test_node',
                    connection_params=self.connparams,
                    heartbeats=False,
                    debug=True)
        rpcc = node.create_rpc_client(msg_type=SonarMessage,
                                      rpc_name='sonar.front')
        rpcc.run()
        rpcc.run()

        self.assertTrue(1, 1)
