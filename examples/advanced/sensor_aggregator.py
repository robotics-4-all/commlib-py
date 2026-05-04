#!/usr/bin/env python

"""Advanced — Sensor Data Aggregator (TopicAggregator).

Merges data from multiple sensor topics into a single output topic,
with optional per-topic data processors.

Usage::

    python examples/advanced/sensor_aggregator.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.aggregation import TopicAggregator  # noqa: E402


if __name__ == "__main__":
    parser = make_broker_parser("Aggregate multiple sensor topics")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    input_topics = [
        "building.floor1.temperature",
        "building.floor1.humidity",
    ]
    output_topic = "building.floor1.environment_combined"

    processors = {
        "building.floor1.temperature": [
            lambda msg: {
                "temperature_celsius": msg.get("value", 0),
                "source": "floor1_temp_sensor",
            }
        ],
        "building.floor1.humidity": [
            lambda msg: {
                "humidity_pct": msg.get("value", 0),
                "source": "floor1_hum_sensor",
            }
        ],
    }

    aggregator = TopicAggregator(
        conn_params,
        input_topics,
        output_topic,
        data_processors=processors,
    )
    aggregator.start()

    print(f"[aggregator] Merging {input_topics} -> {output_topic}")

    try:
        if args.timeout:
            import time

            time.sleep(args.timeout)
        else:
            import time

            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
