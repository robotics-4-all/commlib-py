"""
Scaling benchmarks for commlib-py.

Tests how performance scales with:
- Number of publishers/subscribers
- Message sizes
- Concurrent connections
- Message rates

Can be run standalone or via pytest integration tests.
"""

import time
import psutil
from commlib.msg import PubSubMessage


class ScalingTestMessage(PubSubMessage):
    """Message for scaling tests with configurable payload."""

    seq: int = 0
    data: str = ""
    timestamp: float = 0.0


def _get_transport_classes(transport):
    """Return (ConnectionParameters, Publisher) for transport."""
    if transport == "mock":
        from commlib.transports.mock import (
            ConnectionParameters,
            Publisher,
        )
    elif transport == "mqtt":
        from commlib.transports.mqtt import (
            ConnectionParameters,
            Publisher,
        )
    elif transport == "redis":
        from commlib.transports.redis import (
            ConnectionParameters,
            Publisher,
        )
    elif transport == "amqp":
        from commlib.transports.amqp import (
            ConnectionParameters,
            Publisher,
        )
    else:
        raise ValueError(f"Unknown transport: {transport}")
    return ConnectionParameters, Publisher


def benchmark_publisher_scaling(transport="mock", num_publishers_list=None):
    """
    Benchmark how throughput scales with number of publishers.

    Args:
        transport: Transport type (mock, mqtt, redis, amqp)
        num_publishers_list: List of publisher counts to test

    Returns:
        dict: Results mapping num_publishers -> throughput
    """
    if num_publishers_list is None:
        num_publishers_list = [1, 5, 10, 20, 50, 100]

    results = {}

    ConnectionParameters, Publisher = _get_transport_classes(transport)
    conn_params = ConnectionParameters()

    print(f"\n{'=' * 60}")
    print(f"Publisher Scaling Benchmark ({transport})")
    print(f"{'=' * 60}\n")
    print(
        f"{'Publishers':>12} | {'Throughput (msg/s)':>18}"
        f" | {'Latency (ms)':>14} | {'Total Messages':>15}"
    )
    print(f"{'-' * 12}-+-{'-' * 18}-+-{'-' * 14}-+-{'-' * 15}")

    for num_pubs in num_publishers_list:
        publishers = []

        # Create publishers
        for i in range(num_pubs):
            pub = Publisher(
                topic=f"scaling/test/pub{i}",
                msg_type=ScalingTestMessage,
                conn_params=conn_params,
            )
            pub.run(wait=True)
            publishers.append(pub)

        message = ScalingTestMessage(seq=0, data="test", timestamp=time.time())

        # Warmup
        for pub in publishers:
            for _ in range(10):
                pub.publish(message)
        time.sleep(0.2)

        # Benchmark
        iterations_per_pub = 100
        total_messages = num_pubs * iterations_per_pub

        start = time.perf_counter()
        for _ in range(iterations_per_pub):
            for pub in publishers:
                pub.publish(message)
        elapsed = time.perf_counter() - start

        throughput = total_messages / elapsed
        latency = (elapsed / total_messages) * 1000
        results[num_pubs] = throughput

        print(
            f"{num_pubs:>12} | {throughput:>18.0f} | {latency:>14.3f} | {total_messages:>15}"
        )

        # Cleanup
        for pub in publishers:
            pub.stop(wait=True)

        time.sleep(0.2)

    print(f"\n{'=' * 60}\n")
    return results


def benchmark_message_size_scaling(transport="mock", message_sizes=None):
    """
    Benchmark how throughput changes with message size.

    Args:
        transport: Transport type
        message_sizes: List of message sizes (in bytes) to test

    Returns:
        dict: Results mapping size -> throughput
    """
    if message_sizes is None:
        message_sizes = [10, 100, 1000, 10000, 100000]  # 10B to 100KB

    results = {}

    ConnectionParameters, Publisher = _get_transport_classes(transport)
    conn_params = ConnectionParameters()

    print(f"\n{'=' * 60}")
    print(f"Message Size Scaling Benchmark ({transport})")
    print(f"{'=' * 60}\n")
    print(
        f"{'Size (bytes)':>13} | {'Throughput (msg/s)':>18}"
        f" | {'Bandwidth (MB/s)':>18} | {'Latency (ms)':>14}"
    )
    print(f"{'-' * 13}-+-{'-' * 18}-+-{'-' * 18}-+-{'-' * 14}")

    for size in message_sizes:
        pub = Publisher(
            topic="scaling/message_size",
            msg_type=ScalingTestMessage,
            conn_params=conn_params,
        )
        pub.run(wait=True)

        # Create message with specified size
        data = "x" * size
        message = ScalingTestMessage(seq=0, data=data, timestamp=time.time())

        # Warmup
        for _ in range(20):
            pub.publish(message)
        time.sleep(0.1)

        # Benchmark
        iterations = min(
            1000, max(100, 100000 // size)
        )  # Adjust iterations based on size
        start = time.perf_counter()
        for _ in range(iterations):
            pub.publish(message)
        elapsed = time.perf_counter() - start

        throughput = iterations / elapsed
        bandwidth_mb = (throughput * size) / (1024 * 1024)
        latency = (elapsed / iterations) * 1000
        results[size] = throughput

        print(
            f"{size:>13} | {throughput:>18.0f} | {bandwidth_mb:>18.2f} | {latency:>14.3f}"
        )

        pub.stop(wait=True)
        time.sleep(0.1)

    print(f"\n{'=' * 60}\n")
    return results


def benchmark_memory_usage(transport="mock", num_publishers=20, duration=5.0):
    """
    Benchmark memory usage with multiple publishers.

    Args:
        transport: Transport type
        num_publishers: Number of publishers to create
        duration: How long to run the benchmark (seconds)

    Returns:
        dict: Memory usage statistics
    """
    ConnectionParameters, Publisher = _get_transport_classes(transport)
    conn_params = ConnectionParameters()
    process = psutil.Process()

    print(f"\n{'=' * 60}")
    print(f"Memory Usage Benchmark ({transport})")
    print(f"{'=' * 60}\n")

    # Measure baseline memory
    baseline_mem = process.memory_info().rss / (1024 * 1024)  # MB
    print(f"Baseline memory: {baseline_mem:.2f} MB")

    publishers = []

    # Create publishers and track memory
    print(f"\nCreating {num_publishers} publishers...")
    for i in range(num_publishers):
        pub = Publisher(
            topic=f"memory/test/pub{i}",
            msg_type=ScalingTestMessage,
            conn_params=conn_params,
        )
        pub.run(wait=True)
        publishers.append(pub)

        if (i + 1) % 10 == 0:
            current_mem = process.memory_info().rss / (1024 * 1024)
            mem_per_pub = (current_mem - baseline_mem) / (i + 1)
            print(
                f"  {i + 1} publishers: {current_mem:.2f} MB ({mem_per_pub:.2f} MB/publisher)"
            )

    creation_mem = process.memory_info().rss / (1024 * 1024)
    mem_per_publisher = (creation_mem - baseline_mem) / num_publishers

    print(f"\nMemory after creation: {creation_mem:.2f} MB")
    print(f"Memory per publisher: {mem_per_publisher:.2f} MB")

    # Run publishers and measure memory under load
    print(f"\nRunning publishers for {duration} seconds...")
    message = ScalingTestMessage(seq=0, data="x" * 100, timestamp=time.time())

    start_time = time.time()
    msg_count = 0

    while (time.time() - start_time) < duration:
        for pub in publishers:
            pub.publish(message)
            msg_count += 1
        time.sleep(0.001)  # Small delay to prevent CPU saturation

    runtime_mem = process.memory_info().rss / (1024 * 1024)
    elapsed = time.time() - start_time
    throughput = msg_count / elapsed

    print(f"\nMemory under load: {runtime_mem:.2f} MB")
    print(f"Messages sent: {msg_count}")
    print(f"Throughput: {throughput:.0f} msg/sec")

    # Cleanup and measure final memory
    for pub in publishers:
        pub.stop(wait=True)

    time.sleep(0.5)
    final_mem = process.memory_info().rss / (1024 * 1024)

    print(f"Memory after cleanup: {final_mem:.2f} MB")

    results = {
        "baseline_mb": baseline_mem,
        "creation_mb": creation_mem,
        "runtime_mb": runtime_mem,
        "final_mb": final_mem,
        "mem_per_publisher_mb": mem_per_publisher,
        "throughput": throughput,
        "messages_sent": msg_count,
    }

    print(f"\n{'=' * 60}\n")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run scaling benchmarks")
    parser.add_argument(
        "--transport",
        choices=["mock", "mqtt", "redis", "amqp"],
        default="mock",
        help="Transport to benchmark",
    )
    parser.add_argument(
        "--test",
        choices=["publishers", "message_size", "memory", "all"],
        default="all",
        help="Which test to run",
    )

    args = parser.parse_args()

    if args.test in ["publishers", "all"]:
        benchmark_publisher_scaling(transport=args.transport)

    if args.test in ["message_size", "all"]:
        benchmark_message_size_scaling(transport=args.transport)

    if args.test in ["memory", "all"]:
        benchmark_memory_usage(transport=args.transport)
