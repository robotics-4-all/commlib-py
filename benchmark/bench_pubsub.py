"""Benchmark pub/sub performance with mock transport."""

import time
from commlib.msg import PubSubMessage
from commlib.transports.mock import (
    Publisher,
    Subscriber,
    ConnectionParameters,
    clear_mock_bus,
)


class SensorReading(PubSubMessage):
    """Example message for benchmarking."""

    temperature: float = 23.5
    humidity: float = 65.0
    pressure: float = 1013.25
    timestamp: float = 0.0


def benchmark_publish_throughput():
    """Benchmark publisher throughput."""
    clear_mock_bus()
    conn_params = ConnectionParameters()

    # Create publisher
    pub = Publisher(
        topic="sensors.temperature",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run()

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    # Warm up
    for _ in range(1000):
        pub.publish(message)

    # Benchmark
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000  # ms

    pub.stop()

    print(f"Publish:     {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    return throughput


def benchmark_pubsub_roundtrip():
    """Benchmark pub/sub round trip with message delivery."""
    clear_mock_bus()
    conn_params = ConnectionParameters()

    message_count = [0]

    def on_message(_msg):
        message_count[0] += 1

    # Create subscriber
    sub = Subscriber(
        topic="sensors.temperature",
        msg_type=SensorReading,
        on_message=on_message,
        conn_params=conn_params,
    )
    sub.run()

    # Create publisher
    pub = Publisher(
        topic="sensors.temperature",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run()

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    # Warm up
    for _ in range(100):
        pub.publish(message)

    # Reset counter
    message_count[0] = 0

    # Benchmark
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000  # ms

    pub.stop()
    sub.stop()

    print(f"Pub+Sub:     {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    print(f"Messages delivered: {message_count[0]}/{iterations}")

    return throughput


def benchmark_multiple_subscribers():
    """Benchmark one publisher with multiple subscribers."""
    clear_mock_bus()
    conn_params = ConnectionParameters()

    num_subscribers = 10
    message_counts = [[0] for _ in range(num_subscribers)]

    subscribers = []
    for i in range(num_subscribers):

        def on_message(_msg, idx=i):
            message_counts[idx][0] += 1

        sub = Subscriber(
            topic="sensors.temperature",
            msg_type=SensorReading,
            on_message=on_message,
            conn_params=conn_params,
        )
        sub.run()
        subscribers.append(sub)

    # Create publisher
    pub = Publisher(
        topic="sensors.temperature",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run()

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    # Warm up
    for _ in range(100):
        pub.publish(message)

    # Reset counters
    for count in message_counts:
        count[0] = 0

    # Benchmark
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000  # ms

    pub.stop()
    for sub in subscribers:
        sub.stop()

    total_delivered = sum(count[0] for count in message_counts)

    print(f"\nMultiple subscribers ({num_subscribers} subscribers):")
    print(f"  Publish:   {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    print(
        f"  Delivered: {total_delivered} total"
        f" ({total_delivered / num_subscribers:.0f}"
        " per subscriber)"
    )

    return throughput


def benchmark_message_types():
    """Benchmark different message types and sizes."""
    clear_mock_bus()
    conn_params = ConnectionParameters()

    print("\nBenchmark: Message size impact")
    print("-" * 60)

    # Small message
    class SmallMessage(PubSubMessage):
        value: float = 0.0

    # Medium message
    class MediumMessage(PubSubMessage):
        values: list = [0.0] * 50

    # Large message
    class LargeMessage(PubSubMessage):
        values: list = [0.0] * 500

    message_types = [
        (SmallMessage, "Small (1 field)"),
        (SensorReading, "Medium (4 fields)"),
        (MediumMessage, "Large (50 fields)"),
        (LargeMessage, "XLarge (500 fields)"),
    ]

    for msg_type, label in message_types:
        pub = Publisher(
            topic="test.data",
            msg_type=msg_type,
            conn_params=conn_params,
        )
        pub.run()

        message = msg_type()

        # Warm up
        for _ in range(100):
            pub.publish(message)

        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            pub.publish(message)
        elapsed = time.perf_counter() - start

        throughput = iterations / elapsed
        latency = (elapsed / iterations) * 1000  # ms

        print(f"{label:20s}: {latency:7.3f} ms/msg | {throughput:8.0f} msg/sec")

        pub.stop()
        clear_mock_bus()


if __name__ == "__main__":
    print("=" * 60)
    print("Pub/Sub Performance Benchmarks (Mock Transport)")
    print("=" * 60)
    print()

    print("Benchmark: Publish throughput")
    print("-" * 60)
    benchmark_publish_throughput()

    print()
    print("Benchmark: Pub/Sub round trip")
    print("-" * 60)
    benchmark_pubsub_roundtrip()

    benchmark_multiple_subscribers()
    benchmark_message_types()

    print()
    print("=" * 60)
