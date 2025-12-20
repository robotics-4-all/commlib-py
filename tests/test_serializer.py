import unittest
from decimal import Decimal
from commlib.serializer import JSONSerializer, BinarySerializer, TextSerializer


class TestJSONSerializer(unittest.TestCase):
    def test_serialize_deserialize_dict(self):
        data = {'a': 1, 'b': 'test', 'c': True}
        serialized = JSONSerializer.serialize(data)
        deserialized = JSONSerializer.deserialize(serialized)
        self.assertEqual(data, deserialized)

    def test_make_primitives(self):
        data = {
            'a': Decimal('1.5'),
            'b': (1, 2),
            'c': None
        }
        # Decimal should become float, tuple should become list
        expected = {
            'a': 1.5,
            'b': [1, 2],
            'c': None
        }
        primitives = JSONSerializer.make_primitives(data)
        self.assertEqual(primitives, expected)


class TestBinarySerializer(unittest.TestCase):
    def test_serialize_deserialize(self):
        data = {'a': 1}
        serialized = BinarySerializer.serialize(data)
        self.assertIsInstance(serialized, bytes)
        deserialized = BinarySerializer.deserialize(serialized)
        self.assertEqual(data, deserialized)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            BinarySerializer.serialize("not a dict")
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

if __name__ == '__main__':
    unittest.main()
