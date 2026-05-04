"""Shared helpers for commlib-py examples.

Provides common broker selection and connection parameter setup so that
every example script can be run against any supported broker with a
uniform CLI interface::

    python examples/smart_building/sensor_publisher.py --broker redis
    python examples/smart_building/sensor_publisher.py --broker mqtt --host 10.0.0.5
"""

import argparse
from typing import Any, Optional


def make_broker_parser(description: str = "") -> argparse.ArgumentParser:
    """Return an ``ArgumentParser`` pre-configured with broker options."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--broker",
        type=str,
        default="redis",
        choices=["redis", "amqp", "mqtt", "kafka"],
        help="Message broker type (default: redis)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Broker hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Broker port (omit for protocol default)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Auto-stop after N seconds (default: run forever)",
    )
    return parser


def get_connection_params(
    broker: str, host: str = "localhost", port: Optional[int] = None
) -> Any:
    """Import and return ``ConnectionParameters`` for the chosen broker."""
    ConnectionParameters: type
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters
    else:
        raise ValueError(f"Unsupported broker: {broker}")

    params = ConnectionParameters(host=host)
    if port is not None:
        params.port = port
    return params
