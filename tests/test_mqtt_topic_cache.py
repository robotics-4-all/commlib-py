"""Unit tests for MQTT topic transformation caching."""
# pylint: disable=protected-access

import unittest
from commlib.transports.mqtt import MQTTTransport


class TestMQTTTopicTransformCache(unittest.TestCase):
    """Test MQTT topic transformation caching functionality."""

    def test_transform_topic_basic(self):
        """Test basic topic transformation."""
        result = MQTTTransport._transform_topic_cached("robot.sensors.temperature")
        self.assertEqual(result, "robot/sensors/temperature")

    def test_transform_topic_trailing_wildcard(self):
        """Test transformation of trailing wildcard."""
        result = MQTTTransport._transform_topic_cached("robot.sensors.*")
        self.assertEqual(result, "robot/sensors/#")

    def test_transform_topic_single_level_wildcard(self):
        """Test transformation of single-level wildcard."""
        result = MQTTTransport._transform_topic_cached("robot.*/temperature")
        self.assertEqual(result, "robot/+/temperature")

    def test_transform_topic_mixed_wildcards(self):
        """Test transformation with mixed wildcards."""
        result = MQTTTransport._transform_topic_cached("robot.*/sensors.*")
        self.assertEqual(result, "robot/+/sensors/#")

    def test_transform_topic_caching(self):
        """Test that repeated calls use cache."""
        topic = "robot.sensors.temperature"

        # Clear cache to start fresh
        MQTTTransport._transform_topic_cached.cache_clear()
        cache_info_before = MQTTTransport._transform_topic_cached.cache_info()
        self.assertEqual(cache_info_before.hits, 0)
        self.assertEqual(cache_info_before.misses, 0)

        # First call - cache miss
        result1 = MQTTTransport._transform_topic_cached(topic)
        cache_info_after_first = MQTTTransport._transform_topic_cached.cache_info()
        self.assertEqual(cache_info_after_first.misses, 1)
        self.assertEqual(cache_info_after_first.hits, 0)

        # Second call - cache hit
        result2 = MQTTTransport._transform_topic_cached(topic)
        cache_info_after_second = MQTTTransport._transform_topic_cached.cache_info()
        self.assertEqual(cache_info_after_second.misses, 1)
        self.assertEqual(cache_info_after_second.hits, 1)

        # Results should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result1, "robot/sensors/temperature")

    def test_transform_topic_cache_size(self):
        """Test cache eviction with maxsize=512."""
        # Clear cache
        MQTTTransport._transform_topic_cached.cache_clear()

        # Generate 600 unique topics (more than cache size of 512)
        topics = [f"robot.sensor{i}.data" for i in range(600)]

        # Transform all topics
        for topic in topics:
            MQTTTransport._transform_topic_cached(topic)

        cache_info = MQTTTransport._transform_topic_cached.cache_info()

        # We should have 600 misses (first call for each topic)
        self.assertEqual(cache_info.misses, 600)

        # Transform last 400 topics again (these should still be in cache)
        for topic in topics[-400:]:
            MQTTTransport._transform_topic_cached(topic)

        cache_info_after = MQTTTransport._transform_topic_cached.cache_info()

        # The last 400 topics should be cache hits (they're within the 512 cache size)
        self.assertGreaterEqual(cache_info_after.hits, 400)

    def test_transform_topic_idempotent(self):
        """Test that transformation is idempotent for same input."""
        topic = "robot.arm.joint1"
        result1 = MQTTTransport._transform_topic_cached(topic)
        result2 = MQTTTransport._transform_topic_cached(topic)
        result3 = MQTTTransport._transform_topic_cached(topic)

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
        self.assertEqual(result1, "robot/arm/joint1")


if __name__ == "__main__":
    unittest.main()
