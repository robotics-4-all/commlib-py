#!/usr/bin/env python

"""Extended tests for message classes."""

import unittest
from typing import Optional

from commlib.msg import Message, MessageHeader, PubSubMessage, RPCMessage


class TestMessageHeader(unittest.TestCase):
    """Test MessageHeader class."""

    def test_header_defaults(self):
        """Test MessageHeader default values."""
        header = MessageHeader()
        self.assertIsNotNone(header)
        self.assertEqual(header.msg_id, -1)  # Default is -1, not 0
        self.assertEqual(header.node_id, "")

    def test_header_assignment(self):
        """Test MessageHeader field assignment."""
        header = MessageHeader()
        header.msg_id = 42
        header.node_id = "test_node"
        header.timestamp = 1234567890
        header.agent = "test_agent"
        header.properties = {"key": "value"}

        self.assertEqual(header.msg_id, 42)
        self.assertEqual(header.node_id, "test_node")
        self.assertEqual(header.timestamp, 1234567890)
        self.assertEqual(header.agent, "test_agent")
        self.assertEqual(header.properties, {"key": "value"})

    def test_header_to_dict(self):
        """Test MessageHeader serialization to dict."""
        header = MessageHeader()
        header.msg_id = 1
        header.node_id = "node1"
        header_dict = header.model_dump()
        self.assertIn("msg_id", header_dict)
        self.assertIn("node_id", header_dict)
        self.assertEqual(header_dict["msg_id"], 1)
        self.assertEqual(header_dict["node_id"], "node1")


class TestBaseMessage(unittest.TestCase):
    """Test base Message class."""

    def test_message_creation(self):
        """Test Message object creation."""
        msg = Message()
        self.assertIsNotNone(msg)

    def test_message_to_dict(self):
        """Test Message serialization."""
        msg = Message()
        msg_dict = msg.model_dump()
        self.assertIsInstance(msg_dict, dict)

    def test_message_from_dict(self):
        """Test Message creation from dict."""
        msg_dict = {}
        msg = Message.model_validate(msg_dict)
        self.assertIsNotNone(msg)


class TestPubSubMessage(unittest.TestCase):
    """Test PubSubMessage class."""

    def test_pubsub_message_creation(self):
        """Test PubSubMessage creation."""
        msg = PubSubMessage()
        self.assertIsNotNone(msg)

    def test_custom_pubsub_message(self):
        """Test custom PubSubMessage subclass."""
        class CustomMessage(PubSubMessage):
            value: int = 0
            name: str = ""

        msg = CustomMessage()
        msg.value = 42
        msg.name = "test"
        self.assertEqual(msg.value, 42)
        self.assertEqual(msg.name, "test")

    def test_custom_pubsub_message_to_dict(self):
        """Test custom PubSubMessage serialization."""
        class CustomMessage(PubSubMessage):
            value: int = 0
            name: str = ""

        msg = CustomMessage(value=10, name="msg")
        msg_dict = msg.model_dump()
        self.assertEqual(msg_dict["value"], 10)
        self.assertEqual(msg_dict["name"], "msg")

    def test_nested_pubsub_message(self):
        """Test nested PubSubMessage."""
        class InnerMessage(Message):
            inner_value: int = 0

        class OuterMessage(PubSubMessage):
            outer_value: int = 0
            inner: Optional[InnerMessage] = None

        outer = OuterMessage()
        outer.outer_value = 10
        outer.inner = InnerMessage(inner_value=5)

        outer_dict = outer.model_dump()
        self.assertEqual(outer_dict["outer_value"], 10)
        self.assertEqual(outer_dict["inner"]["inner_value"], 5)


class TestRPCMessage(unittest.TestCase):
    """Test RPCMessage class."""

    def test_rpc_message_structure(self):
        """Test RPCMessage structure."""
        msg = RPCMessage()
        # RPCMessage should have Request and Response classes
        self.assertTrue(hasattr(RPCMessage, 'Request'))
        self.assertTrue(hasattr(RPCMessage, 'Response'))

    def test_custom_rpc_message(self):
        """Test custom RPCMessage subclass."""
        class AdditionRPC(RPCMessage):
            class Request(RPCMessage.Request):
                a: int = 0
                b: int = 0

            class Response(RPCMessage.Response):
                result: int = 0

        request = AdditionRPC.Request(a=5, b=3)
        self.assertEqual(request.a, 5)
        self.assertEqual(request.b, 3)

        response = AdditionRPC.Response(result=8)
        self.assertEqual(response.result, 8)

    def test_rpc_request_to_dict(self):
        """Test RPC Request serialization."""
        class AdditionRPC(RPCMessage):
            class Request(RPCMessage.Request):
                a: int = 0
                b: int = 0

        request = AdditionRPC.Request(a=10, b=20)
        request_dict = request.model_dump()
        self.assertEqual(request_dict["a"], 10)
        self.assertEqual(request_dict["b"], 20)

    def test_rpc_response_to_dict(self):
        """Test RPC Response serialization."""
        class AdditionRPC(RPCMessage):
            class Response(RPCMessage.Response):
                result: int = 0

        response = AdditionRPC.Response(result=30)
        response_dict = response.model_dump()
        self.assertEqual(response_dict["result"], 30)

    def test_multiple_rpc_message_types(self):
        """Test multiple RPC message type definitions."""
        class MultiplyRPC(RPCMessage):
            class Request(RPCMessage.Request):
                x: int = 0
                y: int = 0

            class Response(RPCMessage.Response):
                product: int = 0

        req = MultiplyRPC.Request(x=4, y=5)
        resp = MultiplyRPC.Response(product=20)

        self.assertEqual(req.x, 4)
        self.assertEqual(req.y, 5)
        self.assertEqual(resp.product, 20)


if __name__ == '__main__':
    unittest.main()
