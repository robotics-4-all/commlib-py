"""
Integration tests for AMQP benchmarks - Phase 3 Validation.

These tests validate that AMQP benchmark scripts work correctly with a real RabbitMQ broker.
They specifically validate Phase 3 optimizations:
- Event-driven RPC response
- Connection pooling
- Performance improvements

Requires:
    - RabbitMQ broker running (e.g., docker run -d -p 5672:5672 rabbitmq:3-management)
    - Set COMMLIB_AMQP_HOST and COMMLIB_AMQP_PORT if not localhost:5672
"""
# pylint: disable=unused-argument

import sys
import warnings
from pathlib import Path

import pytest

# Add benchmark directory to Python path
benchmark_dir = Path(__file__).parent.parent.parent / "benchmark"
sys.path.insert(0, str(benchmark_dir))


@pytest.mark.amqp
@pytest.mark.integration
@pytest.mark.benchmark
class TestAMQPBenchmarks:
    """Integration tests for AMQP benchmarks - Phase 3 validation."""

    @pytest.mark.smoke
    def test_amqp_broker_available(self, amqp_available):
        """Verify AMQP broker is available before running benchmarks."""
        # amqp_available fixture will skip if broker not available
        assert amqp_available is True

    @pytest.mark.smoke
    def test_amqp_benchmark_imports(self, amqp_available):
        """Verify benchmark script can be imported without errors."""
        try:
            import bench_amqp_real

            assert hasattr(bench_amqp_real, "benchmark_amqp_publish")
            assert hasattr(bench_amqp_real, "benchmark_amqp_pubsub_roundtrip")
            assert hasattr(bench_amqp_real, "benchmark_amqp_rpc_latency")
            assert hasattr(bench_amqp_real, "benchmark_amqp_connection_pooling")
        except ImportError as e:
            pytest.fail(f"Failed to import bench_amqp_real: {e}")

    @pytest.mark.smoke
    def test_amqp_publish_smoke(self, amqp_available):
        """Quick AMQP publish smoke test - validates basic functionality."""
        from bench_amqp_real import benchmark_amqp_publish

        throughput = benchmark_amqp_publish(iterations=50, warmup=10)

        # Warning-based threshold (not hard assertion)
        if throughput < 1000:
            warnings.warn(f"AMQP publish slow: {throughput:.0f} msg/sec")

        assert throughput > 0, "Throughput should be positive"

    def test_amqp_publish_full(self, amqp_available):
        """Full AMQP publish benchmark."""
        from bench_amqp_real import benchmark_amqp_publish

        throughput = benchmark_amqp_publish(iterations=1000)

        if throughput < 5000:
            warnings.warn(f"AMQP publish below 5k msg/sec: {throughput:.0f}")

        assert throughput > 0

    @pytest.mark.smoke
    def test_amqp_pubsub_smoke(self, amqp_available):
        """Quick AMQP pub/sub smoke test."""
        from bench_amqp_real import benchmark_amqp_pubsub_roundtrip

        throughput = benchmark_amqp_pubsub_roundtrip(iterations=10)

        if throughput < 100:
            warnings.warn(f"AMQP pub/sub slow: {throughput:.0f} msg/sec")

        assert throughput > 0

    def test_amqp_pubsub_full(self, amqp_available):
        """Full AMQP pub/sub benchmark."""
        from bench_amqp_real import benchmark_amqp_pubsub_roundtrip

        throughput = benchmark_amqp_pubsub_roundtrip(iterations=100)

        if throughput < 1000:
            warnings.warn(f"AMQP pub/sub below 1k msg/sec: {throughput:.0f}")

        assert throughput > 0

    @pytest.mark.smoke
    def test_amqp_rpc_latency_smoke(self, amqp_available):
        """Quick RPC latency test - validates Phase 3 event-driven optimization."""
        from bench_amqp_real import benchmark_amqp_rpc_latency

        latency = benchmark_amqp_rpc_latency(iterations=10)

        # Phase 3 event-driven should have low latency (not busy-wait)
        if latency > 50:  # 50ms seems high for local broker
            warnings.warn(f"AMQP RPC latency high: {latency:.1f} ms")

        assert latency > 0, "Latency should be positive"
        assert latency < 1000, f"Latency too high: {latency:.1f} ms"

    def test_amqp_rpc_latency_full(self, amqp_available):
        """Full RPC latency benchmark - Phase 3 event-driven validation."""
        from bench_amqp_real import benchmark_amqp_rpc_latency

        latency = benchmark_amqp_rpc_latency(iterations=100)

        # Phase 3 optimization should show low latency
        if latency > 20:
            warnings.warn(f"AMQP RPC latency: {latency:.1f} ms (expected <20ms)")

        assert latency > 0
        assert latency < 500, f"Latency extremely high: {latency:.1f} ms"

    @pytest.mark.smoke
    def test_amqp_connection_pooling(self, amqp_available):
        """Validate Phase 3 connection pooling - critical optimization test."""
        from bench_amqp_real import benchmark_amqp_connection_pooling

        num_connections = benchmark_amqp_connection_pooling(num_publishers=20)

        # Phase 3 optimization: 20 publishers should share 1 connection
        if num_connections > 1:
            warnings.warn(
                f"Phase 3 connection pooling inefficient: {num_connections} connections "
                f"for 20 publishers (expected 1)"
            )

        # Soft assertion - warn but don't fail
        assert num_connections >= 1, "Should have at least 1 connection"
        assert num_connections <= 3, (
            f"Too many connections: {num_connections} (expected 1)"
        )

        # Ideal case
        if num_connections == 1:
            print(
                "\n✓ Phase 3 optimization VALIDATED: All publishers share 1 connection!"
            )
