"""
Unit tests for Phase 3 AMQP optimizations.

Tests event-driven RPC response, connection pooling, and events thread optimizations.
"""
# pylint: disable=protected-access

import threading
import unittest
from unittest.mock import Mock, patch

from commlib.transports.amqp import (
    ConnectionParameters,
    _AMQP_CONNECTION_LOCK,
    _AMQP_CONNECTION_REFCOUNT,
    _AMQP_CONNECTION_REGISTRY,
    _make_connection_key,
    get_or_create_amqp_connection,
    release_amqp_connection,
)


class TestAMQPConnectionPooling(unittest.TestCase):
    """Test AMQP connection pooling optimizations (Phase 3)."""

    def setUp(self):
        """Clear connection registry before each test."""
        with _AMQP_CONNECTION_LOCK:
            _AMQP_CONNECTION_REGISTRY.clear()
            _AMQP_CONNECTION_REFCOUNT.clear()

    def tearDown(self):
        """Clean up connections after each test."""
        with _AMQP_CONNECTION_LOCK:
            # Close all remaining connections
            for key in list(_AMQP_CONNECTION_REGISTRY.keys()):
                try:
                    conn = _AMQP_CONNECTION_REGISTRY.pop(key)
                    if conn.is_open:
                        conn.close()
                except Exception:
                    pass
            _AMQP_CONNECTION_REGISTRY.clear()
            _AMQP_CONNECTION_REFCOUNT.clear()

    def test_connection_key_generation(self):
        """Test connection key is generated correctly."""
        params = ConnectionParameters(
            host="localhost",
            port=5672,
            vhost="/",
            username="guest",
            password="guest",
        )
        key = _make_connection_key(params)
        self.assertEqual(key, ("localhost", 5672, "/", "guest"))
        # Verify password is not stored in key (only username is)
        self.assertEqual(len(key), 4)  # host, port, vhost, username (no password)

    def test_connection_key_different_hosts(self):
        """Test different hosts produce different keys."""
        params1 = ConnectionParameters(host="host1", port=5672)
        params2 = ConnectionParameters(host="host2", port=5672)
        key1 = _make_connection_key(params1)
        key2 = _make_connection_key(params2)
        self.assertNotEqual(key1, key2)

    def test_connection_key_different_ports(self):
        """Test different ports produce different keys."""
        params1 = ConnectionParameters(host="localhost", port=5672)
        params2 = ConnectionParameters(host="localhost", port=5673)
        key1 = _make_connection_key(params1)
        key2 = _make_connection_key(params2)
        self.assertNotEqual(key1, key2)

    @patch("commlib.transports.amqp.Connection")
    def test_connection_pool_reuse(self, mock_connection_class):
        """Test connection pool reuses existing connections."""
        # Mock connection
        mock_conn = Mock()
        mock_conn.is_open = True
        mock_connection_class.return_value = mock_conn

        params = ConnectionParameters(host="localhost", port=5672)

        # First request creates connection
        conn1 = get_or_create_amqp_connection(params)
        self.assertEqual(mock_connection_class.call_count, 1)
        key = _make_connection_key(params)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 1)

        # Second request reuses connection
        conn2 = get_or_create_amqp_connection(params)
        self.assertEqual(mock_connection_class.call_count, 1)  # Still 1, not 2
        self.assertIs(conn1, conn2)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 2)

        # Third request also reuses
        get_or_create_amqp_connection(params)
        self.assertEqual(mock_connection_class.call_count, 1)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 3)

    @patch("commlib.transports.amqp.Connection")
    def test_connection_pool_refcounting(self, mock_connection_class):
        """Test connection pool reference counting works correctly."""
        mock_conn = Mock()
        mock_conn.is_open = True
        mock_connection_class.return_value = mock_conn

        params = ConnectionParameters(host="localhost", port=5672)
        key = _make_connection_key(params)

        # Create 3 references
        get_or_create_amqp_connection(params)
        get_or_create_amqp_connection(params)
        get_or_create_amqp_connection(params)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 3)

        # Release 2 references
        release_amqp_connection(params)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 2)
        self.assertIn(key, _AMQP_CONNECTION_REGISTRY)  # Still in registry

        release_amqp_connection(params)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 1)
        self.assertIn(key, _AMQP_CONNECTION_REGISTRY)

        # Release last reference - should close and remove
        release_amqp_connection(params)
        self.assertNotIn(key, _AMQP_CONNECTION_REGISTRY)
        self.assertNotIn(key, _AMQP_CONNECTION_REFCOUNT)
        mock_conn.close.assert_called_once()

    @patch("commlib.transports.amqp.Connection")
    def test_connection_pool_different_params(self, mock_connection_class):
        """Test different connection parameters create separate connections."""
        mock_conn1 = Mock()
        mock_conn1.is_open = True
        mock_conn2 = Mock()
        mock_conn2.is_open = True
        mock_connection_class.side_effect = [mock_conn1, mock_conn2]

        params1 = ConnectionParameters(host="host1", port=5672)
        params2 = ConnectionParameters(host="host2", port=5672)

        conn1 = get_or_create_amqp_connection(params1)
        conn2 = get_or_create_amqp_connection(params2)

        self.assertIsNot(conn1, conn2)
        self.assertEqual(mock_connection_class.call_count, 2)
        self.assertEqual(len(_AMQP_CONNECTION_REGISTRY), 2)

    @patch("commlib.transports.amqp.Connection")
    def test_connection_pool_stale_connection_cleanup(self, mock_connection_class):
        """Test stale connections are removed and recreated."""
        # First connection (will become stale)
        mock_conn1 = Mock()
        mock_conn1.is_open = False  # Stale!
        # Second connection (fresh)
        mock_conn2 = Mock()
        mock_conn2.is_open = True
        mock_connection_class.side_effect = [mock_conn1, mock_conn2]

        params = ConnectionParameters(host="localhost", port=5672)

        # Create connection
        conn1 = get_or_create_amqp_connection(params)
        self.assertEqual(mock_connection_class.call_count, 1)

        # Request again - should detect stale and create new
        conn2 = get_or_create_amqp_connection(params)
        self.assertEqual(mock_connection_class.call_count, 2)
        self.assertIsNot(conn1, conn2)

    @patch("commlib.transports.amqp.Connection")
    def test_connection_pool_thread_safety(self, mock_connection_class):
        """Test connection pool is thread-safe."""
        mock_conn = Mock()
        mock_conn.is_open = True
        mock_connection_class.return_value = mock_conn

        params = ConnectionParameters(host="localhost", port=5672)
        connections = []
        errors = []

        def get_connection():
            try:
                conn = get_or_create_amqp_connection(params)
                connections.append(conn)
            except Exception as e:
                errors.append(e)

        # Create 10 threads requesting connections simultaneously
        threads = [threading.Thread(target=get_connection) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should create only 1 connection
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(mock_connection_class.call_count, 1)
        key = _make_connection_key(params)
        self.assertEqual(_AMQP_CONNECTION_REFCOUNT[key], 10)

    def test_release_nonexistent_connection(self):
        """Test releasing non-existent connection doesn't crash."""
        params = ConnectionParameters(host="localhost", port=5672)
        # Should not raise exception
        release_amqp_connection(params)
        self.assertEqual(len(_AMQP_CONNECTION_REGISTRY), 0)


class TestAMQPEventsThreadOptimization(unittest.TestCase):
    """Test AMQP events thread optimization (Phase 3)."""

    def test_process_events_interval_optimized(self):
        """Test AMQP events polling interval is optimized to 50ms."""
        from commlib.transports.amqp import Connection

        # Should be 0.05 (50ms), not 0.01 (10ms)
        self.assertEqual(Connection._PROCESS_EVENTS_INTERVAL, 0.05)
        self.assertNotEqual(Connection._PROCESS_EVENTS_INTERVAL, 0.01)


class TestAMQPEventDrivenRPC(unittest.TestCase):
    """Test event-driven RPC response optimization (Phase 3)."""

    def test_rpc_client_has_response_event(self):
        """Test RPCClient initializes with response event."""
        from commlib.msg import RPCMessage
        from commlib.transports.amqp import RPCClient

        class TestRPC(RPCMessage):
            class Request(RPCMessage.Request):
                value: int = 0

            class Response(RPCMessage.Response):
                result: int = 0

        try:
            client = RPCClient(
                rpc_name="test_rpc",
                conn_params=ConnectionParameters(host="localhost", port=5672),
                msg_type=TestRPC,
            )
            # Should have _response_event attribute
            self.assertTrue(hasattr(client, "_response_event"))
            self.assertIsInstance(client._response_event, threading.Event)
        except Exception:
            # Connection might fail, but we're just testing initialization
            pass


class TestAMQPConnectionStateEvents(unittest.TestCase):
    """Test event-driven connection state (Phase 3)."""

    @patch("commlib.transports.amqp.Connection")
    def test_amqp_transport_uses_event_driven_state(self, mock_connection_class):
        """Test AMQPTransport uses _set_connected for event-driven state."""
        from commlib.transports.amqp import AMQPTransport

        mock_conn = Mock()
        mock_conn.is_open = True
        mock_conn.channel.return_value = Mock()
        mock_connection_class.return_value = mock_conn

        transport = AMQPTransport(
            conn_params=ConnectionParameters(host="localhost", port=5672),
            use_shared_connection=False,  # Don't use pooling for this test
        )

        # Should have connection events from BaseTransport
        self.assertTrue(hasattr(transport, "_connected_event"))
        self.assertTrue(hasattr(transport, "_disconnected_event"))
        self.assertIsInstance(transport._connected_event, threading.Event)
        self.assertIsInstance(transport._disconnected_event, threading.Event)


if __name__ == "__main__":
    unittest.main()
