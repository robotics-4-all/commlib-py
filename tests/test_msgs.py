#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest

from commlib.msg import as_dict
from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from commlib.msg import MessageHeader, RPCMessage, PubSubMessage, Object
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
        header.seq = 1
        header.timestamp = 12312451231231
        header.node_id = 'testnode'
        header.properties = {'a': 1}

    def test_nested_message_to_dict(self):
        _d = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            }
        }
        @DataClass
        class TestObject(Object):
            c: int = 1
            d: int = 2

        @DataClass
        class TestPubSubMessage(PubSubMessage):
            a: int = 1
            b: TestObject = TestObject()

        _msg = TestPubSubMessage()
        _msg.b = TestObject(c=2, d=3)
        assert _msg.as_dict() == _d

    def test_nested_message_from_dict(self):
        _d = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            }
        }
        @DataClass
        class TestObject(Object):
            c: int = 1
            d: int = 2

        @DataClass
        class TestPubSubMessage(PubSubMessage):
            a: int = 1
            b: TestObject = TestObject()

        _msg = TestPubSubMessage()
        _msg.from_dict(_d)
        assert _msg == TestPubSubMessage(a=1, b=TestObject(c=2, d=3))

    def test_from_dict_0(self):
        req_d = {'a': 1, 'b': 2}
        resp_d = {'c': 3, 'd': 4}
        class TestRPCMessage(RPCMessage):
            @DataClass
            class Request(RPCMessage.Request):
                a: int = 0
                b: int = 0

            @DataClass
            class Response(RPCMessage.Response):
                c: int = 0
                d: int = 0

        req = TestRPCMessage.Request()
        req.from_dict(req_d)
        assert req == TestRPCMessage.Request(a=1, b=2)
        req = TestRPCMessage.Request(**req_d)
        assert req == TestRPCMessage.Request(a=1, b=2)

        resp = TestRPCMessage.Response()
        resp.from_dict(resp_d)
        assert resp == TestRPCMessage.Response(c=3, d=4)
        resp = TestRPCMessage.Response(**resp_d)
        assert resp == TestRPCMessage.Response(c=3, d=4)
