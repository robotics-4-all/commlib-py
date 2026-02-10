"""System-level performance benchmarks.

Benchmarks overall system performance including thread pool usage,
connection management, and resource utilization.
"""

import time
from commlib.msg import PubSubMessage
from commlib.transports.mock import Subscriber, ConnectionParameters
from commlib.thread_pool import get_io_pool, ThreadPoolManager


class SensorReading(PubSubMessage):
    """Example message for benchmarking."""

    temperature: float = 23.5
    humidity: float = 65.0
    pressure: float = 1013.25


def benchmark_shared_vs_dedicated_pools():
    """Compare shared vs dedicated thread pools."""
    conn_params = ConnectionParameters(host="localhost", port=6379)
    num_subscribers = 20

    print("Benchmark: Shared vs Dedicated Thread Pools")
    print("-" * 60)
    print(f"Creating {num_subscribers} subscribers...")
    print()

    # Test with dedicated pools (legacy)
    print("Using DEDICATED pools (legacy):")
    ThreadPoolManager._instance = None  # Reset
    subs_dedicated = []
    start = time.perf_counter()
    for i in range(num_subscribers):
        sub = Subscriber(
            topic=f"sensors.sensor{i}",
            msg_type=SensorReading,
            on_message=lambda msg: None,
            conn_params=conn_params,
            use_shared_pool=False,  # Dedicated pool
        )
        subs_dedicated.append(sub)

    for sub in subs_dedicated:
        sub.run()

    dedicated_time = time.perf_counter() - start
    print(f"  Creation + Start: {dedicated_time * 1000:7.2f} ms")
    print(f"  Pools created: {num_subscribers} (1 per subscriber)")

    # Cleanup
    for sub in subs_dedicated:
        sub.stop()

    # Test with shared pools (optimized)
    print()
    print("Using SHARED pools (optimized):")
    ThreadPoolManager._instance = None  # Reset
    subs_shared = []
    start = time.perf_counter()
    for i in range(num_subscribers):
        sub = Subscriber(
            topic=f"sensors.sensor{i}",
            msg_type=SensorReading,
            on_message=lambda msg: None,
            conn_params=conn_params,
            use_shared_pool=True,  # Shared pool
        )
        subs_shared.append(sub)

    for sub in subs_shared:
        sub.run()

    shared_time = time.perf_counter() - start
    print(f"  Creation + Start: {shared_time * 1000:7.2f} ms")
    print(f"  Pools created: 1 (shared across all)")

    # Cleanup
    for sub in subs_shared:
        sub.stop()

    # Summary
    print()
    print("Summary:")
    print(f"  Dedicated: {dedicated_time * 1000:7.2f} ms")
    print(f"  Shared:    {shared_time * 1000:7.2f} ms")
    improvement = ((dedicated_time - shared_time) / dedicated_time) * 100
    print(f"  Improvement: {improvement:5.1f}% faster")

    return shared_time, dedicated_time


def benchmark_subscriber_scaling():
    """Benchmark subscriber creation scaling."""
    conn_params = ConnectionParameters(host="localhost", port=6379)

    print("\nBenchmark: Subscriber Scaling")
    print("-" * 60)
    print("Number of subscribers vs creation time:")
    print()

    counts = [1, 5, 10, 20, 50]

    for count in counts:
        ThreadPoolManager._instance = None  # Reset

        subscribers = []
        start = time.perf_counter()

        for i in range(count):
            sub = Subscriber(
                topic=f"test.{i}",
                msg_type=SensorReading,
                on_message=lambda msg: None,
                conn_params=conn_params,
                use_shared_pool=True,
            )
            subscribers.append(sub)

        for sub in subscribers:
            sub.run()

        elapsed = time.perf_counter() - start

        # Cleanup
        for sub in subscribers:
            sub.stop()

        avg_per_sub = (elapsed / count) * 1000
        print(
            f"  {count:3d} subscribers: {elapsed * 1000:7.2f} ms total | {avg_per_sub:6.2f} ms/subscriber"
        )


def benchmark_pool_reuse():
    """Benchmark thread pool reuse efficiency."""
    conn_params = ConnectionParameters(host="localhost", port=6379)

    print("\nBenchmark: Thread Pool Reuse")
    print("-" * 60)

    ThreadPoolManager._instance = None  # Reset

    # Get pool multiple times (should be same instance)
    pool_ids = []
    start = time.perf_counter()
    for _ in range(100):
        pool = get_io_pool()
        pool_ids.append(id(pool))
    elapsed = time.perf_counter() - start

    unique_pools = len(set(pool_ids))
    print(f"Pool retrievals: 100 calls")
    print(f"Unique pools:    {unique_pools} (should be 1)")
    print(f"Total time:      {elapsed * 1000:7.3f} ms")
    print(f"Avg per call:    {(elapsed / 100) * 1000000:7.3f} µs")

    assert unique_pools == 1, "Pool reuse failed!"
    print("\n✓ Pool reuse working correctly")


def benchmark_memory_footprint():
    """Estimate memory footprint reduction."""
    print("\nBenchmark: Estimated Memory Savings")
    print("-" * 60)

    num_subscribers = 50
    threads_per_dedicated_pool = 4
    threads_per_shared_pool = 8  # Single shared pool
    thread_stack_size_mb = 8  # Typical Python thread stack

    dedicated_threads = num_subscribers * threads_per_dedicated_pool
    shared_threads = threads_per_shared_pool

    dedicated_memory = dedicated_threads * thread_stack_size_mb
    shared_memory = shared_threads * thread_stack_size_mb

    savings = dedicated_memory - shared_memory
    savings_pct = (savings / dedicated_memory) * 100

    print(f"Scenario: {num_subscribers} subscribers")
    print()
    print(f"Dedicated pools:")
    print(
        f"  Threads:  {dedicated_threads:4d} ({num_subscribers} pools × {threads_per_dedicated_pool} threads)"
    )
    print(f"  Memory:   {dedicated_memory:4d} MB")
    print()
    print(f"Shared pool:")
    print(
        f"  Threads:  {shared_threads:4d} (1 pool × {threads_per_shared_pool} threads)"
    )
    print(f"  Memory:   {shared_memory:4d} MB")
    print()
    print(f"Savings:    {savings:4d} MB ({savings_pct:5.1f}% reduction)")


if __name__ == "__main__":
    print("=" * 60)
    print("System Performance Benchmarks")
    print("=" * 60)
    print()

    benchmark_shared_vs_dedicated_pools()
    benchmark_subscriber_scaling()
    benchmark_pool_reuse()
    benchmark_memory_footprint()

    print()
    print("=" * 60)
