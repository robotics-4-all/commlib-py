#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for bridges module."""
# pylint: disable=protected-access

import unittest
from unittest.mock import Mock, patch

from commlib.bridges import Bridge, RPCBridge, TopicBridge, PTopicBridge
from commlib.bridges import RPCBridgeType, TopicBridgeType
from commlib.transports.mock import ConnectionParameters


class TestBridgeEnums(unittest.TestCase):
    """Test bridge type enums."""

    def test_rpc_bridge_type_values(self):
        """Test RPCBridgeType enum values."""
        self.assertEqual(RPCBridgeType.REDIS_TO_AMQP.value, 1)
        self.assertEqual(RPCBridgeType.AMQP_TO_REDIS.value, 2)
        self.assertEqual(RPCBridgeType.MQTT_TO_REDIS.value, 5)

    def test_topic_bridge_type_values(self):
        """Test TopicBridgeType enum values."""
        self.assertEqual(TopicBridgeType.REDIS_TO_AMQP.value, 1)
        self.assertEqual(TopicBridgeType.AMQP_TO_REDIS.value, 2)
        self.assertEqual(TopicBridgeType.MQTT_TO_MQTT.value, 7)


class TestBridgeBaseClass(unittest.TestCase):
    """Test Bridge base class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock connection parameters with redis and amqp types
        self.redis_params = Mock(spec=ConnectionParameters)
        self.redis_params.host = "redis_host"
        self.redis_params.port = 6379
        # Make type string contain 'redis'
        type(self.redis_params).__module__ = "commlib.transports.redis"
        type(self.redis_params).__name__ = "ConnectionParameters"

        self.amqp_params = Mock(spec=ConnectionParameters)
        self.amqp_params.host = "amqp_host"
        self.amqp_params.port = 5672
        type(self.amqp_params).__module__ = "commlib.transports.amqp"
        type(self.amqp_params).__name__ = "ConnectionParameters"

    def test_bridge_logger(self):
        """Test that Bridge has logger classmethod."""
        logger = Bridge.logger()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "commlib.bridges")

    def test_bridge_init_redis_to_amqp(self):
        """Test Bridge initialization for REDIS to AMQP."""
        bridge = Bridge(
            from_uri="test/rpc",
            to_uri="test.rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
            auto_transform_uris=False,
        )

        self.assertEqual(bridge._from_uri, "test/rpc")
        self.assertEqual(bridge._to_uri, "test.rpc")
        self.assertEqual(bridge._btype, RPCBridgeType.REDIS_TO_AMQP)

    def test_bridge_init_amqp_to_redis(self):
        """Test Bridge initialization for AMQP to REDIS."""
        bridge = Bridge(
            from_uri="test.rpc",
            to_uri="test/rpc",
            from_broker_params=self.amqp_params,
            to_broker_params=self.redis_params,
            auto_transform_uris=False,
        )

        self.assertEqual(bridge._btype, RPCBridgeType.AMQP_TO_REDIS)

    def test_bridge_debug_property(self):
        """Test Bridge debug property."""
        bridge = Bridge(
            from_uri="test",
            to_uri="test",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
            debug=True,
        )

        self.assertTrue(bridge.debug)

    def test_bridge_log_property(self):
        """Test Bridge log property returns logger."""
        bridge = Bridge(
            from_uri="test",
            to_uri="test",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )

        self.assertIsNotNone(bridge.log)

    def test_bridge_run_not_implemented(self):
        """Test that Bridge.run() raises NotImplementedError."""
        bridge = Bridge(
            from_uri="test",
            to_uri="test",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )

        with self.assertRaises(NotImplementedError):
            bridge.run()

    def test_transform_uri_redis_to_amqp(self):
        """Test URI transformation for REDIS to AMQP (/ to .)."""
        bridge = Bridge(
            from_uri="test/rpc/service",
            to_uri="test/rpc/service",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
            auto_transform_uris=True,
        )

        # Should transform / to .
        self.assertEqual(bridge._to_uri, "test.rpc.service")

    def test_transform_uri_amqp_to_redis(self):
        """Test URI transformation for AMQP to REDIS (no change)."""
        bridge = Bridge(
            from_uri="test.rpc.service",
            to_uri="test.rpc.service",
            from_broker_params=self.amqp_params,
            to_broker_params=self.redis_params,
            auto_transform_uris=True,
        )

        # Should not transform
        self.assertEqual(bridge._to_uri, "test.rpc.service")

    def test_transform_uri_disabled(self):
        """Test that auto_transform_uris=False prevents transformation."""
        bridge = Bridge(
            from_uri="test/rpc",
            to_uri="test/rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
            auto_transform_uris=False,
        )

        # Should not transform
        self.assertEqual(bridge._to_uri, "test/rpc")


class TestRPCBridge(unittest.TestCase):
    """Test RPCBridge class."""

    def setUp(self):
        """Set up test fixtures."""
        self.redis_params = Mock(spec=ConnectionParameters)
        self.redis_params.host = "localhost"
        self.redis_params.port = 6379
        type(self.redis_params).__module__ = "commlib.transports.redis"
        type(self.redis_params).__name__ = "ConnectionParameters"

        self.amqp_params = Mock(spec=ConnectionParameters)
        self.amqp_params.host = "localhost"
        self.amqp_params.port = 5672
        type(self.amqp_params).__module__ = "commlib.transports.amqp"
        type(self.amqp_params).__name__ = "ConnectionParameters"

    @patch("commlib.bridges.endpoint_factory")
    def test_rpc_bridge_init(self, mock_factory):
        """Test RPCBridge initialization creates server and client."""
        mock_server = Mock()
        mock_client = Mock()
        mock_factory.return_value.return_value = Mock()
        mock_factory.return_value.side_effect = [mock_server, mock_client]

        _bridge = RPCBridge(
            from_uri="test.rpc",
            to_uri="test.rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
            msg_type=None,
        )

        # Verify endpoints were created
        self.assertEqual(mock_factory.call_count, 2)

    @patch("commlib.bridges.endpoint_factory")
    def test_rpc_bridge_on_request(self, mock_factory):
        """Test RPCBridge on_request forwards to client."""
        mock_server = Mock()
        mock_client = Mock()
        mock_client.call = Mock(return_value={"result": "success"})

        def factory_side_effect(*args, **_kwargs):
            Mock()
            if "RPCService" in str(args):
                return lambda **kw: mock_server
            else:
                return lambda **kw: mock_client

        mock_factory.side_effect = factory_side_effect

        bridge = RPCBridge(
            from_uri="test.rpc",
            to_uri="test.rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._client = mock_client

        # Call on_request
        request = {"data": "test"}
        response = bridge.on_request(request)

        # Verify client.call was invoked
        mock_client.call.assert_called_once_with(request)
        self.assertEqual(response, {"result": "success"})

    @patch("commlib.bridges.endpoint_factory")
    def test_rpc_bridge_run(self, mock_factory):
        """Test RPCBridge run starts server and client."""
        mock_server = Mock()
        mock_client = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = RPCBridge(
            from_uri="test.rpc",
            to_uri="test.rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._server = mock_server
        bridge._client = mock_client

        bridge.run()

        # Verify both endpoints started
        mock_server.run.assert_called_once()
        mock_client.run.assert_called_once()

    @patch("commlib.bridges.endpoint_factory")
    def test_rpc_bridge_stop(self, mock_factory):
        """Test RPCBridge stop stops server and client."""
        mock_server = Mock()
        mock_client = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = RPCBridge(
            from_uri="test.rpc",
            to_uri="test.rpc",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._server = mock_server
        bridge._client = mock_client

        bridge.stop()

        # Verify both endpoints stopped
        mock_server.stop.assert_called_once()
        mock_client.stop.assert_called_once()


class TestTopicBridge(unittest.TestCase):
    """Test TopicBridge class."""

    def setUp(self):
        """Set up test fixtures."""
        self.redis_params = Mock(spec=ConnectionParameters)
        self.redis_params.host = "localhost"
        self.redis_params.port = 6379
        type(self.redis_params).__module__ = "commlib.transports.redis"
        type(self.redis_params).__name__ = "ConnectionParameters"

        self.amqp_params = Mock(spec=ConnectionParameters)
        self.amqp_params.host = "localhost"
        self.amqp_params.port = 5672
        type(self.amqp_params).__module__ = "commlib.transports.amqp"
        type(self.amqp_params).__name__ = "ConnectionParameters"

    @patch("commlib.bridges.endpoint_factory")
    def test_topic_bridge_init(self, mock_factory):
        """Test TopicBridge initialization creates subscriber and publisher."""
        mock_factory.return_value = lambda **kw: Mock()

        _bridge = TopicBridge(
            from_uri="test/topic",
            to_uri="test.topic",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )

        # Verify endpoints were created
        self.assertEqual(mock_factory.call_count, 2)

    @patch("commlib.bridges.endpoint_factory")
    def test_topic_bridge_on_message(self, mock_factory):
        """Test TopicBridge on_message publishes to destination."""
        mock_sub = Mock()
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = TopicBridge(
            from_uri="test/topic",
            to_uri="test.topic",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._sub = mock_sub
        bridge._pub = mock_pub

        # Call on_message
        msg = {"data": "test_message"}
        bridge.on_message(msg)

        # Verify publisher was called
        mock_pub.publish.assert_called_once_with(msg)

    @patch("commlib.bridges.endpoint_factory")
    def test_topic_bridge_run(self, mock_factory):
        """Test TopicBridge run starts subscriber and publisher."""
        mock_sub = Mock()
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = TopicBridge(
            from_uri="test/topic",
            to_uri="test.topic",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._sub = mock_sub
        bridge._pub = mock_pub

        bridge.run()

        # Verify both endpoints started
        mock_sub.run.assert_called_once()
        mock_pub.run.assert_called_once()

    @patch("commlib.bridges.endpoint_factory")
    def test_topic_bridge_stop(self, mock_factory):
        """Test TopicBridge stop stops subscriber and publisher."""
        mock_sub = Mock()
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = TopicBridge(
            from_uri="test/topic",
            to_uri="test.topic",
            from_broker_params=self.redis_params,
            to_broker_params=self.amqp_params,
        )
        bridge._sub = mock_sub
        bridge._pub = mock_pub

        bridge.stop()

        # Verify both endpoints stopped
        mock_sub.stop.assert_called_once()
        mock_pub.stop.assert_called_once()


class TestPTopicBridge(unittest.TestCase):
    """Test PTopicBridge class."""

    def setUp(self):
        """Set up test fixtures."""
        self.redis_params = Mock(spec=ConnectionParameters)
        self.redis_params.host = "localhost"
        self.redis_params.port = 6379
        type(self.redis_params).__module__ = "commlib.transports.redis"
        type(self.redis_params).__name__ = "ConnectionParameters"

        self.mqtt_params = Mock(spec=ConnectionParameters)
        self.mqtt_params.host = "localhost"
        self.mqtt_params.port = 1883
        type(self.mqtt_params).__module__ = "commlib.transports.mqtt"
        type(self.mqtt_params).__name__ = "ConnectionParameters"

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_init(self, mock_factory):
        """Test PTopicBridge initialization."""
        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="test/*",
            to_uri="dest",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
        )

        # Verify pattern subscriber and multi-publisher created
        self.assertEqual(mock_factory.call_count, 2)
        self.assertEqual(bridge._btype, TopicBridgeType.MQTT_TO_REDIS)

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_on_message_with_prefix(self, mock_factory):
        """Test PTopicBridge on_message with to_uri prefix."""
        mock_sub = Mock()
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="source/*",
            to_uri="dest",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
            auto_transform_uris=False,
        )
        bridge._sub = mock_sub
        bridge._pub = mock_pub

        # Call on_message with topic
        msg = {"data": "test"}
        topic = "matched/topic"
        bridge.on_message(msg, topic)

        # Verify publish with prefixed topic
        mock_pub.publish.assert_called_once()
        call_args = mock_pub.publish.call_args
        self.assertEqual(call_args[0][0], msg)
        self.assertEqual(call_args[0][1], "dest.matched/topic")

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_on_message_empty_prefix(self, mock_factory):
        """Test PTopicBridge on_message with empty to_uri."""
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="source/*",
            to_uri="",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
            auto_transform_uris=False,
        )
        bridge._pub = mock_pub

        msg = {"data": "test"}
        topic = "test/topic"
        bridge.on_message(msg, topic)

        # Should use original topic
        call_args = mock_pub.publish.call_args
        self.assertEqual(call_args[0][1], "test/topic")

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_uri_transform(self, mock_factory):
        """Test PTopicBridge with uri_transform list."""
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="source/*",
            to_uri="dest",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
            uri_transform=[("old", "new"), ("test", "prod")],
            auto_transform_uris=False,
        )
        bridge._pub = mock_pub

        msg = {"data": "test"}
        topic = "old/test/topic"
        bridge.on_message(msg, topic)

        # Verify transforms applied
        call_args = mock_pub.publish.call_args
        # Should be: dest.old/test/topic -> dest.new/prod/topic
        published_topic = call_args[0][1]
        self.assertIn("new", published_topic)
        self.assertIn("prod", published_topic)

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_run(self, mock_factory):
        """Test PTopicBridge run starts subscriber."""
        mock_sub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="test/*",
            to_uri="dest",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
        )
        bridge._sub = mock_sub

        bridge.run()

        # Verify subscriber started
        mock_sub.run.assert_called_once()

    @patch("commlib.bridges.endpoint_factory")
    def test_ptopic_bridge_stop(self, mock_factory):
        """Test PTopicBridge stop stops subscriber and publisher."""
        mock_sub = Mock()
        mock_pub = Mock()

        mock_factory.return_value = lambda **kw: Mock()

        bridge = PTopicBridge(
            from_uri="test/*",
            to_uri="dest",
            from_broker_params=self.mqtt_params,
            to_broker_params=self.redis_params,
        )
        bridge._sub = mock_sub
        bridge._pub = mock_pub

        bridge.stop()

        # Verify both stopped
        mock_sub.stop.assert_called_once()
        mock_pub.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
