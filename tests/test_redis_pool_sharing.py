"""Tests for Redis connection pool sharing."""

import unittest
from commlib.transports.redis import (
    ConnectionParameters,
    get_or_create_redis_pool,
    release_redis_pool,
    _get_pool_key,
    _REDIS_POOL_REGISTRY,
    _REDIS_POOL_REFCOUNT,
)


class TestRedisPoolSharing(unittest.TestCase):
    """Test Redis connection pool sharing functionality."""

    def tearDown(self):
        """Clean up pools after each test."""
        # Clear registry for clean state
        _REDIS_POOL_REGISTRY.clear()
        _REDIS_POOL_REFCOUNT.clear()

    def test_pool_key_tcp(self):
        """Test pool key generation for TCP connections."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)
        key = _get_pool_key(params)
        self.assertEqual(key, ("tcp", "localhost", 6379, 0))

    def test_pool_key_tcp_different_db(self):
        """Test pool keys differ for different databases."""
        params1 = ConnectionParameters(host="localhost", port=6379, db=0)
        params2 = ConnectionParameters(host="localhost", port=6379, db=1)

        key1 = _get_pool_key(params1)
        key2 = _get_pool_key(params2)

        self.assertNotEqual(key1, key2)

    def test_pool_key_unix(self):
        """Test pool key generation for Unix socket connections."""
        params = ConnectionParameters(unix_socket="/tmp/redis.sock", db=0)
        key = _get_pool_key(params)
        self.assertEqual(key, ("unix", "/tmp/redis.sock", 0))

    def test_get_or_create_pool_creates_new(self):
        """Test that get_or_create_pool creates new pool."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        # Registry should be empty
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 0)

        pool = get_or_create_redis_pool(params)

        # Pool should be created and registered
        self.assertIsNotNone(pool)
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 1)
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 1)

    def test_get_or_create_pool_reuses_existing(self):
        """Test that get_or_create_pool reuses existing pool."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        pool1 = get_or_create_redis_pool(params)
        pool2 = get_or_create_redis_pool(params)

        # Should be the same pool instance
        self.assertIs(pool1, pool2)

        # Only one pool in registry
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 1)

        # Reference count should be 2
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 2)

    def test_different_params_create_different_pools(self):
        """Test that different parameters create different pools."""
        params1 = ConnectionParameters(host="localhost", port=6379, db=0)
        params2 = ConnectionParameters(host="localhost", port=6380, db=0)

        pool1 = get_or_create_redis_pool(params1)
        pool2 = get_or_create_redis_pool(params2)

        # Should be different pool instances
        self.assertIsNot(pool1, pool2)

        # Two pools in registry
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 2)

    def test_release_pool_decrements_refcount(self):
        """Test that releasing pool decrements reference count."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        get_or_create_redis_pool(params)
        get_or_create_redis_pool(params)

        # Reference count should be 2
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 2)

        release_redis_pool(params)

        # Reference count should be 1
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 1)

        # Pool should still exist
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 1)

    def test_release_pool_removes_when_zero(self):
        """Test that pool is removed when refcount reaches zero."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        get_or_create_redis_pool(params)

        # Release the pool
        release_redis_pool(params)

        # Pool should be removed from registry
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 0)
        self.assertNotIn(_get_pool_key(params), _REDIS_POOL_REFCOUNT)

    def test_multiple_instances_share_pool(self):
        """Test that multiple transport instances share the same pool."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        # Simulate 10 transport instances
        pools = [get_or_create_redis_pool(params) for _ in range(10)]

        # All should be the same instance
        unique_pools = set(id(p) for p in pools)
        self.assertEqual(len(unique_pools), 1)

        # Only one pool in registry
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 1)

        # Reference count should be 10
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 10)

    def test_pool_cleanup_sequence(self):
        """Test complete lifecycle of pool creation and cleanup."""
        params = ConnectionParameters(host="localhost", port=6379, db=0)

        # Create 3 references
        pool1 = get_or_create_redis_pool(params)
        pool2 = get_or_create_redis_pool(params)
        pool3 = get_or_create_redis_pool(params)

        self.assertIs(pool1, pool2)
        self.assertIs(pool2, pool3)
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 3)

        # Release 2
        release_redis_pool(params)
        release_redis_pool(params)

        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 1)
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 1)

        # Release last one
        release_redis_pool(params)

        # Should be cleaned up
        self.assertEqual(len(_REDIS_POOL_REGISTRY), 0)

    def test_thread_safety(self):
        """Test that pool creation is thread-safe."""
        import threading

        params = ConnectionParameters(host="localhost", port=6379, db=0)
        pools = []

        def create_pool():
            pool = get_or_create_redis_pool(params)
            pools.append(pool)

        threads = [threading.Thread(target=create_pool) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same pool
        unique_pools = set(id(p) for p in pools)
        self.assertEqual(len(unique_pools), 1)

        # Reference count should be 10
        self.assertEqual(_REDIS_POOL_REFCOUNT[_get_pool_key(params)], 10)


if __name__ == "__main__":
    unittest.main()
