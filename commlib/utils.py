import re
import uuid
import time

from typing import (Any, Callable, Dict, List, Optional, Tuple, Type,
                    TypeVar, Union, Text)


def camelcase_to_snakecase(_str: str) -> str:
    """camelcase_to_snakecase.
    Transform a camelcase string to  snakecase

    Args:
        _str (str): String to apply transformation.

    Returns:
        str: Transformed string
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', _str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def gen_timestamp() -> int:
    """gen_timestamp.
    Generate a timestamp.

    Args:

    Returns:
        int: Timestamp in integer representation. User `str()` to
            transform to string.
    """
    return int(1.0 * (time.time() + 0.5) * 1000)


def gen_random_id() -> str:
    """gen_random_id.
    Generates a random unique id, using the uuid library.

    Args:

    Returns:
        str: String representation of the random unique id
    """
    return str(uuid.uuid4()).replace('-', '')


class Rate:
    def __init__(self, hz: int):
        self._hz = hz
        self._tsleep = 1.0 / hz

    def sleep(self):
        time.sleep(self._tsleep)
