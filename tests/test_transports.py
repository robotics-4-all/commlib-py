#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for transport initialization."""

import unittest
from enum import Enum

from commlib.transports import TransportType, connection_params_for_transport


class TestTransportType(unittest.TestCase):
    """Test TransportType enum."""

    def test_transport_types_is_enum(self):
        """Test that TransportType is an Enum."""
        self.assertTrue(isinstance(TransportType.AMQP, Enum))

    def test_transport_types_exist(self):
        """Test that transport types are defined."""
        self.assertTrue(hasattr(TransportType, "REDIS"))
        self.assertTrue(hasattr(TransportType, "AMQP"))
        self.assertTrue(hasattr(TransportType, "MQTT"))
        self.assertTrue(hasattr(TransportType, "KAFKA"))

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


class TestConnectionParamsForTransport(unittest.TestCase):
    """Test connection_params_for_transport function."""

    def test_mqtt_connection_params(self):
        """Test that MQTT transport returns correct ConnectionParameters class."""
        from commlib.transports.mqtt import ConnectionParameters as MQTTParams

        result = connection_params_for_transport(TransportType.MQTT)
        self.assertEqual(result, MQTTParams)

    def test_redis_connection_params(self):
        """Test that REDIS transport returns correct ConnectionParameters class."""
        from commlib.transports.redis import ConnectionParameters as RedisParams

        result = connection_params_for_transport(TransportType.REDIS)
        self.assertEqual(result, RedisParams)

    def test_amqp_connection_params(self):
        """Test that AMQP transport returns correct ConnectionParameters class."""
        from commlib.transports.amqp import ConnectionParameters as AMQPParams

        result = connection_params_for_transport(TransportType.AMQP)
        self.assertEqual(result, AMQPParams)

    def test_kafka_connection_params(self):
        """Test that KAFKA transport returns correct ConnectionParameters class."""
        from commlib.transports.kafka import ConnectionParameters as KafkaParams

        result = connection_params_for_transport(TransportType.KAFKA)
        self.assertEqual(result, KafkaParams)

    def test_connection_params_returns_callable(self):
        """Test that returned values are callable classes."""
        for transport_type in TransportType:
            result = connection_params_for_transport(transport_type)
            self.assertTrue(callable(result))
            self.assertTrue(isinstance(result, type))


if __name__ == "__main__":
    unittest.main()
