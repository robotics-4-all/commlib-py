"""Real Redis broker benchmarks.

Requires running Redis server:
  docker run -d -p 6379:6379 redis:latest

Or use existing Redis via environment variables:
  export COMMLIB_REDIS_HOST=localhost
  export COMMLIB_REDIS_PORT=6379
"""

import os
import sys
import time
from commlib.msg import PubSubMessage
from commlib.transports.redis import Publisher, Subscriber, ConnectionParameters


class SensorReading(PubSubMessage):
    """Example sensor message."""

    temperature: float = 23.5
    humidity: float = 65.0
    pressure: float = 1013.25
    timestamp: float = 0.0


def get_redis_params():
    """Get Redis connection parameters from environment or defaults."""
    host = os.getenv("COMMLIB_REDIS_HOST", "localhost")
    port = int(os.getenv("COMMLIB_REDIS_PORT", "6379"))
    return ConnectionParameters(host=host, port=port)


def check_redis_available():
    """Check if Redis server is available."""
    import socket

    params = get_redis_params()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((params.host, params.port))
        sock.close()
        return result == 0
    except Exception:
        return False


def benchmark_redis_publish_throughput(iterations=1000, warmup=100):
    """Benchmark Redis publisher throughput.

    Args:
        iterations: Number of messages to publish for the benchmark
        warmup: Number of warmup messages to publish before benchmark

    Returns:
        float: Throughput in messages per second
    """
    conn_params = get_redis_params()

    print("Setting up Redis publisher...")
    pub = Publisher(
        topic="benchmark.sensors.temperature",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run(wait=True)

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    # Warm up
    if warmup > 0:
        print(f"Warming up ({warmup} messages)...")
        for _ in range(warmup):
            pub.publish(message)
        time.sleep(0.1)

    # Benchmark
    print(f"Running benchmark ({iterations} messages)...")
    start = time.perf_counter()
    for _ in range(iterations):
        pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000  # ms

    pub.stop(wait=True)

    print(f"Redis Publish: {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    return throughput


def benchmark_redis_pubsub_roundtrip(iterations=100, warmup=50):
    """Benchmark Redis pub/sub round trip.

    Args:
        iterations: Number of messages to publish for the benchmark
        warmup: Number of warmup messages to publish before benchmark

    Returns:
        float: Throughput in messages per second
    """
    conn_params = get_redis_params()

    message_count = [0]
    received_messages = []

    def on_message(msg):
        message_count[0] += 1
        received_messages.append(msg)

    print("\nSetting up Redis subscriber...")
    sub = Subscriber(
        topic="benchmark.sensors.temperature",
        msg_type=SensorReading,
        on_message=on_message,
        conn_params=conn_params,
    )
    sub.run(wait=True)
    time.sleep(0.5)  # Wait for subscription to be ready

    print("Setting up Redis publisher...")
    pub = Publisher(
        topic="benchmark.sensors.temperature",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run(wait=True)

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    # Warm up
    if warmup > 0:
        print(f"Warming up ({warmup} messages)...")
        for _ in range(warmup):
            pub.publish(message)
        time.sleep(0.5)
        message_count[0] = 0  # Reset
        received_messages.clear()

    # Benchmark
    print(f"Running benchmark ({iterations} messages)...")
    start = time.perf_counter()
    for i in range(iterations):
        message.timestamp = time.time()
        pub.publish(message)

    # Wait for all messages to be received
    timeout = 5.0
    wait_start = time.time()
    while message_count[0] < iterations and (time.time() - wait_start) < timeout:
        time.sleep(0.01)

    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000  # ms

    # Calculate end-to-end latency
    if received_messages:
        latencies = []
        for msg in received_messages[:iterations]:
            if hasattr(msg, "timestamp") and msg.timestamp > 0:
                msg_latency = (time.time() - msg.timestamp) * 1000
                if msg_latency < 1000:  # Sanity check
                    latencies.append(msg_latency)

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            print(f"Avg E2E latency: {avg_latency:7.3f} ms")

    pub.stop(wait=True)
    sub.stop()

    print(f"Redis Pub+Sub: {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    print(f"Messages delivered: {message_count[0]}/{iterations}")

    return throughput


def benchmark_redis_connection_pool_sharing(num_publishers=20):
    """Benchmark Redis connection pool sharing.

    Args:
        num_publishers: Number of publishers to create

    Returns:
        int: Number of connection pools created (should be 1 if sharing works)
    """
    from commlib.transports.redis import (
        _REDIS_POOL_REGISTRY,
        RedisTransport,
    )

    conn_params = get_redis_params()

    print("\nBenchmark: Connection pool sharing")
    print("-" * 60)

    RedisTransport.reset_redis_pool()

    publishers = []

    print(f"Creating {num_publishers} publishers...")
    start = time.perf_counter()
    for i in range(num_publishers):
        pub = Publisher(
            topic=f"benchmark.pool.pub{i}",
            msg_type=SensorReading,
            conn_params=conn_params,
        )
        pub.run(wait=True)
        publishers.append(pub)
    creation_time = time.perf_counter() - start

    # Check pool registry
    num_pools = len(_REDIS_POOL_REGISTRY)

    print(f"Publishers created: {num_publishers}")
    print(f"Connection pools:   {num_pools}")
    print(f"Creation time:      {creation_time * 1000:7.2f} ms")
    print(f"Avg per publisher:  {(creation_time / num_publishers) * 1000:7.2f} ms")

    if num_pools == 1:
        print("✓ Connection pool sharing working correctly!")
    else:
        print(f"⚠ Expected 1 pool, got {num_pools}")

    # Cleanup
    for pub in publishers:
        pub.stop(wait=True)

    time.sleep(0.2)

    return num_pools


def benchmark_redis_concurrent_publishers(
    num_publishers=10, iterations_per_pub=100, warmup=10
):
    """Benchmark multiple concurrent publishers.

    Args:
        num_publishers: Number of concurrent publishers to create
        iterations_per_pub: Number of messages each publisher sends
        warmup: Number of warmup messages per publisher

    Returns:
        float: Total throughput in messages per second
    """
    conn_params = get_redis_params()

    print(f"\nBenchmark: {num_publishers} concurrent publishers")
    print("-" * 60)

    publishers = []
    for i in range(num_publishers):
        pub = Publisher(
            topic=f"benchmark.concurrent.pub{i}",
            msg_type=SensorReading,
            conn_params=conn_params,
        )
        pub.run(wait=True)
        publishers.append(pub)

    message = SensorReading(temperature=23.5, humidity=65.0, pressure=1013.25)

    # Warm up
    if warmup > 0:
        for pub in publishers:
            for _ in range(warmup):
                pub.publish(message)
        time.sleep(0.2)

    # Benchmark
    total_messages = num_publishers * iterations_per_pub

    start = time.perf_counter()
    for _ in range(iterations_per_pub):
        for pub in publishers:
            pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = total_messages / elapsed
    latency = (elapsed / total_messages) * 1000

    print(f"Total messages: {total_messages}")
    print(f"Throughput:     {throughput:10.0f} msg/sec")
    print(f"Avg latency:    {latency:7.3f} ms/msg")

    for pub in publishers:
        pub.stop(wait=True)

    return throughput


def benchmark_redis_message_sizes():
    """Benchmark different message sizes."""
    conn_params = get_redis_params()

    print("\nBenchmark: Message sizes")
    print("-" * 60)

    # Small message
    class SmallMessage(PubSubMessage):
        """Small Message."""
        value: float = 0.0

    # Large message
    class LargeMessage(PubSubMessage):
        """Large Message."""
        data: str = "x" * 10000  # 10KB

    message_types = [
        (SmallMessage(), "Small (1 field)"),
        (SensorReading(), "Medium (4 fields)"),
        (LargeMessage(), "Large (10KB)"),
    ]

    for message, label in message_types:
        pub = Publisher(
            topic="benchmark.sizes.test",
            msg_type=type(message),
            conn_params=conn_params,
        )
        pub.run(wait=True)

        # Warm up
        for _ in range(20):
            pub.publish(message)

        # Benchmark
        iterations = 200
        start = time.perf_counter()
        for _ in range(iterations):
            pub.publish(message)
        elapsed = time.perf_counter() - start

        throughput = iterations / elapsed
        latency = (elapsed / iterations) * 1000

        print(f"{label:20s}: {latency:7.3f} ms/msg | {throughput:8.0f} msg/sec")

        pub.stop(wait=True)
        time.sleep(0.2)


if __name__ == "__main__":
    print("=" * 60)
    print("Redis Real Server Benchmarks")
    print("=" * 60)

    params = get_redis_params()
    print(f"\nRedis Server: {params.host}:{params.port}")

    if not check_redis_available():
        print("\n❌ Redis server not available!")
        print(f"   Could not connect to {params.host}:{params.port}")
        print("\nTo run these benchmarks, start a Redis server:")
        print("  docker run -d -p 6379:6379 redis:latest")
        print("\nOr set environment variables:")
        print("  export COMMLIB_REDIS_HOST=your-redis-host")
        print("  export COMMLIB_REDIS_PORT=6379")
        sys.exit(1)

    print("✓ Redis server is available\n")

    try:
        print("Benchmark: Publish throughput")
        print("-" * 60)
        benchmark_redis_publish_throughput()

        print("\nBenchmark: Pub/Sub round trip")
        print("-" * 60)
        benchmark_redis_pubsub_roundtrip()

        benchmark_redis_connection_pool_sharing()
        benchmark_redis_concurrent_publishers()
        benchmark_redis_message_sizes()

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
