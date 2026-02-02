"""Shared thread pool manager for commlib.

Provides centralized thread pool management to reduce thread proliferation
and improve resource utilization across subscribers, RPC services, and actions.
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


class ThreadPoolManager:
    """Singleton manager for shared thread pools.

    Reduces thread count from 50-100 per node to 10-20 by sharing pools
    across all components. Categorizes work into:
    - IO operations (message handling, network I/O)
    - Compute operations (CPU-intensive callbacks)
    - Action execution (long-running action goals)
    """

    _instance: Optional["ThreadPoolManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize thread pools (singleton - use get_instance() instead)."""
        self._io_pool: Optional[ThreadPoolExecutor] = None
        self._compute_pool: Optional[ThreadPoolExecutor] = None
        self._action_pool: Optional[ThreadPoolExecutor] = None
        self._pool_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ThreadPoolManager":
        """Get singleton instance of ThreadPoolManager.

        Returns:
            ThreadPoolManager: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_io_pool(self, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """Get shared thread pool for I/O operations.

        Used for message handling, network I/O, and subscriber callbacks.
        Default size: CPU count × 2 (I/O bound workload)

        Args:
            max_workers: Maximum worker threads (only used on first call)

        Returns:
            ThreadPoolExecutor: Shared I/O thread pool
        """
        if self._io_pool is None:
            with self._pool_lock:
                if self._io_pool is None:
                    workers = max_workers or (os.cpu_count() or 4) * 2
                    self._io_pool = ThreadPoolExecutor(
                        max_workers=workers, thread_name_prefix="commlib-io-"
                    )
        return self._io_pool

    def get_compute_pool(self, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """Get shared thread pool for compute operations.

        Used for CPU-intensive callbacks and data processing.
        Default size: CPU count (CPU bound workload)

        Args:
            max_workers: Maximum worker threads (only used on first call)

        Returns:
            ThreadPoolExecutor: Shared compute thread pool
        """
        if self._compute_pool is None:
            with self._pool_lock:
                if self._compute_pool is None:
                    workers = max_workers or (os.cpu_count() or 4)
                    self._compute_pool = ThreadPoolExecutor(
                        max_workers=workers, thread_name_prefix="commlib-compute-"
                    )
        return self._compute_pool

    def get_action_pool(self, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """Get shared thread pool for action execution.

        Used for long-running action goals that may block.
        Default size: CPU count × 4 (mixed I/O and compute)

        Args:
            max_workers: Maximum worker threads (only used on first call)

        Returns:
            ThreadPoolExecutor: Shared action thread pool
        """
        if self._action_pool is None:
            with self._pool_lock:
                if self._action_pool is None:
                    workers = max_workers or (os.cpu_count() or 4) * 4
                    self._action_pool = ThreadPoolExecutor(
                        max_workers=workers, thread_name_prefix="commlib-action-"
                    )
        return self._action_pool

    def shutdown_all(self, wait: bool = True) -> None:
        """Shutdown all thread pools.

        Args:
            wait: If True, wait for all tasks to complete
        """
        with self._pool_lock:
            if self._io_pool is not None:
                self._io_pool.shutdown(wait=wait)
                self._io_pool = None
            if self._compute_pool is not None:
                self._compute_pool.shutdown(wait=wait)
                self._compute_pool = None
            if self._action_pool is not None:
                self._action_pool.shutdown(wait=wait)
                self._action_pool = None


# Convenience functions for direct access
def get_io_pool(max_workers: Optional[int] = None) -> ThreadPoolExecutor:
    """Get shared I/O thread pool.

    Args:
        max_workers: Maximum worker threads (only used on first call)

    Returns:
        ThreadPoolExecutor: Shared I/O thread pool
    """
    return ThreadPoolManager.get_instance().get_io_pool(max_workers)


def get_compute_pool(max_workers: Optional[int] = None) -> ThreadPoolExecutor:
    """Get shared compute thread pool.

    Args:
        max_workers: Maximum worker threads (only used on first call)

    Returns:
        ThreadPoolExecutor: Shared compute thread pool
    """
    return ThreadPoolManager.get_instance().get_compute_pool(max_workers)


def get_action_pool(max_workers: Optional[int] = None) -> ThreadPoolExecutor:
    """Get shared action thread pool.

    Args:
        max_workers: Maximum worker threads (only used on first call)

    Returns:
        ThreadPoolExecutor: Shared action thread pool
    """
    return ThreadPoolManager.get_instance().get_action_pool(max_workers)


def shutdown_all_pools(wait: bool = True) -> None:
    """Shutdown all shared thread pools.

    Args:
        wait: If True, wait for all tasks to complete
    """
    ThreadPoolManager.get_instance().shutdown_all(wait)
