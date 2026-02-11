import unittest
import time
from decimal import Decimal
from commlib.serializer import (
    JSONSerializer,
    BinarySerializer,
    TextSerializer,
    get_json_backend,
)


class TestJSONBackend(unittest.TestCase):
    """Test JSON backend detection."""

    def test_get_json_backend_returns_string(self):
        """Test that get_json_backend returns a string."""
        backend = get_json_backend()
        self.assertIsInstance(backend, str)

    def test_get_json_backend_valid_value(self):
        """Test that backend is one of the expected values."""
        backend = get_json_backend()
        self.assertIn(backend, ["orjson", "ujson", "json"])


class TestJSONSerializer(unittest.TestCase):
    def test_serialize_deserialize_dict(self):
        data = {"a": 1, "b": "test", "c": True}
        serialized = JSONSerializer.serialize(data)
        deserialized = JSONSerializer.deserialize(serialized)
        self.assertEqual(data, deserialized)

    def test_make_primitives(self):
        data = {"a": Decimal("1.5"), "b": (1, 2), "c": None}
        # Decimal should become float, tuple should become list
        expected = {"a": 1.5, "b": [1, 2], "c": None}
        primitives = JSONSerializer.make_primitives(data)
        self.assertEqual(primitives, expected)

    def test_make_primitives_non_mutating(self):
        """Test that make_primitives does not mutate the original data."""
        original = {"a": Decimal("1.5"), "b": (1, 2), "c": {"nested": Decimal("2.5")}}
        original_copy = {
            "a": Decimal("1.5"),
            "b": (1, 2),
            "c": {"nested": Decimal("2.5")},
        }

        # Call make_primitives
        result = JSONSerializer.make_primitives(original)

        # Original should be unchanged
        self.assertEqual(original, original_copy)
        self.assertIsInstance(original["a"], Decimal)
        self.assertIsInstance(original["b"], tuple)
        self.assertIsInstance(original["c"]["nested"], Decimal)  # type: ignore[index]

        # Result should be converted
        self.assertEqual(result["a"], 1.5)
        self.assertIsInstance(result["a"], float)
        self.assertEqual(result["b"], [1, 2])
        self.assertIsInstance(result["b"], list)
        self.assertEqual(result["c"]["nested"], 2.5)
        self.assertIsInstance(result["c"]["nested"], float)

    def test_make_primitives_performance(self):
        """Test performance of make_primitives with nested structures."""

        # Create deeply nested structure (10 levels)
        def create_nested(depth):
            if depth == 0:
                return {"value": Decimal("1.23"), "tuple": (1, 2, 3)}
            return {"level": depth, "nested": create_nested(depth - 1)}

        data = create_nested(10)

        # Warm up
        for _ in range(10):
            JSONSerializer.make_primitives(data)

        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            JSONSerializer.make_primitives(data)
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 1 second for 1000 iterations)
        self.assertLess(
            elapsed,
            1.0,
            f"make_primitives too slow: {elapsed:.3f}s for {iterations} iterations",
        )


class TestBinarySerializer(unittest.TestCase):
    def test_serialize_deserialize(self):
        data = {"a": 1}
        serialized = BinarySerializer.serialize(data)
        self.assertIsInstance(serialized, bytes)
        deserialized = BinarySerializer.deserialize(serialized)
        self.assertEqual(data, deserialized)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            BinarySerializer.serialize("not a dict")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            BinarySerializer.deserialize("not bytes")


class TestTextSerializer(unittest.TestCase):
    def test_serialize_deserialize(self):
        data = "hello world"
        serialized = TextSerializer.serialize(data)
        self.assertEqual(serialized, "hello world")
        deserialized = TextSerializer.deserialize(serialized)
        self.assertEqual(deserialized, data)

    def test_serialize_list(self):
        data = [1, 2, 3]
        serialized = TextSerializer.serialize(data)
        self.assertEqual(serialized, "1,2,3")
        deserialized = TextSerializer.deserialize(serialized)
        self.assertEqual(deserialized, ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
