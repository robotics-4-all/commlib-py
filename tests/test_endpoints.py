#!/usr/bin/env python

"""Tests for commlib endpoints module."""

import unittest
from enum import Enum

from commlib.endpoints import EndpointState, BaseEndpoint
from commlib.compression import CompressionType
from commlib.serializer import JSONSerializer
from commlib.transports.mock import ConnectionParameters


class TestEndpointState(unittest.TestCase):
    """Test EndpointState enum."""

    def test_endpoint_state_values(self):
        """Test EndpointState enum values."""
        self.assertEqual(EndpointState.DISCONNECTED.value, 0)
        self.assertEqual(EndpointState.CONNECTED.value, 1)
        self.assertEqual(EndpointState.CONNECTING.value, 2)
        self.assertEqual(EndpointState.DISCONNECTING.value, 3)

    def test_endpoint_state_is_enum(self):
        """Test EndpointState is an Enum."""
        self.assertIsInstance(EndpointState.CONNECTED, Enum)

    def test_endpoint_state_members(self):
        """Test EndpointState has all expected members."""
        members = list(EndpointState)
        self.assertEqual(len(members), 4)
        self.assertIn(EndpointState.DISCONNECTED, members)
        self.assertIn(EndpointState.CONNECTED, members)
        self.assertIn(EndpointState.CONNECTING, members)
        self.assertIn(EndpointState.DISCONNECTING, members)


class TestBaseEndpoint(unittest.TestCase):
    """Test BaseEndpoint class."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(host="test", port="1234")

    def test_base_endpoint_creation(self):
        """Test BaseEndpoint creation."""
        endpoint = BaseEndpoint(
            debug=False,
            serializer=JSONSerializer,
            conn_params=self.conn_params,
            compression=CompressionType.NO_COMPRESSION
        )
        self.assertIsNotNone(endpoint)
        self.assertFalse(endpoint.debug)
        self.assertEqual(endpoint._serializer, JSONSerializer)
        self.assertEqual(endpoint._compression, CompressionType.NO_COMPRESSION)

    def test_base_endpoint_debug_mode(self):
        """Test BaseEndpoint with debug enabled."""
        endpoint = BaseEndpoint(debug=True)
        self.assertTrue(endpoint.debug)

    def test_base_endpoint_compression_types(self):
        """Test BaseEndpoint with different compression types."""
        for comp_type in [
            CompressionType.NO_COMPRESSION,
            CompressionType.BEST_SPEED,
            CompressionType.BEST_COMPRESSION,
            CompressionType.DEFAULT_COMPRESSION,
        ]:
            endpoint = BaseEndpoint(compression=comp_type)
            self.assertEqual(endpoint._compression, comp_type)

    def test_base_endpoint_logger(self):
        """Test BaseEndpoint logger."""
        logger = BaseEndpoint.logger()
        self.assertIsNotNone(logger)
        # Logger should be a logging.Logger instance
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'debug'))
        self.assertTrue(hasattr(logger, 'warning'))
        self.assertTrue(hasattr(logger, 'error'))

    def test_base_endpoint_logger_singleton(self):
        """Test that logger is singleton."""
        logger1 = BaseEndpoint.logger()
        logger2 = BaseEndpoint.logger()
        self.assertIs(logger1, logger2)

    def test_base_endpoint_with_connection_params(self):
        """Test BaseEndpoint with connection parameters."""
        endpoint = BaseEndpoint(conn_params=self.conn_params)
        self.assertIsNotNone(endpoint._conn_params)

    def test_base_endpoint_default_values(self):
        """Test BaseEndpoint default values."""
        endpoint = BaseEndpoint()
        self.assertFalse(endpoint.debug)
        self.assertEqual(endpoint._compression, CompressionType.NO_COMPRESSION)
        self.assertEqual(endpoint._serializer, JSONSerializer)


if __name__ == '__main__':
    unittest.main()
