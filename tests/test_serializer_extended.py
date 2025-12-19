#!/usr/bin/env python

"""Extended tests for serializer module."""

import unittest
from decimal import Decimal

from commlib.serializer import JSONSerializer, BinarySerializer, TextSerializer, Serializer


class TestSerializerBase(unittest.TestCase):
    """Test base Serializer class."""

    def test_serializer_is_abstract(self):
        """Test that Serializer has abstract methods."""
        self.assertTrue(hasattr(Serializer, 'serialize'))
        self.assertTrue(hasattr(Serializer, 'deserialize'))


class TestJSONSerializerExtended(unittest.TestCase):
    """Extended tests for JSONSerializer."""

    def test_serialize_dict(self):
        """Test serializing dictionary."""
        data = {'a': 1, 'b': 2}
        result = JSONSerializer.serialize(data)
        self.assertIsInstance(result, str)

    def test_deserialize_dict(self):
        """Test deserializing dictionary."""
        json_str = '{"a": 1, "b": 2}'
        result = JSONSerializer.deserialize(json_str)
        self.assertEqual(result, {'a': 1, 'b': 2})

    def test_serialize_list(self):
        """Test serializing dict with list."""
        data = {'items': [1, 2, 3, 4, 5]}
        result = JSONSerializer.serialize(data)
        self.assertIsInstance(result, str)

    def test_deserialize_list(self):
        """Test deserializing list."""
        json_str = '[1, 2, 3, 4, 5]'
        result = JSONSerializer.deserialize(json_str)
        self.assertEqual(result, [1, 2, 3, 4, 5])

    def test_serialize_nested_structure(self):
        """Test serializing nested structure."""
        data = {
            'users': [
                {'name': 'Alice', 'age': 30},
                {'name': 'Bob', 'age': 25}
            ],
            'count': 2
        }
        result = JSONSerializer.serialize(data)
        deserialized = JSONSerializer.deserialize(result)
        self.assertEqual(deserialized, data)

    def test_make_primitives_dict(self):
        """Test make_primitives with dict."""
        data = {
            'a': Decimal('1.5'),
            'b': (1, 2),
            'c': None,
            'd': True
        }
        result = JSONSerializer.make_primitives(data)
        self.assertEqual(result['a'], 1.5)
        self.assertEqual(result['b'], [1, 2])
        self.assertIsNone(result['c'])
        self.assertTrue(result['d'])

    def test_make_primitives_list(self):
        """Test make_primitives with dict containing list."""
        data = {
            'items': [Decimal('1.5'), (1, 2), None]
        }
        result = JSONSerializer.make_primitives(data)
        self.assertEqual(result['items'][0], 1.5)
        self.assertEqual(result['items'][1], [1, 2])
        self.assertIsNone(result['items'][2])

    def test_make_primitives_set(self):
        """Test make_primitives with dict containing set."""
        data = {
            'items': {1, 2, 3}
        }
        result = JSONSerializer.make_primitives(data)
        # Sets are converted to strings by make_primitive_value
        self.assertIsInstance(result['items'], str)
        # The string representation contains all the set elements
        self.assertIn('1', result['items'])
        self.assertIn('2', result['items'])
        self.assertIn('3', result['items'])


class TestBinarySerializerExtended(unittest.TestCase):
    """Extended tests for BinarySerializer."""

    def test_serialize_dict(self):
        """Test serializing dictionary to binary."""
        data = {'key': 'value', 'number': 42}
        result = BinarySerializer.serialize(data)
        self.assertIsInstance(result, bytes)

    def test_deserialize_binary(self):
        """Test deserializing binary data."""
        data = {'key': 'value', 'number': 42}
        serialized = BinarySerializer.serialize(data)
        deserialized = BinarySerializer.deserialize(serialized)
        self.assertEqual(deserialized, data)

    def test_serialize_list(self):
        """Test serializing list to binary."""
        data = {'items': [1, 2, 3]}
        result = BinarySerializer.serialize(data)
        self.assertIsInstance(result, bytes)

    def test_invalid_serialize_type(self):
        """Test that serializing invalid types raises error."""
        with self.assertRaises(ValueError):
            BinarySerializer.serialize("not a dict")

    def test_invalid_deserialize_type(self):
        """Test that deserializing invalid types raises error."""
        with self.assertRaises(ValueError):
            BinarySerializer.deserialize("not bytes")

    def test_roundtrip(self):
        """Test serialize-deserialize roundtrip."""
        data = {'a': 1, 'b': [1, 2, 3], 'c': {'nested': True}}
        serialized = BinarySerializer.serialize(data)
        deserialized = BinarySerializer.deserialize(serialized)
        self.assertEqual(deserialized, data)


class TestTextSerializerExtended(unittest.TestCase):
    """Extended tests for TextSerializer."""

    def test_serialize_string(self):
        """Test serializing string."""
        data = "hello world"
        result = TextSerializer.serialize(data)
        self.assertEqual(result, "hello world")

    def test_deserialize_string(self):
        """Test deserializing string."""
        result = TextSerializer.deserialize("hello world")
        self.assertEqual(result, "hello world")

    def test_serialize_list(self):
        """Test serializing list."""
        data = [1, 2, 3]
        result = TextSerializer.serialize(data)
        self.assertEqual(result, "1,2,3")

    def test_deserialize_list(self):
        """Test deserializing list."""
        result = TextSerializer.deserialize("1,2,3")
        self.assertEqual(result, ["1", "2", "3"])

    def test_serialize_number(self):
        """Test serializing number."""
        result = TextSerializer.serialize(42)
        self.assertEqual(result, "42")

    def test_serialize_empty_list(self):
        """Test serializing empty list."""
        result = TextSerializer.serialize([])
        self.assertEqual(result, "")

    def test_deserialize_empty_string(self):
        """Test deserializing empty string."""
        result = TextSerializer.deserialize("")
        # Empty string without comma returns the string itself
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
