import unittest
import zlib
from commlib.compression import CompressionType, inflate_str, deflate, HAS_LZ4

class TestLZ4Compression(unittest.TestCase):
    def test_lz4_compression_decompression(self):
        test_str = "Hello World" * 100
        compressed = inflate_str(test_str, CompressionType.DEFAULT_COMPRESSION)
        self.assertIsInstance(compressed, bytes)
        
        decompressed = deflate(compressed, CompressionType.DEFAULT_COMPRESSION)
        self.assertEqual(decompressed.decode(), test_str)

    def test_lz4_fallback_to_zlib(self):
        # Even if HAS_LZ4 is False, it should work (using zlib)
        test_str = "Fallback Test" * 50
        compressed = inflate_str(test_str, CompressionType.DEFAULT_COMPRESSION)
        decompressed = deflate(compressed, CompressionType.DEFAULT_COMPRESSION)
        self.assertEqual(decompressed.decode(), test_str)
        
        if not HAS_LZ4:
            # Verify it's actually zlib
            self.assertEqual(decompressed, zlib.decompress(compressed))

if __name__ == "__main__":
    unittest.main()
