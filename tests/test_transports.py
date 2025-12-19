#!/usr/bin/env python

"""Tests for transport initialization."""

import unittest
from enum import Enum

from commlib.transports import TransportType


class TestTransportType(unittest.TestCase):
    """Test TransportType enum."""

    def test_transport_types_is_enum(self):
        """Test that TransportType is an Enum."""
        self.assertTrue(isinstance(TransportType.AMQP, Enum))

    def test_transport_types_exist(self):
        """Test that transport types are defined."""
        self.assertTrue(hasattr(TransportType, 'REDIS'))
        self.assertTrue(hasattr(TransportType, 'AMQP'))
        self.assertTrue(hasattr(TransportType, 'MQTT'))
        self.assertTrue(hasattr(TransportType, 'KAFKA'))

    def test_amqp_transport(self):
        """Test AMQP transport type."""
        self.assertEqual(TransportType.AMQP.value, 1)

    def test_redis_transport(self):
        """Test REDIS transport type."""
        self.assertEqual(TransportType.REDIS.value, 2)

    def test_mqtt_transport(self):
        """Test MQTT transport type."""
        self.assertEqual(TransportType.MQTT.value, 3)

    def test_kafka_transport(self):
        """Test KAFKA transport type."""
        self.assertEqual(TransportType.KAFKA.value, 4)

    def test_transport_type_enum_members(self):
        """Test TransportType enum members."""
        members = list(TransportType)
        self.assertEqual(len(members), 4)
        self.assertIn(TransportType.AMQP, members)
        self.assertIn(TransportType.REDIS, members)
        self.assertIn(TransportType.MQTT, members)
        self.assertIn(TransportType.KAFKA, members)


if __name__ == '__main__':
    unittest.main()
