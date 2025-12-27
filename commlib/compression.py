"""Data compression utilities.

Provides compression types and functions for deflating and inflating message content.
Supports various compression levels for optimized performance.
"""

import zlib


try:
    import lz4.frame as clib
    HAS_LZ4 = True
except ImportError:
    import zlib as clib
    HAS_LZ4 = False


class CompressionType:
    """CompressionType.

    - NO_COMPRESSION
    - BEST_SPEED
    - BEST_COMPRESSION
    - DEFAULT_COMPRESSION
    """

    NO_COMPRESSION = 0
    BEST_SPEED = zlib.Z_BEST_SPEED
    BEST_COMPRESSION = zlib.Z_BEST_COMPRESSION
    DEFAULT_COMPRESSION = zlib.Z_DEFAULT_COMPRESSION


def inflate_str(text: str, compression_type: int = CompressionType.DEFAULT_COMPRESSION):
    """inflate_str.

    Args:
        text (str): text
        compression_type (int): compression_type
    """
    if compression_type == CompressionType.NO_COMPRESSION:
        return zlib.compress(text.encode(), 0)
    if HAS_LZ4:
        return clib.compress(text.encode())
    return zlib.compress(text.encode(), compression_type)


def deflate(data: bytes, compression_type: int = CompressionType.DEFAULT_COMPRESSION):
    """deflate.

    Args:
        data (bytes): data
        compression_type (int): compression_type
    """
    try:
        return clib.decompress(data)
    except Exception:
        if HAS_LZ4:
            return zlib.decompress(data)
        raise
