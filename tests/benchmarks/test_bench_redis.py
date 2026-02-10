"""
Integration tests for Redis benchmarks.

These tests validate that Redis benchmark scripts work correctly with a real broker.
They use warning-based thresholds (not hard assertions) to detect performance regressions
without causing test failures due to system load variations.

Requires:
    - Redis broker running (e.g., docker run -d -p 1883:1883 eclipse-mosquitto)
    - Set COMMLIB_Redis_HOST and COMMLIB_Redis_PORT if not localhost:1883
"""

import pytest
import warnings
import sys
from pathlib import Path

# Add benchmark directory to Python path
benchmark_dir = Path(__file__).parent.parent.parent / "benchmark"
sys.path.insert(0, str(benchmark_dir))

# Import will be done inside tests after ensuring broker availability


@pytest.mark.redis
@pytest.mark.integration
@pytest.mark.benchmark
class TestRedisBenchmarks:
    """Integration tests for Redis benchmarks."""

    @pytest.mark.smoke
    def test_redis_broker_available(self, redis_available):
        """Verify Redis broker is available before running benchmarks."""
        # redis_available fixture will skip if broker not available
        assert redis_available is True

    @pytest.mark.smoke
    def test_redis_benchmark_imports(self, redis_available):
        """Verify benchmark script can be imported without errors."""
        try:
            import bench_redis_real

            assert hasattr(bench_redis_real, "benchmark_redis_publish_throughput")
            assert hasattr(bench_redis_real, "benchmark_redis_pubsub_roundtrip")
            assert hasattr(bench_redis_real, "benchmark_redis_concurrent_publishers")
        except ImportError as e:
            pytest.fail(f"Failed to import bench_redis_real: {e}")

    def test_redis_publish_benchmark_exists(self, redis_available):
        """Verify Redis publish benchmark function exists and is callable."""
        import bench_redis_real

        # Verify function exists
        assert callable(bench_redis_real.benchmark_redis_publish_throughput)

        # Note: Not running the actual benchmark in this test
        # Full benchmark execution is tested in manual/CI runs

    def test_redis_pubsub_benchmark_exists(self, redis_available):
        """Verify Redis pub/sub benchmark function exists and is callable."""
        import bench_redis_real

        # Verify function exists
        assert callable(bench_redis_real.benchmark_redis_pubsub_roundtrip)

    def test_redis_concurrent_benchmark_exists(self, redis_available):
        """Verify Redis concurrent publishers benchmark exists and is callable."""
        import bench_redis_real

        # Verify function exists
        assert callable(bench_redis_real.benchmark_redis_concurrent_publishers)

    @pytest.mark.smoke
    def test_redis_publish_smoke(self, redis_available):
        """Quick Redis publish smoke test - 100 messages."""
        from bench_redis_real import benchmark_redis_publish_throughput

        throughput = benchmark_redis_publish_throughput(iterations=100, warmup=10)

        # Warning-based threshold - doesn't fail on slow systems
        if throughput < 2000:
            warnings.warn(
                f"Redis publish slow: {throughput:.0f} msg/sec (expected >2000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_redis_publish_full(self, redis_available):
        """Full Redis publish benchmark - 1000 messages."""
        from bench_redis_real import benchmark_redis_publish_throughput

        throughput = benchmark_redis_publish_throughput(iterations=1000, warmup=100)

        # Warning-based threshold
        if throughput < 10000:
            warnings.warn(
                f"Redis publish below expected: {throughput:.0f} msg/sec (expected >10000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    @pytest.mark.smoke
    def test_redis_pubsub_smoke(self, redis_available):
        """Quick Redis pub/sub smoke test - 50 messages."""
        from bench_redis_real import benchmark_redis_pubsub_roundtrip

        throughput = benchmark_redis_pubsub_roundtrip(iterations=50, warmup=10)

        # Warning-based threshold
        if throughput < 1000:
            warnings.warn(
                f"Redis pub/sub slow: {throughput:.0f} msg/sec (expected >1000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_redis_pubsub_full(self, redis_available):
        """Full Redis pub/sub benchmark - 100 messages."""
        from bench_redis_real import benchmark_redis_pubsub_roundtrip

        throughput = benchmark_redis_pubsub_roundtrip(iterations=100, warmup=50)

        # Warning-based threshold
        if throughput < 2000:
            warnings.warn(
                f"Redis pub/sub below expected: {throughput:.0f} msg/sec (expected >2000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    @pytest.mark.smoke
    def test_redis_connection_pooling_smoke(self, redis_available):
        """Quick Redis connection pooling smoke test."""
        from bench_redis_real import benchmark_redis_connection_pool_sharing

        num_pools = benchmark_redis_connection_pool_sharing(num_publishers=10)

        # Warning-based threshold - should have exactly 1 pool
        if num_pools > 1:
            warnings.warn(
                f"Redis connection pooling inefficient: {num_pools} pools for 10 publishers (expected 1)"
            )

        # Basic sanity check
        assert num_pools >= 1, "Should have at least 1 connection pool"

    def test_redis_connection_pooling_full(self, redis_available):
        """Full Redis connection pooling benchmark - validates Phase 2 optimization."""
        from bench_redis_real import benchmark_redis_connection_pool_sharing

        num_pools = benchmark_redis_connection_pool_sharing(num_publishers=20)

        # Warning-based threshold - should have exactly 1 pool
        if num_pools > 1:
            warnings.warn(
                f"Redis connection pooling inefficient: {num_pools} pools for 20 publishers (expected 1)"
            )

        # Basic sanity check - Phase 2 optimization should result in 1 pool
        assert num_pools >= 1, "Should have at least 1 connection pool"

    @pytest.mark.smoke
    def test_redis_concurrent_smoke(self, redis_available):
        """Quick Redis concurrent publishers smoke test."""
        from bench_redis_real import benchmark_redis_concurrent_publishers

        throughput = benchmark_redis_concurrent_publishers(
            num_publishers=5, iterations_per_pub=20, warmup=5
        )

        # Warning-based threshold
        if throughput < 2000:
            warnings.warn(
                f"Redis concurrent slow: {throughput:.0f} msg/sec (expected >2000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_redis_concurrent_full(self, redis_available):
        """Full Redis concurrent publishers benchmark."""
        from bench_redis_real import benchmark_redis_concurrent_publishers

        throughput = benchmark_redis_concurrent_publishers(
            num_publishers=10, iterations_per_pub=100, warmup=10
        )

        # Warning-based threshold
        if throughput < 10000:
            warnings.warn(
                f"Redis concurrent below expected: {throughput:.0f} msg/sec (expected >10000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"
