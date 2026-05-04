"""
Integration tests for scaling benchmarks.

These tests validate that scaling benchmarks work correctly with mock transport
(no external dependencies required).
"""

import sys
from pathlib import Path

import pytest

# Add benchmark directory to Python path
benchmark_dir = Path(__file__).parent.parent.parent / "benchmark"
sys.path.insert(0, str(benchmark_dir))


@pytest.mark.unit
@pytest.mark.benchmark
class TestScalingBenchmarks:
    """Unit tests for scaling benchmarks using mock transport."""

    def test_publisher_scaling_import(self):
        """Verify publisher scaling benchmark can be imported."""
        from bench_scaling import benchmark_publisher_scaling

        assert callable(benchmark_publisher_scaling)

    def test_message_size_scaling_import(self):
        """Verify message size scaling benchmark can be imported."""
        from bench_scaling import benchmark_message_size_scaling

        assert callable(benchmark_message_size_scaling)

    def test_memory_usage_import(self):
        """Verify memory usage benchmark can be imported."""
        from bench_scaling import benchmark_memory_usage

        assert callable(benchmark_memory_usage)

    @pytest.mark.smoke
    def test_publisher_scaling_smoke(self):
        """Quick smoke test for publisher scaling."""
        from bench_scaling import benchmark_publisher_scaling

        results = benchmark_publisher_scaling(
            transport="mock", num_publishers_list=[1, 5, 10]
        )

        # Verify we got results for all publisher counts
        assert len(results) == 3
        assert 1 in results
        assert 5 in results
        assert 10 in results

        # Verify all throughputs are positive
        for num_pubs, throughput in results.items():
            assert throughput > 0, (
                f"Throughput for {num_pubs} publishers should be positive"
            )

    @pytest.mark.smoke
    def test_message_size_scaling_smoke(self):
        """Quick smoke test for message size scaling."""
        from bench_scaling import benchmark_message_size_scaling

        results = benchmark_message_size_scaling(
            transport="mock", message_sizes=[10, 100, 1000]
        )

        # Verify we got results for all message sizes
        assert len(results) == 3
        assert 10 in results
        assert 100 in results
        assert 1000 in results

        # Verify all throughputs are positive
        for size, throughput in results.items():
            assert throughput > 0, f"Throughput for size {size} should be positive"

    @pytest.mark.smoke
    def test_memory_usage_smoke(self):
        """Quick smoke test for memory usage benchmark."""
        from bench_scaling import benchmark_memory_usage

        results = benchmark_memory_usage(
            transport="mock",
            num_publishers=10,
            duration=2.0,  # Quick 2-second test
        )

        # Verify all expected metrics are present
        assert "baseline_mb" in results
        assert "creation_mb" in results
        assert "runtime_mb" in results
        assert "final_mb" in results
        assert "mem_per_publisher_mb" in results
        assert "throughput" in results
        assert "messages_sent" in results

        # Verify memory values make sense
        assert results["baseline_mb"] > 0
        assert results["creation_mb"] >= results["baseline_mb"]
        assert results["runtime_mb"] >= results["baseline_mb"]
        assert results["mem_per_publisher_mb"] >= 0
        assert results["throughput"] > 0
        assert results["messages_sent"] > 0

    def test_publisher_scaling_full(self):
        """Full publisher scaling test."""
        from bench_scaling import benchmark_publisher_scaling

        results = benchmark_publisher_scaling(
            transport="mock", num_publishers_list=[1, 5, 10, 20, 50]
        )

        assert len(results) == 5

        # Generally, total throughput should increase with more publishers
        # (though not necessarily linear due to overhead)
        for num_pubs, throughput in results.items():
            assert throughput > 1000, (
                f"Throughput for {num_pubs} publishers unexpectedly low: {throughput}"
            )

    def test_message_size_scaling_full(self):
        """Full message size scaling test."""
        from bench_scaling import benchmark_message_size_scaling

        results = benchmark_message_size_scaling(
            transport="mock", message_sizes=[10, 100, 1000, 10000]
        )

        assert len(results) == 4

        # Larger messages generally have lower message/sec throughput
        # But this is transport-dependent, so just verify positive values
        for size, throughput in results.items():
            assert throughput > 0, f"Throughput for size {size} should be positive"

    def test_memory_usage_full(self):
        """Full memory usage benchmark test."""
        from bench_scaling import benchmark_memory_usage

        results = benchmark_memory_usage(
            transport="mock", num_publishers=20, duration=3.0
        )

        # Memory after creation should be at least baseline (RSS too coarse for small allocations)
        assert results["creation_mb"] >= results["baseline_mb"]

        # Memory per publisher should be reasonable (less than 10MB for mock transport)
        assert results["mem_per_publisher_mb"] < 10, (
            f"Memory per publisher unexpectedly high: {results['mem_per_publisher_mb']:.2f} MB"
        )

        # Should have sent a reasonable number of messages
        assert results["messages_sent"] > 1000, (
            f"Expected more messages sent: {results['messages_sent']}"
        )
