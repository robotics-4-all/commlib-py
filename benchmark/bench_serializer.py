"""Benchmark serialization performance."""

import time
from decimal import Decimal
from commlib.serializer import JSONSerializer


def benchmark_make_primitives():
    """Benchmark make_primitives with nested structures."""

    def create_nested(depth):
        """Create deeply nested structure."""
        if depth == 0:
            return {
                "value": Decimal("1.23"),
                "tuple": (1, 2, 3),
                "float": 3.14,
                "int": 42,
                "str": "test",
            }
        return {
            "level": depth,
            "nested": create_nested(depth - 1),
            "list": [Decimal("1.1"), Decimal("2.2"), Decimal("3.3")],
        }

    # Test different depths
    depths = [5, 10, 15]
    iterations = 1000

    print("Benchmark: make_primitives")
    print("-" * 60)

    for depth in depths:
        data = create_nested(depth)

        # Warm up
        for _ in range(100):
            JSONSerializer.make_primitives(data)

        # Benchmark
        start = time.perf_counter()
        for _ in range(iterations):
            JSONSerializer.make_primitives(data)
        elapsed = time.perf_counter() - start

        ops_per_sec = iterations / elapsed
        time_per_op = (elapsed / iterations) * 1000  # ms

        print(
            f"Depth {depth:2d}: {time_per_op:7.3f} ms/op | {ops_per_sec:8.0f} ops/sec"
        )


def benchmark_serialization():
    """Benchmark JSON serialization."""

    test_data = {
        "timestamp": 1234567890.123,
        "sensor_id": "temp_sensor_01",
        "readings": [
            {"temp": 23.5, "humidity": 65.2},
            {"temp": 23.7, "humidity": 64.8},
            {"temp": 23.6, "humidity": 65.0},
        ],
        "metadata": {
            "location": "room_A",
            "floor": 3,
            "building": "main",
        },
    }

    iterations = 10000

    print("\nBenchmark: JSON serialization")
    print("-" * 60)

    # Warm up
    for _ in range(1000):
        JSONSerializer.serialize(test_data)

    # Benchmark serialize
    start = time.perf_counter()
    for _ in range(iterations):
        result = JSONSerializer.serialize(test_data)
    elapsed = time.perf_counter() - start

    ops_per_sec = iterations / elapsed
    time_per_op = (elapsed / iterations) * 1000  # ms

    print(f"Serialize:   {time_per_op:7.3f} ms/op | {ops_per_sec:8.0f} ops/sec")

    # Benchmark deserialize
    serialized = JSONSerializer.serialize(test_data)

    # Warm up
    for _ in range(1000):
        JSONSerializer.deserialize(serialized)

    start = time.perf_counter()
    for _ in range(iterations):
        JSONSerializer.deserialize(serialized)
    elapsed = time.perf_counter() - start

    ops_per_sec = iterations / elapsed
    time_per_op = (elapsed / iterations) * 1000  # ms

    print(f"Deserialize: {time_per_op:7.3f} ms/op | {ops_per_sec:8.0f} ops/sec")


def benchmark_round_trip():
    """Benchmark serialize + deserialize round trip."""

    test_data = {
        "id": "msg_12345",
        "type": "sensor_reading",
        "payload": {
            "temperature": Decimal("23.5"),
            "pressure": Decimal("1013.25"),
            "coordinates": (40.7128, -74.0060),  # Will become list
        },
    }

    iterations = 5000

    print("\nBenchmark: Round trip (serialize + deserialize)")
    print("-" * 60)

    # Warm up
    for _ in range(500):
        primitives = JSONSerializer.make_primitives(test_data)
        serialized = JSONSerializer.serialize(primitives)
        deserialized = JSONSerializer.deserialize(serialized)

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        primitives = JSONSerializer.make_primitives(test_data)
        serialized = JSONSerializer.serialize(primitives)
        deserialized = JSONSerializer.deserialize(serialized)
    elapsed = time.perf_counter() - start

    ops_per_sec = iterations / elapsed
    time_per_op = (elapsed / iterations) * 1000  # ms

    print(f"Round trip:  {time_per_op:7.3f} ms/op | {ops_per_sec:8.0f} ops/sec")


if __name__ == "__main__":
    print("=" * 60)
    print("Serializer Performance Benchmarks")
    print("=" * 60)
    print()

    benchmark_make_primitives()
    benchmark_serialization()
    benchmark_round_trip()

    print()
    print("=" * 60)
