"""Tests for topic conversion utilities.

Tests conversion between different protocol topic notations:
- MQTT format: a/b/c with +/# wildcards
- Redis format: a.b.c with * wildcards
- AMQP format: a.b.c with * and # wildcards
- Kafka format: a-b-c with flat names
- Commlib unified: a.b.c with * wildcards
"""

import pytest

from commlib.utils import (
    convert_topic_notation,
    topic_from_amqp,
    topic_from_kafka,
    topic_from_mqtt,
    topic_from_redis,
    topic_to_amqp,
    topic_to_kafka,
    topic_to_mqtt,
    topic_to_redis,
)


class TestTopicToMQTT:
    """Test conversion from commlib unified notation to MQTT format."""

    def test_simple_topic(self):
        """Test conversion of simple topic without wildcards."""
        assert topic_to_mqtt("sensors.temperature") == "sensors/temperature"

    def test_nested_topic(self):
        """Test conversion of deeply nested topic."""
        assert topic_to_mqtt("building.floor.room.sensor") == "building/floor/room/sensor"

    def test_single_level_wildcard(self):
        """Test conversion of single-level wildcard in middle."""
        assert topic_to_mqtt("sensors.*.temperature") == "sensors/+/temperature"

    def test_multiple_single_level_wildcards(self):
        """Test conversion with multiple single-level wildcards."""
        assert topic_to_mqtt("sensors.*.data.*.value") == "sensors/+/data/+/value"

    def test_trailing_wildcard(self):
        """Test conversion of trailing wildcard (multi-level)."""
        assert topic_to_mqtt("sensors.*") == "sensors/#"

    def test_only_wildcard(self):
        """Test conversion of just wildcard."""
        assert topic_to_mqtt("*") == "+"


class TestTopicFromMQTT:
    """Test conversion from MQTT format to commlib unified notation."""

    def test_simple_topic(self):
        """Test conversion of simple MQTT topic without wildcards."""
        assert topic_from_mqtt("sensors/temperature") == "sensors.temperature"

    def test_nested_topic(self):
        """Test conversion of deeply nested MQTT topic."""
        assert topic_from_mqtt("building/floor/room/sensor") == "building.floor.room.sensor"

    def test_single_level_wildcard(self):
        """Test conversion of MQTT single-level wildcard (+)."""
        assert topic_from_mqtt("sensors/+/temperature") == "sensors.*.temperature"

    def test_multiple_single_level_wildcards(self):
        """Test conversion with multiple MQTT single-level wildcards."""
        assert topic_from_mqtt("sensors/+/data/+/value") == "sensors.*.data.*.value"

    def test_multi_level_wildcard(self):
        """Test conversion of MQTT multi-level wildcard (#)."""
        assert topic_from_mqtt("sensors/#") == "sensors.*"

    def test_only_wildcard(self):
        """Test conversion of just MQTT multi-level wildcard."""
        assert topic_from_mqtt("#") == "*"


class TestMQTTRoundTrip:
    """Test round-trip conversion between commlib and MQTT formats."""

    def test_simple_roundtrip(self):
        """Test simple topic round-trip conversion."""
        original = "sensors.temperature"
        converted = topic_to_mqtt(original)
        back = topic_from_mqtt(converted)
        assert back == original

    def test_single_wildcard_roundtrip(self):
        """Test single wildcard round-trip."""
        original = "sensors.*.temperature"
        converted = topic_to_mqtt(original)
        back = topic_from_mqtt(converted)
        assert back == original

    def test_trailing_wildcard_roundtrip(self):
        """Test trailing wildcard round-trip."""
        original = "sensors.*"
        converted = topic_to_mqtt(original)
        back = topic_from_mqtt(converted)
        assert back == original


class TestTopicToRedis:
    """Test conversion from commlib to Redis format."""

    def test_simple_topic(self):
        """Test that simple topic remains unchanged for Redis."""
        assert topic_to_redis("sensors.temperature") == "sensors.temperature"

    def test_nested_topic(self):
        """Test that nested topic remains unchanged for Redis."""
        assert topic_to_redis("building.floor.room") == "building.floor.room"

    def test_topic_with_wildcard(self):
        """Test that wildcards remain unchanged for Redis."""
        assert topic_to_redis("sensors.*.temperature") == "sensors.*.temperature"

    def test_multiple_wildcards(self):
        """Test multiple wildcards remain unchanged."""
        assert topic_to_redis("sensors.*.data.*") == "sensors.*.data.*"


class TestTopicFromRedis:
    """Test conversion from Redis format to commlib."""

    def test_simple_topic(self):
        """Test that simple Redis topic remains unchanged."""
        assert topic_from_redis("sensors.temperature") == "sensors.temperature"

    def test_topic_with_wildcard(self):
        """Test that Redis wildcards remain unchanged."""
        assert topic_from_redis("sensors.*.temperature") == "sensors.*.temperature"


class TestRedisRoundTrip:
    """Test round-trip conversion between commlib and Redis formats."""

    def test_simple_roundtrip(self):
        """Test simple topic round-trip with Redis."""
        original = "sensors.temperature"
        converted = topic_to_redis(original)
        back = topic_from_redis(converted)
        assert back == original

    def test_wildcard_roundtrip(self):
        """Test wildcard round-trip with Redis."""
        original = "sensors.*.data.*"
        converted = topic_to_redis(original)
        back = topic_from_redis(converted)
        assert back == original


class TestTopicToKafka:
    """Test conversion from commlib to Kafka format."""

    def test_simple_topic(self):
        """Test conversion to flat Kafka topic name."""
        assert topic_to_kafka("sensors.temperature") == "sensors-temperature"

    def test_nested_topic(self):
        """Test conversion of deeply nested topic to Kafka."""
        assert topic_to_kafka("building.floor.room.sensor") == "building-floor-room-sensor"

    def test_topic_with_wildcard(self):
        """Test that wildcards are preserved in Kafka format."""
        assert topic_to_kafka("sensors.*.temperature") == "sensors-*-temperature"

    def test_multiple_wildcards(self):
        """Test multiple wildcards in Kafka format."""
        assert topic_to_kafka("sensors.*.data.*") == "sensors-*-data-*"


class TestTopicFromKafka:
    """Test conversion from Kafka format to commlib."""

    def test_simple_topic(self):
        """Test conversion from flat Kafka topic to commlib."""
        assert topic_from_kafka("sensors-temperature") == "sensors.temperature"

    def test_nested_topic(self):
        """Test conversion of nested Kafka topic."""
        assert topic_from_kafka("building-floor-room-sensor") == "building.floor.room.sensor"

    def test_topic_with_wildcard(self):
        """Test that Kafka wildcards convert back to commlib."""
        assert topic_from_kafka("sensors-*-temperature") == "sensors.*.temperature"

    def test_multiple_wildcards(self):
        """Test multiple Kafka wildcards convert back."""
        assert topic_from_kafka("sensors-*-data-*") == "sensors.*.data.*"


class TestKafkaRoundTrip:
    """Test round-trip conversion between commlib and Kafka formats."""

    def test_simple_roundtrip(self):
        """Test simple topic round-trip with Kafka."""
        original = "sensors.temperature"
        converted = topic_to_kafka(original)
        back = topic_from_kafka(converted)
        assert back == original

    def test_wildcard_roundtrip(self):
        """Test wildcard round-trip with Kafka."""
        original = "sensors.*.data.*"
        converted = topic_to_kafka(original)
        back = topic_from_kafka(converted)
        assert back == original


class TestTopicToAMQP:
    """Test conversion from commlib to AMQP format."""

    def test_simple_topic(self):
        """Test that AMQP topic remains unchanged (dot notation)."""
        assert topic_to_amqp("sensors.temperature") == "sensors.temperature"

    def test_topic_with_wildcard(self):
        """Test that AMQP wildcards remain unchanged."""
        assert topic_to_amqp("sensors.*.temperature") == "sensors.*.temperature"


class TestTopicFromAMQP:
    """Test conversion from AMQP format to commlib."""

    def test_simple_topic(self):
        """Test that AMQP topic remains unchanged."""
        assert topic_from_amqp("sensors.temperature") == "sensors.temperature"

    def test_topic_with_wildcard(self):
        """Test that AMQP wildcards remain unchanged."""
        assert topic_from_amqp("sensors.*.temperature") == "sensors.*.temperature"


class TestAMQPRoundTrip:
    """Test round-trip conversion between commlib and AMQP formats."""

    def test_simple_roundtrip(self):
        """Test simple topic round-trip with AMQP."""
        original = "sensors.temperature"
        converted = topic_to_amqp(original)
        back = topic_from_amqp(converted)
        assert back == original

    def test_wildcard_roundtrip(self):
        """Test wildcard round-trip with AMQP."""
        original = "sensors.*.temperature"
        converted = topic_to_amqp(original)
        back = topic_from_amqp(converted)
        assert back == original


class TestConvertTopicNotation:
    """Test the unified topic conversion function."""

    def test_mqtt_to_commlib(self):
        """Test MQTT to commlib conversion."""
        result = convert_topic_notation("sensors/+/temperature", "mqtt", "commlib")
        assert result == "sensors.*.temperature"

    def test_commlib_to_mqtt(self):
        """Test commlib to MQTT conversion."""
        result = convert_topic_notation("sensors.*.temperature", "commlib", "mqtt")
        assert result == "sensors/+/temperature"

    def test_redis_to_mqtt(self):
        """Test Redis to MQTT conversion."""
        result = convert_topic_notation("sensors.temperature", "redis", "mqtt")
        assert result == "sensors/temperature"

    def test_mqtt_to_redis(self):
        """Test MQTT to Redis conversion."""
        result = convert_topic_notation("sensors/temperature", "mqtt", "redis")
        assert result == "sensors.temperature"

    def test_commlib_to_kafka(self):
        """Test commlib to Kafka conversion."""
        result = convert_topic_notation("sensors.temperature", "commlib", "kafka")
        assert result == "sensors-temperature"

    def test_kafka_to_commlib(self):
        """Test Kafka to commlib conversion."""
        result = convert_topic_notation("sensors-temperature", "kafka", "commlib")
        assert result == "sensors.temperature"

    def test_kafka_to_mqtt(self):
        """Test Kafka to MQTT conversion."""
        result = convert_topic_notation("sensors-temperature", "kafka", "mqtt")
        assert result == "sensors/temperature"

    def test_mqtt_to_kafka(self):
        """Test MQTT to Kafka conversion."""
        result = convert_topic_notation("sensors/temperature", "mqtt", "kafka")
        assert result == "sensors-temperature"

    def test_commlib_to_amqp(self):
        """Test commlib to AMQP conversion."""
        result = convert_topic_notation("sensors.temperature", "commlib", "amqp")
        assert result == "sensors.temperature"

    def test_amqp_to_mqtt(self):
        """Test AMQP to MQTT conversion."""
        result = convert_topic_notation("sensors.*.temperature", "amqp", "mqtt")
        assert result == "sensors/+/temperature"

    def test_same_protocol_no_conversion(self):
        """Test that same protocol returns topic unchanged."""
        topic = "sensors.*.temperature"
        result = convert_topic_notation(topic, "commlib", "commlib")
        assert result == topic

    def test_complex_topic_mqtt_to_commlib(self):
        """Test complex topic conversion from MQTT."""
        result = convert_topic_notation("building/+/floor/+/room/+/sensor/#", "mqtt", "commlib")
        assert result == "building.*.floor.*.room.*.sensor.*"

    def test_complex_topic_commlib_to_kafka(self):
        """Test complex topic conversion to Kafka."""
        result = convert_topic_notation(
            "building.floor.room.sensor.temperature", "commlib", "kafka"
        )
        assert result == "building-floor-room-sensor-temperature"


class TestConvertTopicNotationErrors:
    """Test error handling in topic conversion."""

    def test_invalid_source_protocol(self):
        """Test that invalid source protocol raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported source protocol"):
            convert_topic_notation("sensors.temperature", "invalid", "mqtt")

    def test_invalid_target_protocol(self):
        """Test that invalid target protocol raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported target protocol"):
            convert_topic_notation("sensors.temperature", "mqtt", "invalid")

    def test_both_protocols_invalid(self):
        """Test that both invalid protocols raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported source protocol"):
            convert_topic_notation("sensors.temperature", "bad1", "bad2")


class TestTopicConversionEdgeCases:
    """Test edge cases in topic conversion."""

    def test_empty_segments_mqtt(self):
        """Test MQTT format with multiple slashes."""
        # This is technically invalid but should not crash
        result = topic_from_mqtt("sensors//temperature")
        assert result == "sensors..temperature"

    def test_wildcard_only_commlib(self):
        """Test topic that is just a wildcard."""
        result = topic_to_mqtt("*")
        assert result == "+"

    def test_single_segment(self):
        """Test single segment topic."""
        assert topic_to_mqtt("sensors") == "sensors"
        assert topic_from_mqtt("sensors") == "sensors"

    def test_trailing_dot_commlib(self):
        """Test topic with trailing dot."""
        result = topic_to_mqtt("sensors.")
        assert "/" in result

    def test_leading_dot_commlib(self):
        """Test topic with leading dot."""
        result = topic_to_mqtt(".sensors")
        assert result.startswith("/")


class TestTopicConversionRealWorldScenarios:
    """Test real-world topic conversion scenarios."""

    def test_iot_sensor_hierarchy_mqtt_to_commlib(self):
        """Test IoT sensor hierarchy conversion from MQTT."""
        mqtt_topic = "home/+/sensors/+/temperature"
        result = convert_topic_notation(mqtt_topic, "mqtt", "commlib")
        assert result == "home.*.sensors.*.temperature"

    def test_iot_sensor_hierarchy_commlib_to_kafka(self):
        """Test IoT sensor hierarchy conversion to Kafka."""
        commlib_topic = "home.*.sensors.*.temperature"
        result = convert_topic_notation(commlib_topic, "commlib", "kafka")
        assert result == "home-*-sensors-*-temperature"

    def test_event_stream_mqtt_to_redis(self):
        """Test event stream topic conversion from MQTT to Redis."""
        mqtt_topic = "events/system/+/logs"
        result = convert_topic_notation(mqtt_topic, "mqtt", "redis")
        assert result == "events.system.*.logs"

    def test_rpc_namespace_mqtt_format(self):
        """Test RPC namespace in MQTT format."""
        mqtt_topic = "rpc/+/request"
        result = convert_topic_notation(mqtt_topic, "mqtt", "commlib")
        assert result == "rpc.*.request"

    def test_wildcard_everything_mqtt(self):
        """Test MQTT topic matching everything."""
        mqtt_topic = "#"
        result = convert_topic_notation(mqtt_topic, "mqtt", "commlib")
        assert result == "*"

    def test_specific_path_wildcard_end(self):
        """Test specific path with wildcard at end."""
        commlib_topic = "building.floor1.rooms.*"
        mqtt_result = convert_topic_notation(commlib_topic, "commlib", "mqtt")
        assert mqtt_result == "building/floor1/rooms/#"
        
        kafka_result = convert_topic_notation(commlib_topic, "commlib", "kafka")
        assert kafka_result == "building-floor1-rooms-*"
