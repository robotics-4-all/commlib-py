#!/usr/bin/env python

"""Tests for commlib exceptions."""

import unittest

from commlib.exceptions import (
    BaseException as CommLibBaseException,
    ConnectionError,
    AMQPError,
    MQTTError,
    RedisError,
    RPCClientError,
    RPCServiceError,
    RPCRequestError,
    RPCClientTimeoutError,
    RPCServerError,
    PublisherError,
    SubscriberError,
    NodeError,
    SerializationError,
)


class TestCustomExceptions(unittest.TestCase):
    """Test custom exception classes."""

    def test_base_exception(self):
        """Test BaseException creation with message and errors."""
        msg = "Test error"
        errors = {"key": "value"}
        exc = CommLibBaseException(msg, errors)
        self.assertEqual(str(exc), msg)
        self.assertEqual(exc.errors, errors)

    def test_base_exception_no_errors(self):
        """Test BaseException without errors parameter."""
        msg = "Test error"
        exc = CommLibBaseException(msg)
        self.assertIsNone(exc.errors)

    def test_connection_error(self):
        """Test ConnectionError."""
        msg = "Connection failed"
        errors = {"reason": "timeout"}
        exc = ConnectionError(msg, errors)
        self.assertEqual(str(exc), msg)
        self.assertEqual(exc.errors, errors)

    def test_amqp_error(self):
        """Test AMQPError."""
        msg = "AMQP connection failed"
        exc = AMQPError(msg)
        self.assertEqual(str(exc), msg)

    def test_mqtt_error(self):
        """Test MQTTError."""
        msg = "MQTT publish failed"
        exc = MQTTError(msg)
        self.assertEqual(str(exc), msg)

    def test_redis_error(self):
        """Test RedisError."""
        msg = "Redis operation failed"
        exc = RedisError(msg)
        self.assertEqual(str(exc), msg)

    def test_rpc_client_error(self):
        """Test RPCClientError."""
        msg = "RPC call failed"
        exc = RPCClientError(msg)
        # Standard Exception keeps args as tuple
        self.assertEqual(exc.args, (msg, None))

    def test_rpc_service_error(self):
        """Test RPCServiceError."""
        msg = "RPC service error"
        exc = RPCServiceError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_rpc_request_error(self):
        """Test RPCRequestError."""
        msg = "Invalid RPC request"
        exc = RPCRequestError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_rpc_client_timeout_error(self):
        """Test RPCClientTimeoutError."""
        msg = "RPC request timeout"
        exc = RPCClientTimeoutError(msg)
        self.assertEqual(exc.args, (msg, None))
        self.assertIsInstance(exc, RPCClientError)

    def test_rpc_server_error(self):
        """Test RPCServerError."""
        msg = "RPC server error"
        exc = RPCServerError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_publisher_error(self):
        """Test PublisherError."""
        msg = "Publisher error"
        exc = PublisherError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_subscriber_error(self):
        """Test SubscriberError."""
        msg = "Subscriber error"
        exc = SubscriberError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_node_error(self):
        """Test NodeError."""
        msg = "Node error"
        exc = NodeError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_serialization_error(self):
        """Test SerializationError."""
        msg = "Serialization failed"
        exc = SerializationError(msg)
        self.assertEqual(exc.args, (msg, None))

    def test_exception_inheritance(self):
        """Test exception hierarchy."""
        exc = RPCClientTimeoutError("timeout")
        self.assertIsInstance(exc, RPCClientError)
        self.assertIsInstance(exc, Exception)


if __name__ == '__main__':
    unittest.main()
