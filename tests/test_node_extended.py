#!/usr/bin/env python

"""Extended tests for Node class."""

import unittest
from typing import Optional

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node
from commlib.transports.mock import ConnectionParameters


class SensorMessage(PubSubMessage):
    """Test sensor message."""
    header: MessageHeader = MessageHeader()
    value: float = 0.0
    unit: str = ""


class MathRPC(RPCMessage):
    """Test math RPC."""
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        result: int = 0


class TestNodeExtended(unittest.TestCase):
    """Extended tests for Node class."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(
            host="test",
            port="1234",
            reconnect_attempts=0
        )

    def test_node_creation_basic(self):
        """Test basic Node creation."""
        node = Node(
            node_name="test_node",
            connection_params=self.conn_params,
            heartbeats=False,
            debug=True
        )
        self.assertEqual(node._node_name, "test_node")
        self.assertTrue(node._debug)

    def test_node_name_property(self):
        """Test Node name property."""
        node = Node(
            node_name="my.sensor.node",
            connection_params=self.conn_params
        )
        self.assertEqual(node._node_name, "my.sensor.node")

    def test_node_without_heartbeats(self):
        """Test Node without heartbeats."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        self.assertFalse(node._heartbeats)

    def test_node_with_heartbeats(self):
        """Test Node with heartbeats."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=True
        )
        self.assertTrue(node._heartbeats)

    def test_node_publishers_tracking(self):
        """Test Node tracks publishers."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        initial_count = len(node._publishers)
        node.create_publisher(
            msg_type=SensorMessage,
            topic="sensor.temperature"
        )
        self.assertEqual(len(node._publishers), initial_count + 1)

    def test_node_subscribers_tracking(self):
        """Test Node tracks subscribers."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        initial_count = len(node._subscribers)
        node.create_subscriber(
            msg_type=SensorMessage,
            topic="sensor.data",
            on_message=lambda msg: None
        )
        self.assertEqual(len(node._subscribers), initial_count + 1)

    def test_node_rpcs_tracking(self):
        """Test Node tracks RPC services."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        initial_count = len(node._rpc_services)
        node.create_rpc(
            msg_type=MathRPC,
            rpc_name="math.add",
            on_request=lambda req: MathRPC.Response(result=0)
        )
        self.assertEqual(len(node._rpc_services), initial_count + 1)

    def test_node_rpc_clients_tracking(self):
        """Test Node tracks RPC clients."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        initial_count = len(node._rpc_clients)
        node.create_rpc_client(
            msg_type=MathRPC,
            rpc_name="math.multiply"
        )
        self.assertEqual(len(node._rpc_clients), initial_count + 1)

    def test_node_logger(self):
        """Test Node logger."""
        logger = Node.logger()
        self.assertIsNotNone(logger)
        self.assertTrue(hasattr(logger, 'info'))

    def test_node_logger_singleton(self):
        """Test Node logger is singleton."""
        logger1 = Node.logger()
        logger2 = Node.logger()
        self.assertIs(logger1, logger2)

    def test_node_connection_params(self):
        """Test Node stores connection parameters."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params
        )
        self.assertEqual(node._conn_params, self.conn_params)

    def test_node_multiple_publishers(self):
        """Test Node with multiple publishers."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        pub1 = node.create_publisher(msg_type=SensorMessage, topic="topic1")
        pub2 = node.create_publisher(msg_type=SensorMessage, topic="topic2")
        self.assertEqual(len(node._publishers), 2)

    def test_node_multiple_subscribers(self):
        """Test Node with multiple subscribers."""
        node = Node(
            node_name="test",
            connection_params=self.conn_params,
            heartbeats=False
        )
        sub1 = node.create_subscriber(
            msg_type=SensorMessage,
            topic="topic1",
            on_message=lambda msg: None
        )
        sub2 = node.create_subscriber(
            msg_type=SensorMessage,
            topic="topic2",
            on_message=lambda msg: None
        )
        self.assertEqual(len(node._subscribers), 2)


if __name__ == '__main__':
    unittest.main()
