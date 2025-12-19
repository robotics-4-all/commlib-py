#!/usr/bin/env python

"""Tests for commlib RPC module."""

import unittest
import time
from typing import Optional

from commlib.msg import RPCMessage
from commlib.rpc import CommRPCHeader, CommRPCMessage, BaseRPCServer
from commlib.transports.mock import ConnectionParameters
from commlib.utils import gen_timestamp


class TestCommRPCHeader(unittest.TestCase):
    """Test CommRPCHeader class."""

    def test_header_creation(self):
        """Test CommRPCHeader creation."""
        header = CommRPCHeader()
        self.assertEqual(header.reply_to, "")
        self.assertIsNotNone(header.timestamp)
        self.assertEqual(header.content_type, "json")
        self.assertEqual(header.encoding, "utf8")
        self.assertEqual(header.agent, "commlib")

    def test_header_custom_values(self):
        """Test CommRPCHeader with custom values."""
        header = CommRPCHeader(
            reply_to="service.reply",
            timestamp=12345,
            content_type="msgpack",
            encoding="utf16",
            agent="custom-agent"
        )
        self.assertEqual(header.reply_to, "service.reply")
        self.assertEqual(header.timestamp, 12345)
        self.assertEqual(header.content_type, "msgpack")
        self.assertEqual(header.encoding, "utf16")
        self.assertEqual(header.agent, "custom-agent")

    def test_header_timestamp_is_int(self):
        """Test CommRPCHeader timestamp is integer."""
        header = CommRPCHeader()
        self.assertIsInstance(header.timestamp, int)

    def test_header_partial_assignment(self):
        """Test CommRPCHeader partial assignment."""
        header = CommRPCHeader(reply_to="reply.topic")
        self.assertEqual(header.reply_to, "reply.topic")
        self.assertEqual(header.content_type, "json")
        self.assertEqual(header.encoding, "utf8")


class TestCommRPCMessage(unittest.TestCase):
    """Test CommRPCMessage class."""

    def test_message_creation(self):
        """Test CommRPCMessage creation."""
        msg = CommRPCMessage()
        self.assertIsNotNone(msg.header)
        self.assertEqual(msg.data, {})

    def test_message_with_header(self):
        """Test CommRPCMessage with custom header."""
        header = CommRPCHeader(reply_to="reply.topic")
        msg = CommRPCMessage(header=header)
        self.assertEqual(msg.header.reply_to, "reply.topic")

    def test_message_with_data(self):
        """Test CommRPCMessage with data."""
        data = {"key": "value", "number": 42}
        msg = CommRPCMessage(data=data)
        self.assertEqual(msg.data, data)

    def test_message_complete(self):
        """Test CommRPCMessage with header and data."""
        header = CommRPCHeader(reply_to="reply.service")
        data = {"result": "success"}
        msg = CommRPCMessage(header=header, data=data)
        self.assertEqual(msg.header.reply_to, "reply.service")
        self.assertEqual(msg.data, data)


class TestBaseRPCServer(unittest.TestCase):
    """Test BaseRPCServer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(
            host="test",
            port="1234",
            reconnect_attempts=0
        )

    def test_rpc_server_creation(self):
        """Test BaseRPCServer creation."""
        server = BaseRPCServer(
            base_uri="my.service",
            conn_params=self.conn_params
        )
        self.assertEqual(server._base_uri, "my.service")
        self.assertEqual(server._max_workers, 4)
        self.assertIsNotNone(server._executor)

    def test_rpc_server_custom_workers(self):
        """Test BaseRPCServer with custom worker count."""
        server = BaseRPCServer(
            base_uri="service",
            workers=8,
            conn_params=self.conn_params
        )
        self.assertEqual(server._max_workers, 8)

    def test_rpc_server_with_service_map(self):
        """Test BaseRPCServer with service map."""
        def dummy_service(req):
            return {"result": "ok"}

        svc_map = {"my_service": dummy_service}
        server = BaseRPCServer(
            base_uri="test",
            svc_map=svc_map,
            conn_params=self.conn_params
        )
        self.assertEqual(server._svc_map, svc_map)

    def test_rpc_server_interval(self):
        """Test BaseRPCServer interval property."""
        server = BaseRPCServer(
            interval=0.5,
            conn_params=self.conn_params
        )
        self.assertEqual(server.interval, 0.5)

    def test_rpc_server_default_interval(self):
        """Test BaseRPCServer default interval."""
        server = BaseRPCServer(conn_params=self.conn_params)
        self.assertEqual(server.interval, 0.001)

    def test_rpc_server_logger(self):
        """Test BaseRPCServer logger."""
        logger = BaseRPCServer.logger()
        self.assertIsNotNone(logger)
        self.assertTrue(hasattr(logger, 'info'))

    def test_rpc_server_logger_singleton(self):
        """Test BaseRPCServer logger is singleton."""
        logger1 = BaseRPCServer.logger()
        logger2 = BaseRPCServer.logger()
        self.assertIs(logger1, logger2)

    def test_rpc_server_debug_mode(self):
        """Test BaseRPCServer with debug mode."""
        server = BaseRPCServer(debug=True, conn_params=self.conn_params)
        self.assertTrue(server.debug)

    def test_rpc_server_stop_event(self):
        """Test BaseRPCServer stop event."""
        server = BaseRPCServer(conn_params=self.conn_params)
        self.assertFalse(server._t_stop_event.is_set())

    def test_rpc_server_comm_object(self):
        """Test BaseRPCServer communication object."""
        server = BaseRPCServer(conn_params=self.conn_params)
        self.assertIsInstance(server._comm_obj, CommRPCMessage)


if __name__ == '__main__':
    unittest.main()
