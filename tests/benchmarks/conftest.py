"""
Shared pytest fixtures for benchmark integration tests.

Provides broker availability checking to skip tests when brokers are not running.
"""

import pytest
import socket
import os


def is_broker_available(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a broker is available by attempting a TCP connection.

    Args:
        host: Broker hostname or IP address
        port: Broker port number
        timeout: Connection timeout in seconds

    Returns:
        bool: True if broker is reachable, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def mqtt_available():
    """Check if MQTT broker is available and skip test if not.

    Uses environment variables:
        COMMLIB_MQTT_HOST (default: localhost)
        COMMLIB_MQTT_PORT (default: 1883)
    """
    host = os.getenv("COMMLIB_MQTT_HOST", "localhost")
    port = int(os.getenv("COMMLIB_MQTT_PORT", "1883"))

    if not is_broker_available(host, port):
        pytest.skip(f"MQTT broker not available at {host}:{port}")

    return True


@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis broker is available and skip test if not.

    Uses environment variables:
        COMMLIB_REDIS_HOST (default: localhost)
        COMMLIB_REDIS_PORT (default: 6379)
    """
    host = os.getenv("COMMLIB_REDIS_HOST", "localhost")
    port = int(os.getenv("COMMLIB_REDIS_PORT", "6379"))

    if not is_broker_available(host, port):
        pytest.skip(f"Redis broker not available at {host}:{port}")

    return True


@pytest.fixture(scope="session")
def amqp_available():
    """Check if AMQP broker (RabbitMQ) is available and skip test if not.

    Uses environment variables:
        COMMLIB_AMQP_HOST (default: localhost)
        COMMLIB_AMQP_PORT (default: 5672)
    """
    host = os.getenv("COMMLIB_AMQP_HOST", "localhost")
    port = int(os.getenv("COMMLIB_AMQP_PORT", "5672"))

    if not is_broker_available(host, port):
        pytest.skip(f"AMQP broker not available at {host}:{port}")

    return True
