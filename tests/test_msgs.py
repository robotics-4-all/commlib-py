#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest
from typing import Optional

from commlib.msg import Message, MessageHeader, PubSubMessage, RPCMessage
from commlib.timer import Timer


class TestMessages(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_header_message(self):
        """Test MessageHeader class"""
        header = MessageHeader()
        header.msg_id = 1
        header.timestamp = 12312451231231
        header.node_id = "testnode"
        header.properties = {"a": 1}
        header.agent = "test-commlib"

    def test_nested_message_to_dict(self):
        _d = {"a": 1, "b": {"c": 2, "d": 3}}

        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        class TestPubSubMessage(PubSubMessage):
            a: Optional[int] = 1
            b: Optional[TestObject] = TestObject()

        _msg = TestPubSubMessage()
        _msg.b = TestObject(c=2, d=3)
        self.assertEqual(_msg.model_dump(), _d)

    def test_nested_message_from_dict(self):
        _d = {"a": 1, "b": {"c": 2, "d": 3}}

        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        class TestPubSubMessage(PubSubMessage):
            a: Optional[int] = 1
            b: Optional[TestObject] = TestObject()

        _msg = TestPubSubMessage(**_d)
        assert _msg == TestPubSubMessage(a=1, b=TestObject(c=2, d=3))

    def test_from_dict_0(self):
        req_d = {"a": 1, "b": 2}
        resp_d = {"c": 3, "d": 4}

        class TestRPCMessage(RPCMessage):
            class Request(RPCMessage.Request):
                a: Optional[int] = 1
                b: Optional[int] = 2

            class Response(RPCMessage.Response):
                c: Optional[int] = 3
                d: Optional[int] = 4

        req = TestRPCMessage.Request(**req_d)
        assert req == TestRPCMessage.Request(a=1, b=2)

        resp = TestRPCMessage.Response(**resp_d)
        assert resp == TestRPCMessage.Response(c=3, d=4)

    def test_message_to_json(self):
        """Test Message to JSON serialization"""
        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        obj = TestObject(c=10, d=20)
        json_data = obj.to_json()
        self.assertEqual(json_data, '{"c": 10, "d": 20}')

    def test_message_from_json(self):
        """Test Message from JSON deserialization"""
        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        json_data = '{"c": 10, "d": 20}'
        obj = TestObject.from_json(json_data)
        self.assertEqual(obj, TestObject(c=10, d=20))

    def test_pubsub_message_to_json(self):
        """Test PubSubMessage to JSON serialization"""
        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        class TestPubSubMessage(PubSubMessage):
            a: Optional[int] = 1
            b: Optional[TestObject] = TestObject()

        msg = TestPubSubMessage(a=5, b=TestObject(c=10, d=20))
        json_data = msg.to_json()
        self.assertEqual(json_data, '{"a": 5, "b": {"c": 10, "d": 20}}')

    def test_pubsub_message_from_json(self):
        """Test PubSubMessage from JSON deserialization"""
        class TestObject(Message):
            c: Optional[int] = 1
            d: Optional[int] = 2

        class TestPubSubMessage(PubSubMessage):
            a: Optional[int] = 1
            b: Optional[TestObject] = TestObject()

        json_data = '{"a": 5, "b": {"c": 10, "d": 20}}'
        msg = TestPubSubMessage.from_json(json_data)
        self.assertEqual(msg, TestPubSubMessage(a=5, b=TestObject(c=10, d=20)))

    def test_rpc_message_to_json(self):
        """Test RPCMessage to JSON serialization"""
        class TestRPCMessage(RPCMessage):
            class Request(RPCMessage.Request):
                a: Optional[int] = 1
                b: Optional[int] = 2

            class Response(RPCMessage.Response):
                c: Optional[int] = 3
                d: Optional[int] = 4

        req = TestRPCMessage.Request(a=10, b=20)
        resp = TestRPCMessage.Response(c=30, d=40)
        self.assertEqual(req.to_json(), '{"a": 10, "b": 20}')
        self.assertEqual(resp.to_json(), '{"c": 30, "d": 40}')

    def test_rpc_message_from_json(self):
        """Test RPCMessage from JSON deserialization"""
        class TestRPCMessage(RPCMessage):
            class Request(RPCMessage.Request):
                a: Optional[int] = 1
                b: Optional[int] = 2

            class Response(RPCMessage.Response):
                c: Optional[int] = 3
                d: Optional[int] = 4

        req_json = '{"a": 10, "b": 20}'
        resp_json = '{"c": 30, "d": 40}'
        req = TestRPCMessage.Request.from_json(req_json)
        resp = TestRPCMessage.Response.from_json(resp_json)
        self.assertEqual(req, TestRPCMessage.Request(a=10, b=20))
        self.assertEqual(resp, TestRPCMessage.Response(c=30, d=40))
