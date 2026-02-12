#!/usr/bin/env python

"""Robot Fleet — Fleet Operations Monitor (Wildcard PSubscriber pattern).

Subscribes to ``fleet.*.telemetry`` to monitor all robots in the fleet
from a single subscription using pattern-based topic matching.

Usage::

    python examples/robot_fleet/fleet_monitor.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.node import Node  # noqa: E402


def on_robot_telemetry(msg, topic: str) -> None:
    print(f"[monitor] <{topic}> {msg}")


if __name__ == "__main__":
    parser = make_broker_parser("Monitor all robots in the fleet")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="fleet.operations_center",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_psubscriber(
        topic="fleet.*.telemetry",
        on_message=on_robot_telemetry,
    )

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever(sleep_rate=1)
