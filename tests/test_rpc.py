#!/usr/bin/env python

"""Tests for `commlib` package."""

import unittest

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node
from commlib.transports.mock import ConnectionParameters


class SonarMessage(PubSubMessage):
    """Sonar Message."""
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class AddTwoIntMessage(RPCMessage):
    """Add Two Int Message."""
    class Request(RPCMessage.Request):
        """Request payload."""
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        """Response payload."""
        c: int = 0


class TestPubSub(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.connparams = ConnectionParameters(
            host="test",
            port=1234,
            reconnect_attempts=0,
        )

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_rpc_service_double_run(self):
        """Test something."""
        node = Node(
            node_name="test_node",
            connection_params=self.connparams,
            heartbeats=False,
            debug=True,
        )
        rpc = node.create_rpc(
            msg_type=SonarMessage,
            rpc_name="sonar.front",
            on_request=print,
        )
        rpc.run()
        rpc.run()

        # Smoke test: no exception raised on double run

    def test_rpc_client_double_run(self):
        """Test something."""
        node = Node(
            node_name="test_node",
            connection_params=self.connparams,
            heartbeats=False,
            debug=True,
        )
        rpcc = node.create_rpc_client(msg_type=SonarMessage, rpc_name="sonar.front")
        rpcc.run()
        rpcc.run()

        # Smoke test: no exception raised on double run
