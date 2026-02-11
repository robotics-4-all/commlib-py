#!/usr/bin/env python

"""Smart Building — Sensor Telemetry Subscriber (Pub/Sub pattern).

Subscribes to floor sensor readings published by ``sensor_publisher.py``.

Usage::

    python examples/smart_building/sensor_subscriber.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import PubSubMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class SensorReading(PubSubMessage):
    floor: int = 1
    zone: str = "A"
    temperature: float = 22.0
    humidity: float = 50.0
    ts: float = 0.0


def on_sensor_data(msg: SensorReading) -> None:
    print(
        f"[floor {msg.floor}, zone {msg.zone}] "
        f"temp={msg.temperature}°C  humidity={msg.humidity}%"
    )


if __name__ == "__main__":
    parser = make_broker_parser("Subscribe to floor sensor telemetry")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.monitoring.subscriber",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_subscriber(
        msg_type=SensorReading,
        topic="building.floor1.zone_a.environment",
        on_message=on_sensor_data,
    )

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever(sleep_rate=1)
