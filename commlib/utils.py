"""Utility functions and helpers.

Provides common utilities for ID generation, string transformation,
and time management.
"""

import os
import re
import time
import uuid
import logging
from rich.logging import RichHandler


def camelcase_to_snakecase(_str: str) -> str:
    """camelcase_to_snakecase.
    Transform a camelcase string to  snakecase

    Args:
        _str (str): String to apply transformation.

    Returns:
        str: Transformed string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", _str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def gen_timestamp() -> int:
    """gen_timestamp.
    Generate a timestamp.

    Args:

    Returns:
        int: Timestamp in integer representation. User `str()` to
            transform to string.
    """
    return time.time_ns()


def get_timestamp_ns() -> int:
    return gen_timestamp()


def get_timestamp_us() -> int:
    return int(gen_timestamp_ns() / 1e3)


def get_timestamp_ms() -> int:
    return int(gen_timestamp_ns() / 1e6)


def gen_random_id() -> str:
    """gen_random_id.
    Generates a random unique id, using the uuid library.

    Args:

    Returns:
        str: String representation of the random unique id
    """
    return str(uuid.uuid4()).replace("-", "")


class Rate:

    def __init__(self, hz: int):
        """__init__.
        Initializes a `Rate` object with the specified Hz (Hertz) rate.

        Args:
            hz (int): The rate in Hertz (Hz) to use for the `Rate` object.

        Attributes:
            _hz (int): The rate in Hertz (Hz) for the `Rate` object.
            _tsleep (float): The time in seconds to sleep between each iteration, calculated as 1.0 / `_hz`.
        """

        self._hz = hz
        self._tsleep = 1.0 / hz

    def sleep(self):
        """sleep.
        Sleeps for the time specified by the `_tsleep` attribute of the `Rate` object.

        This method is used to implement the desired rate specified by the `hz` parameter
        passed to the `Rate` constructor. It ensures that the code execution is paused for
        the appropriate amount of time between each iteration, in order to achieve the
        desired rate.
        """

        time.sleep(self._tsleep)


LOGGING_FORMAT = "%(message)s"
LOG_LEVEL = os.getenv("COMMLIB_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL, format=LOGGING_FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


def topic_to_mqtt(topic: str) -> str:
    """Convert commlib unified topic notation to MQTT format.

    Converts topic from unified notation (a.b.c with * wildcards)
    to MQTT format (a/b/c with +/# wildcards).

    Args:
        topic (str): Topic in unified notation (e.g., "sensors.*.temperature")

    Returns:
        str: Topic in MQTT format (e.g., "sensors/+/temperature")

    Examples:
        >>> topic_to_mqtt("sensors.temperature")
        'sensors/temperature'
        >>> topic_to_mqtt("sensors.*.temperature")
        'sensors/+/temperature'
        >>> topic_to_mqtt("sensors.*")
        'sensors/#'
    """
    # Replace dots with slashes
    mqtt_topic = topic.replace(".", "/")
    
    # Handle wildcards: convert * to appropriate MQTT wildcards
    # - If * is in the middle (surrounded by /), use + (single-level)
    # - If * is at the end (after /), use # (multi-level)
    if mqtt_topic.endswith("/*"):
        # Replace trailing wildcard with multi-level wildcard
        mqtt_topic = mqtt_topic[:-2] + "/#"
    
    # Replace remaining asterisks (middle segments) with single-level wildcard +
    mqtt_topic = mqtt_topic.replace("/*", "/+").replace("*", "+")
    
    return mqtt_topic


def topic_from_mqtt(topic: str) -> str:
    """Convert MQTT topic notation to commlib unified format.

    Converts topic from MQTT format (a/b/c with +/# wildcards)
    to unified notation (a.b.c with * wildcards).

    Args:
        topic (str): Topic in MQTT format (e.g., "sensors/+/temperature")

    Returns:
        str: Topic in unified notation (e.g., "sensors.*.temperature")

    Examples:
        >>> topic_from_mqtt("sensors/temperature")
        'sensors.temperature'
        >>> topic_from_mqtt("sensors/+/temperature")
        'sensors.*.temperature'
        >>> topic_from_mqtt("sensors/#")
        'sensors.*'
    """
    # Replace multi-level wildcard # with *
    commlib_topic = topic.replace("#", "*")
    # Replace single-level wildcard + with *
    commlib_topic = commlib_topic.replace("+", "*")
    # Replace slashes with dots
    commlib_topic = commlib_topic.replace("/", ".")
    return commlib_topic


def topic_to_redis(topic: str) -> str:
    """Convert commlib unified topic notation to Redis format.

    Redis pub/sub uses dot notation similar to commlib, but with
    pattern matching using asterisks. This function converts unified
    notation to Redis pattern format.

    Args:
        topic (str): Topic in unified notation (e.g., "sensors.*.temperature")

    Returns:
        str: Topic in Redis pattern format (e.g., "sensors.*.temperature")

    Examples:
        >>> topic_to_redis("sensors.temperature")
        'sensors.temperature'
        >>> topic_to_redis("sensors.*.temperature")
        'sensors.*.temperature'
    """
    # Redis uses the same dot notation as commlib unified format
    # Asterisks are already in the right format for Redis pattern matching
    return topic


def topic_from_redis(topic: str) -> str:
    """Convert Redis topic notation to commlib unified format.

    Redis uses dot notation similar to commlib, so conversion is minimal.

    Args:
        topic (str): Topic in Redis format (e.g., "sensors.*.temperature")

    Returns:
        str: Topic in unified notation (e.g., "sensors.*.temperature")

    Examples:
        >>> topic_from_redis("sensors.temperature")
        'sensors.temperature'
        >>> topic_from_redis("sensors.*.temperature")
        'sensors.*.temperature'
    """
    # Redis uses the same dot notation as commlib unified format
    return topic


def topic_to_amqp(topic: str) -> str:
    """Convert commlib unified topic notation to AMQP format.

    AMQP uses dot notation for topic-based exchanges (similar to commlib)
    with asterisks for wildcards.

    Args:
        topic (str): Topic in unified notation (e.g., "sensors.*.temperature")

    Returns:
        str: Topic in AMQP format (e.g., "sensors.*.temperature")

    Examples:
        >>> topic_to_amqp("sensors.temperature")
        'sensors.temperature'
        >>> topic_to_amqp("sensors.*.temperature")
        'sensors.*.temperature'
    """
    # AMQP uses the same dot notation as commlib unified format
    # with * for single-level and # for multi-level wildcards
    return topic


def topic_from_amqp(topic: str) -> str:
    """Convert AMQP topic notation to commlib unified format.

    Args:
        topic (str): Topic in AMQP format (e.g., "sensors.*.temperature")

    Returns:
        str: Topic in unified notation (e.g., "sensors.*.temperature")

    Examples:
        >>> topic_from_amqp("sensors.temperature")
        'sensors.temperature'
        >>> topic_from_amqp("sensors.*.temperature")
        'sensors.*.temperature'
    """
    # AMQP uses the same dot notation as commlib unified format
    return topic


def topic_to_kafka(topic: str) -> str:
    """Convert commlib unified topic notation to Kafka format.

    Kafka topics use simple naming without separators or wildcards.
    This function converts unified notation to a flat Kafka topic name.

    Args:
        topic (str): Topic in unified notation (e.g., "sensors.temperature")

    Returns:
        str: Topic name for Kafka (e.g., "sensors-temperature")

    Examples:
        >>> topic_to_kafka("sensors.temperature")
        'sensors-temperature'
        >>> topic_to_kafka("sensors.*.temperature")
        'sensors-*-temperature'
    """
    # Kafka doesn't support hierarchical topics like MQTT or AMQP
    # Convert dots to hyphens for flat topic names
    kafka_topic = topic.replace(".", "-")
    return kafka_topic


def topic_from_kafka(topic: str) -> str:
    """Convert Kafka topic notation to commlib unified format.

    Kafka topics are flat names, so this function converts hyphenated
    names back to dot notation.

    Args:
        topic (str): Topic name in Kafka format (e.g., "sensors-temperature")

    Returns:
        str: Topic in unified notation (e.g., "sensors.temperature")

    Examples:
        >>> topic_from_kafka("sensors-temperature")
        'sensors.temperature'
        >>> topic_from_kafka("sensors-*-temperature")
        'sensors.*.temperature'
    """
    # Convert hyphens back to dots
    commlib_topic = topic.replace("-", ".")
    return commlib_topic


def convert_topic_notation(topic: str, from_protocol: str, to_protocol: str) -> str:
    """Convert topic notation between different protocols.

    Unified notation is: `a.b.c.d` with `*` as wildcard for any segment.

    Supported protocols:
    - 'commlib': Unified dot notation with * wildcards
    - 'mqtt': MQTT format with / separators and +/# wildcards
    - 'redis': Redis pub/sub format (dot notation with * wildcards)
    - 'amqp': AMQP format (dot notation with * and # wildcards)
    - 'kafka': Kafka format (hyphen-separated flat names)

    Args:
        topic (str): Topic in source protocol format
        from_protocol (str): Source protocol ('commlib', 'mqtt', 'redis', 'amqp', 'kafka')
        to_protocol (str): Target protocol ('commlib', 'mqtt', 'redis', 'amqp', 'kafka')

    Returns:
        str: Topic converted to target protocol format

    Raises:
        ValueError: If protocol is not supported

    Examples:
        >>> convert_topic_notation("sensors/+/temperature", "mqtt", "commlib")
        'sensors.*.temperature'
        >>> convert_topic_notation("sensors.*.temperature", "commlib", "mqtt")
        'sensors/+/temperature'
        >>> convert_topic_notation("sensors.temperature", "redis", "mqtt")
        'sensors/temperature'
    """
    supported_protocols = {"commlib", "mqtt", "redis", "amqp", "kafka"}

    if from_protocol not in supported_protocols:
        raise ValueError(f"Unsupported source protocol: {from_protocol}. "
                        f"Must be one of {supported_protocols}")
    if to_protocol not in supported_protocols:
        raise ValueError(f"Unsupported target protocol: {to_protocol}. "
                        f"Must be one of {supported_protocols}")

    # If source and target are the same, return as-is
    if from_protocol == to_protocol:
        return topic

    # Convert from source protocol to commlib unified format
    if from_protocol == "mqtt":
        commlib_topic = topic_from_mqtt(topic)
    elif from_protocol == "redis":
        commlib_topic = topic_from_redis(topic)
    elif from_protocol == "amqp":
        commlib_topic = topic_from_amqp(topic)
    elif from_protocol == "kafka":
        commlib_topic = topic_from_kafka(topic)
    else:  # from_protocol == "commlib"
        commlib_topic = topic

    # Convert from commlib unified format to target protocol
    if to_protocol == "mqtt":
        return topic_to_mqtt(commlib_topic)
    elif to_protocol == "redis":
        return topic_to_redis(commlib_topic)
    elif to_protocol == "amqp":
        return topic_to_amqp(commlib_topic)
    elif to_protocol == "kafka":
        return topic_to_kafka(commlib_topic)
    else:  # to_protocol == "commlib"
        return commlib_topic
