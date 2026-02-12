#!/usr/bin/env python

"""Smart Building — Sensor Telemetry Publisher (Pub/Sub pattern).

A building floor sensor node publishes temperature and humidity readings
to the broker.  Run alongside ``sensor_subscriber.py`` to see the data
flow end-to-end.

Usage::

    python examples/smart_building/sensor_publisher.py --broker redis
"""

import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import PubSubMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class SensorReading(PubSubMessage):
    floor: int = 1
    zone: str = "A"
    temperature: float = 22.0
    humidity: float = 50.0
    ts: float = 0.0


if __name__ == "__main__":
    parser = make_broker_parser("Publish floor sensor telemetry")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.floor1.sensor_node",
        connection_params=conn_params,
        heartbeats=False,
    )
    pub = node.create_publisher(
        msg_type=SensorReading,
        topic="building.floor1.zone_a.environment",
    )
    node.run()

    start = time.time()
    try:
        while True:
            if args.timeout and time.time() - start > args.timeout:
                break
            msg = SensorReading(
                floor=1,
                zone="A",
                temperature=round(20.0 + random.uniform(0, 5), 2),
                humidity=round(40.0 + random.uniform(0, 20), 2),
                ts=time.time(),
            )
            pub.publish(msg)
            print(f"[sensor] {msg.temperature}°C  {msg.humidity}% RH")
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
