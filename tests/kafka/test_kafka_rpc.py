#!/usr/bin/env python

"""Integration tests for Kafka RPC endpoints.

Requires a running Kafka broker. Set COMMLIB_KAFKA_HOST and
COMMLIB_KAFKA_PORT environment variables if not localhost:29092.
"""

import os
import time
import unittest

import pytest

from commlib.msg import RPCMessage
from commlib.node import Node
from commlib.transports.kafka import ConnectionParameters


class AddTwoIntMessage(RPCMessage):
    """Add Two Int Message."""
    class Request(RPCMessage.Request):
        """Request payload."""
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        """Response payload."""
        c: int = 0


@pytest.mark.kafka
@pytest.mark.integration
class TestKafkaRPC(unittest.TestCase):
    """Test Kafka RPC."""
    def setUp(self):
        kafka_host = os.getenv("COMMLIB_KAFKA_HOST", "localhost")
        kafka_port = int(os.getenv("COMMLIB_KAFKA_PORT", "29092"))
        self.conn_params = ConnectionParameters(host=kafka_host, port=kafka_port)

    def test_rpc_service_client(self):
        """Test rpc service client."""
        def add_handler(msg):
            return AddTwoIntMessage.Response(c=msg.a + msg.b)

        service_node = Node(
            node_name="kafka_rpc_service",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        service_node.create_rpc(
            msg_type=AddTwoIntMessage,
            rpc_name="kafka.test.add_two_ints",
            on_request=add_handler,
        )
        service_node.run()
        time.sleep(3.0)

        client_node = Node(
            node_name="kafka_rpc_client",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        rpc_client = client_node.create_rpc_client(
            msg_type=AddTwoIntMessage,
            rpc_name="kafka.test.add_two_ints",
        )
        client_node.run()
        time.sleep(2.0)

        req = AddTwoIntMessage.Request(a=5, b=3)
        resp = rpc_client.call(req, timeout=10.0)

        self.assertIsNotNone(resp)
        self.assertEqual(resp.c, 8)

        service_node.stop()
        client_node.stop()

    def test_rpc_server_multi_endpoints(self):
        """Test rpc server multi endpoints."""
        def add_handler(msg):
            return AddTwoIntMessage.Response(c=msg.a + msg.b)

        def multiply_handler(msg):
            return AddTwoIntMessage.Response(c=msg.a * msg.b)

        server_node = Node(
            node_name="kafka_rpc_server",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        rpc_server = server_node.create_rpc_server(
            msg_type=AddTwoIntMessage,
            rpc_name="kafka.test.server_base",
        )
        rpc_server.register_rpc(
            rpc_name="kafka.test.server_base.add",
            msg_type=AddTwoIntMessage,
            on_request=add_handler,
        )
        rpc_server.register_rpc(
            rpc_name="kafka.test.server_base.multiply",
            msg_type=AddTwoIntMessage,
            on_request=multiply_handler,
        )
        server_node.run()
        time.sleep(3.0)

        client_node = Node(
            node_name="kafka_rpc_server_client",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        add_client = client_node.create_rpc_client(
            msg_type=AddTwoIntMessage,
            rpc_name="kafka.test.server_base.add",
        )
        multiply_client = client_node.create_rpc_client(
            msg_type=AddTwoIntMessage,
            rpc_name="kafka.test.server_base.multiply",
        )
        client_node.run()
        time.sleep(2.0)

        add_resp = add_client.call(AddTwoIntMessage.Request(a=10, b=5), timeout=10.0)
        self.assertEqual(add_resp.c, 15)

        mult_resp = multiply_client.call(
            AddTwoIntMessage.Request(a=3, b=4), timeout=10.0
        )
        self.assertEqual(mult_resp.c, 12)

        server_node.stop()
        client_node.stop()


if __name__ == "__main__":
    unittest.main()
