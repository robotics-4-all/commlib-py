"""Tests for shared thread pool manager."""
# pylint: disable=protected-access

import unittest
import threading
import time
from commlib.thread_pool import (
    ThreadPoolManager,
    get_io_pool,
    get_compute_pool,
    get_action_pool,
    shutdown_all_pools,
)


class TestThreadPoolManager(unittest.TestCase):
    """Test ThreadPoolManager singleton and pool management."""

    def tearDown(self):
        """Clean up pools after each test."""
        # Reset singleton for clean state
        ThreadPoolManager._instance = None

    def test_singleton_pattern(self):
        """Test that ThreadPoolManager is a singleton."""
        manager1 = ThreadPoolManager.get_instance()
        manager2 = ThreadPoolManager.get_instance()
        self.assertIs(manager1, manager2)

    def test_io_pool_creation(self):
        """Test I/O pool is created on first access."""
        manager = ThreadPoolManager.get_instance()
        pool1 = manager.get_io_pool()
        pool2 = manager.get_io_pool()

        # Same pool instance returned
        self.assertIs(pool1, pool2)
        self.assertIsNotNone(pool1)

    def test_compute_pool_creation(self):
        """Test compute pool is created on first access."""
        manager = ThreadPoolManager.get_instance()
        pool1 = manager.get_compute_pool()
        pool2 = manager.get_compute_pool()

        self.assertIs(pool1, pool2)
        self.assertIsNotNone(pool1)

    def test_action_pool_creation(self):
        """Test action pool is created on first access."""
        manager = ThreadPoolManager.get_instance()
        pool1 = manager.get_action_pool()
        pool2 = manager.get_action_pool()

        self.assertIs(pool1, pool2)
        self.assertIsNotNone(pool1)

    def test_pools_are_independent(self):
        """Test that different pool types are independent instances."""
        manager = ThreadPoolManager.get_instance()
        io_pool = manager.get_io_pool()
        compute_pool = manager.get_compute_pool()
        action_pool = manager.get_action_pool()

        self.assertIsNot(io_pool, compute_pool)
        self.assertIsNot(io_pool, action_pool)
        self.assertIsNot(compute_pool, action_pool)

    def test_pool_executes_tasks(self):
        """Test that pools can execute tasks."""
        pool = get_io_pool()

        result_container = []

        def task():
            result_container.append(42)

        future = pool.submit(task)
        future.result(timeout=1)

        self.assertEqual(result_container, [42])

    def test_pool_concurrent_execution(self):
        """Test pools can execute multiple tasks concurrently."""
        pool = get_io_pool()

        results = []
        lock = threading.Lock()

        def task(value):
            time.sleep(0.01)  # Simulate work
            with lock:
                results.append(value)

        futures = [pool.submit(task, i) for i in range(10)]

        for future in futures:
            future.result(timeout=1)

        self.assertEqual(len(results), 10)
        self.assertEqual(set(results), set(range(10)))

    def test_custom_max_workers(self):
        """Test custom max_workers parameter."""
        # Create new manager instance with custom workers
        manager = ThreadPoolManager.get_instance()
        pool = manager.get_io_pool(max_workers=3)

        # Should have created pool (can't easily test worker count,
        # but verify pool works)
        self.assertIsNotNone(pool)

        future = pool.submit(lambda: 123)
        self.assertEqual(future.result(timeout=1), 123)

    def test_convenience_functions(self):
        """Test convenience functions return correct pools."""
        io = get_io_pool()
        compute = get_compute_pool()
        action = get_action_pool()

        manager = ThreadPoolManager.get_instance()
        self.assertIs(io, manager.get_io_pool())
        self.assertIs(compute, manager.get_compute_pool())
        self.assertIs(action, manager.get_action_pool())

    def test_thread_safety(self):
        """Test thread-safe pool creation."""
        results = []

        def create_pool():
            pool = get_io_pool()
            results.append(pool)

        threads = [threading.Thread(target=create_pool) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same pool instance
        self.assertEqual(len(set(id(p) for p in results)), 1)

    def test_shutdown_all_pools(self):
        """Test shutdown_all_pools cleans up resources."""
        # Create pools
        io = get_io_pool()
        get_compute_pool()
        get_action_pool()

        # Submit some tasks
        io.submit(lambda: time.sleep(0.01))

        # Shutdown
        shutdown_all_pools(wait=True)

        # After shutdown, manager should have no pools
        manager = ThreadPoolManager.get_instance()
        self.assertIsNone(manager._io_pool)
        self.assertIsNone(manager._compute_pool)
        self.assertIsNone(manager._action_pool)


class TestThreadPoolIntegration(unittest.TestCase):
    """Integration tests for thread pools."""

    def tearDown(self):
        """Clean up after each test."""
        ThreadPoolManager._instance = None

    def test_shared_pool_reduces_thread_count(self):
        """Test that shared pool reduces overall thread count."""
        # Simulate creating multiple subscribers/services
        pools = [get_io_pool() for _ in range(10)]

        # All should be the same instance
        unique_pools = set(id(p) for p in pools)
        self.assertEqual(len(unique_pools), 1)

        # This means only 1 ThreadPoolExecutor created instead of 10

    def test_pools_handle_exceptions(self):
        """Test that pools handle task exceptions gracefully."""
        pool = get_io_pool()

        def failing_task():
            raise ValueError("Test exception")

        future = pool.submit(failing_task)

        with self.assertRaises(ValueError):
            future.result(timeout=1)

        # Pool should still work after exception
        future2 = pool.submit(lambda: 42)
        self.assertEqual(future2.result(timeout=1), 42)


if __name__ == "__main__":
    unittest.main()
