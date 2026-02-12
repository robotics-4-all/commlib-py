#!/usr/bin/env python

"""Edge-to-Cloud — Pattern Topic Bridge.

Bridges all topics matching ``edge.sensors.*`` from one broker to
another using ``PTopicBridge`` for wildcard-based forwarding.

Usage::

    python examples/edge_to_cloud/pattern_bridge.py \\
        --broker-a redis --broker-b mqtt
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params  # noqa: E402

from commlib.bridges import PTopicBridge  # noqa: E402
from commlib.msg import PubSubMessage  # noqa: E402


class GenericSensorMsg(PubSubMessage):
    value: float = 0.0
    unit: str = ""


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wildcard topic bridge (edge -> cloud)",
    )
    parser.add_argument(
        "--broker-a", default="redis", choices=["redis", "amqp", "mqtt", "kafka"]
    )
    parser.add_argument("--host-a", default="localhost")
    parser.add_argument("--port-a", type=int, default=None)
    parser.add_argument(
        "--broker-b", default="mqtt", choices=["redis", "amqp", "mqtt", "kafka"]
    )
    parser.add_argument("--host-b", default="localhost")
    parser.add_argument("--port-b", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()
    edge_params = get_connection_params(args.broker_a, args.host_a, args.port_a)
    cloud_params = get_connection_params(args.broker_b, args.host_b, args.port_b)

    bridge = PTopicBridge(
        from_uri="edge.sensors.*",
        to_uri="cloud",
        from_broker_params=edge_params,
        to_broker_params=cloud_params,
        msg_type=GenericSensorMsg,
    )
    bridge.run()

    print(
        f"[bridge] Pattern edge.sensors.* ({args.broker_a}) "
        f"-> cloud.* ({args.broker_b})"
    )

    try:
        if args.timeout:
            time.sleep(args.timeout)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
