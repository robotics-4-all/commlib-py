"""Real MQTT broker benchmarks.

Requires running MQTT broker (mosquitto):
  docker run -d -p 1883:1883 eclipse-mosquitto:latest mosquitto -c /mosquitto-no-auth.conf

Or use existing broker via environment variables:
  export COMMLIB_MQTT_HOST=localhost
  export COMMLIB_MQTT_PORT=1883
"""

import os
import sys
import time
from commlib.msg import PubSubMessage
from commlib.transports.mqtt import Publisher, Subscriber, ConnectionParameters


class SensorReading(PubSubMessage):
    """Example sensor message."""

    temperature: float = 23.5
    humidity: float = 65.0
    pressure: float = 1013.25
    timestamp: float = 0.0


def get_mqtt_params():
    """Get MQTT connection parameters from environment or defaults."""
    host = os.getenv("COMMLIB_MQTT_HOST", "localhost")
    port = int(os.getenv("COMMLIB_MQTT_PORT", "1883"))
    return ConnectionParameters(host=host, port=port)


def check_mqtt_available():
    """Check if MQTT broker is available."""
    import socket

    params = get_mqtt_params()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((params.host, params.port))
        sock.close()
        return result == 0
    except Exception:
        return False


def benchmark_mqtt_publish_throughput(iterations=1000, warmup=100):
    """Benchmark MQTT publisher throughput.

    Args:
        iterations: Number of messages to publish for the benchmark
        warmup: Number of warmup messages to publish before benchmark

    Returns:
        float: Throughput in messages per second
    """
    conn_params = get_mqtt_params()

    print("Setting up MQTT publisher...")
    pub = Publisher(
        topic="benchmark/sensors/temperature",
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

    print(f"MQTT Publish:  {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    return throughput


def benchmark_mqtt_pubsub_roundtrip(iterations=100, warmup=50):
    """Benchmark MQTT pub/sub round trip.

    Args:
        iterations: Number of messages to publish for the benchmark
        warmup: Number of warmup messages to publish before benchmark

    Returns:
        float: Throughput in messages per second
    """
    conn_params = get_mqtt_params()

    message_count = [0]
    received_messages = []

    def on_message(msg):
        message_count[0] += 1
        received_messages.append(msg)

    print("\nSetting up MQTT subscriber...")
    sub = Subscriber(
        topic="benchmark/sensors/temperature",
        msg_type=SensorReading,
        on_message=on_message,
        conn_params=conn_params,
    )
    sub.run(wait=True)
    time.sleep(0.5)  # Wait for subscription to be ready

    print("Setting up MQTT publisher...")
    pub = Publisher(
        topic="benchmark/sensors/temperature",
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
    for _i in range(iterations):
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
    sub.stop(wait=True)

    print(f"MQTT Pub+Sub:  {latency:7.3f} ms/msg | {throughput:10.0f} msg/sec")
    print(f"Messages delivered: {message_count[0]}/{iterations}")

    return throughput


def benchmark_mqtt_qos_levels():
    """Benchmark MQTT publish throughput.

    Note: QoS levels are not configurable via Publisher API in current version.
    Publisher uses QoS 0 by default (hardcoded in transport layer).
    """
    conn_params = get_mqtt_params()

    print("\nBenchmark: MQTT Publish (QoS 0 - default)")
    print("-" * 60)

    message = SensorReading(
        temperature=23.5,
        humidity=65.0,
        pressure=1013.25,
        timestamp=time.time(),
    )

    pub = Publisher(
        topic="benchmark/qos/test",
        msg_type=SensorReading,
        conn_params=conn_params,
    )
    pub.run(wait=True)

    # Warm up
    for _ in range(50):
        pub.publish(message)

    # Benchmark
    iterations = 500
    start = time.perf_counter()
    for _ in range(iterations):
        pub.publish(message)
    elapsed = time.perf_counter() - start

    throughput = iterations / elapsed
    latency = (elapsed / iterations) * 1000

    print(
        f"{'QoS 0 (At most once)':25s}: {latency:7.3f} ms/msg | {throughput:8.0f} msg/sec"
    )

    pub.stop(wait=True)
    time.sleep(0.2)


def benchmark_mqtt_concurrent_publishers(
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
    conn_params = get_mqtt_params()

    print(f"\nBenchmark: {num_publishers} concurrent publishers")
    print("-" * 60)

    publishers = []
    for i in range(num_publishers):
        pub = Publisher(
            topic=f"benchmark/concurrent/pub{i}",
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


if __name__ == "__main__":
    print("=" * 60)
    print("MQTT Real Broker Benchmarks")
    print("=" * 60)

    params = get_mqtt_params()
    print(f"\nMQTT Broker: {params.host}:{params.port}")

    if not check_mqtt_available():
        print("\n❌ MQTT broker not available!")
        print(f"   Could not connect to {params.host}:{params.port}")
        print("\nTo run these benchmarks, start an MQTT broker:")
        print("  docker run -d -p 1883:1883 eclipse-mosquitto:latest \\")
        print("    mosquitto -c /mosquitto-no-auth.conf")
        print("\nOr set environment variables:")
        print("  export COMMLIB_MQTT_HOST=your-broker-host")
        print("  export COMMLIB_MQTT_PORT=1883")
        sys.exit(1)

    print("✓ MQTT broker is available\n")

    try:
        print("Benchmark: Publish throughput")
        print("-" * 60)
        benchmark_mqtt_publish_throughput()

        print("\nBenchmark: Pub/Sub round trip")
        print("-" * 60)
        benchmark_mqtt_pubsub_roundtrip()

        benchmark_mqtt_qos_levels()
        benchmark_mqtt_concurrent_publishers()

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
