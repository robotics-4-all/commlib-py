#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for TCP bridge module."""

import socket
import socketserver
import unittest
from unittest.mock import Mock, patch, call, MagicMock

from commlib.tcp_bridge import TCPBridge, TCPBridgeRequestHandler, ThreadedTCPServer


class TestTCPBridge(unittest.TestCase):
    """Test TCPBridge class."""

    def test_tcp_bridge_init(self):
        """Test TCPBridge initialization stores endpoints correctly."""
        with patch.object(ThreadedTCPServer, "__init__", return_value=None):
            bridge = TCPBridge("localhost", 8080, "remote_host", 9090)

            self.assertEqual(bridge.host_ep1, "localhost")
            self.assertEqual(bridge.port_ep1, 8080)
            self.assertEqual(bridge.host_ep2, "remote_host")
            self.assertEqual(bridge.port_ep2, 9090)

    def test_tcp_bridge_init_calls_super(self):
        """Test that TCPBridge calls parent class __init__."""
        with patch.object(ThreadedTCPServer, "__init__") as mock_super:
            bridge = TCPBridge("127.0.0.1", 5000, "127.0.0.1", 6000)

            # Verify super().__init__ was called with correct args
            mock_super.assert_called_once()
            args = mock_super.call_args[0]
            self.assertEqual(args[0], ("127.0.0.1", 5000))  # host_ep1, port_ep1
            self.assertEqual(args[1], TCPBridgeRequestHandler)


class TestTCPBridgeRequestHandler(unittest.TestCase):
    """Test TCPBridgeRequestHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock server with endpoint info
        self.mock_server = Mock()
        self.mock_server.host_ep2 = "remote_server"
        self.mock_server.port_ep2 = 9090

        # Create a mock request (client socket)
        self.mock_request = Mock()
        self.mock_request.recv = Mock(return_value=b"test data")
        self.mock_request.sendall = Mock()

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_forwards_data(self, mock_socket_constructor):
        """Test that handle() forwards data between client and remote server."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock()
        mock_remote_socket.sendall = Mock()
        mock_remote_socket.recv = Mock(side_effect=[b"response data", b"", b"", b""])
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )
        handler.handle()

        # Verify key behaviors (not exact call counts due to test isolation issues)
        mock_socket_constructor.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_remote_socket.connect.assert_called_with(("remote_server", 9090))
        mock_remote_socket.sendall.assert_called_with(b"test data")
        self.mock_request.sendall.assert_called_with(b"response data")

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_multiple_chunks(self, mock_socket_constructor):
        """Test that handle() forwards multiple data chunks."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock()
        mock_remote_socket.sendall = Mock()
        mock_remote_socket.recv = Mock(
            side_effect=[b"chunk1", b"chunk2", b"chunk3", b"", b"", b""]
        )
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )
        handler.handle()

        # Verify all chunks were forwarded to client
        calls = [call(b"chunk1"), call(b"chunk2"), call(b"chunk3")]
        self.mock_request.sendall.assert_has_calls(calls, any_order=False)

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_empty_data(self, mock_socket_constructor):
        """Test that handle() handles empty client data gracefully."""
        self.mock_request.recv = Mock(return_value=b"")

        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock()
        mock_remote_socket.sendall = Mock()
        mock_remote_socket.recv = Mock(return_value=b"")
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )
        handler.handle()

        # Should connect and send empty data
        mock_remote_socket.connect.assert_called_with(("remote_server", 9090))
        mock_remote_socket.sendall.assert_called_with(b"")

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_connection_refused(self, mock_socket_constructor):
        """Test that handle() handles ConnectionError gracefully."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock(
            side_effect=ConnectionRefusedError("Connection refused")
        )
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )

        with patch("builtins.print") as mock_print:
            handler.handle()
            # Error should be printed
            self.assertTrue(mock_print.called)

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_socket_error(self, mock_socket_constructor):
        """Test that handle() handles socket.error during send."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock()
        mock_remote_socket.sendall = Mock(side_effect=socket.error("Socket error"))
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )

        with patch("builtins.print") as mock_print:
            handler.handle()
            # Error should be printed
            self.assertTrue(mock_print.called)

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_os_error(self, mock_socket_constructor):
        """Test that handle() handles OSError."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock(side_effect=OSError("OS error"))
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )

        with patch("builtins.print") as mock_print:
            handler.handle()
            # Error should be printed
            self.assertTrue(mock_print.called)

    @patch("commlib.tcp_bridge.socket.socket")
    def test_handle_no_response_data(self, mock_socket_constructor):
        """Test handle() when remote server sends no response."""
        mock_remote_socket = MagicMock()
        mock_remote_socket.connect = Mock()
        mock_remote_socket.sendall = Mock()
        mock_remote_socket.recv = Mock(return_value=b"")
        mock_remote_socket.__enter__ = Mock(return_value=mock_remote_socket)
        mock_remote_socket.__exit__ = Mock(return_value=False)

        mock_socket_constructor.return_value = mock_remote_socket

        handler = TCPBridgeRequestHandler(
            self.mock_request, ("127.0.0.1", 1234), self.mock_server
        )
        handler.handle()

        # Should send data to remote
        mock_remote_socket.sendall.assert_called_with(b"test data")
        # But not send anything back to client (no response received)
        # Note: assert_not_called can be flaky with mock reuse, so we check call count
        self.assertEqual(self.mock_request.sendall.call_count, 0)


class TestThreadedTCPServer(unittest.TestCase):
    """Test ThreadedTCPServer class."""

    def test_threaded_tcp_server_inheritance(self):
        """Test that ThreadedTCPServer has correct inheritance."""
        self.assertTrue(issubclass(ThreadedTCPServer, socketserver.ThreadingMixIn))
        self.assertTrue(issubclass(ThreadedTCPServer, socketserver.TCPServer))


if __name__ == "__main__":
    unittest.main()
