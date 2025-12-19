#!/usr/bin/env python

"""Tests for commlib compression module."""

import unittest

from commlib.compression import inflate_str, deflate, CompressionType


class TestCompression(unittest.TestCase):
    """Test compression functions."""

    def test_inflate_deflate_string(self):
        """Test compressing and decompressing a string."""
        original = "Hello, World!"
        compressed = inflate_str(original)
        self.assertIsInstance(compressed, bytes)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_inflate_deflate_json_string(self):
        """Test compressing JSON string."""
        original = '{"key": "value", "number": 42}'
        compressed = inflate_str(original)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_inflate_empty_string(self):
        """Test compressing empty string."""
        original = ""
        compressed = inflate_str(original)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_inflate_large_string(self):
        """Test compressing large string."""
        original = "x" * 10000
        compressed = inflate_str(original)
        # Compression should reduce size
        self.assertLess(len(compressed), len(original))
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_inflate_unicode(self):
        """Test compressing unicode characters."""
        original = "Hello, 世界! 🌍"
        compressed = inflate_str(original)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_inflate_multiline_string(self):
        """Test compressing multiline string."""
        original = "Line 1\nLine 2\nLine 3\n" * 100
        compressed = inflate_str(original)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, original)

    def test_compression_types(self):
        """Test different compression types."""
        text = "x" * 1000
        
        # Test NO_COMPRESSION
        no_comp = inflate_str(text, CompressionType.NO_COMPRESSION)
        self.assertEqual(deflate(no_comp).decode(), text)
        
        # Test BEST_SPEED
        best_speed = inflate_str(text, CompressionType.BEST_SPEED)
        self.assertEqual(deflate(best_speed).decode(), text)
        
        # Test BEST_COMPRESSION
        best_comp = inflate_str(text, CompressionType.BEST_COMPRESSION)
        self.assertEqual(deflate(best_comp).decode(), text)
        # BEST_COMPRESSION should produce smaller output than BEST_SPEED
        self.assertLessEqual(len(best_comp), len(best_speed))

    def test_compression_type_default(self):
        """Test default compression type."""
        text = "Default compression test"
        compressed = inflate_str(text)
        decompressed = deflate(compressed).decode()
        self.assertEqual(decompressed, text)


if __name__ == '__main__':
    unittest.main()
