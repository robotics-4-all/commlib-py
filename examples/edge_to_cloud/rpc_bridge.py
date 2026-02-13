#!/usr/bin/env python

"""Edge-to-Cloud — RPC Bridge.

Bridges an RPC endpoint from an edge broker to a cloud broker so that
cloud clients can call edge services transparently.

Usage::

    python examples/edge_to_cloud/rpc_bridge.py \\
        --broker-a redis --broker-b mqtt
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params  # noqa: E402

from commlib.bridges import RPCBridge  # noqa: E402
from commlib.msg import RPCMessage  # noqa: E402


class DeviceStatusMsg(RPCMessage):
    """Device Status Msg."""
    class Request(RPCMessage.Request):
        """Request payload."""
        device_id: str = ""

    class Response(RPCMessage.Response):
        """Response payload."""
        device_id: str = ""
        online: bool = False
        uptime_hours: float = 0.0


def make_parser() -> argparse.ArgumentParser:
    """Make parser."""
    parser = argparse.ArgumentParser(description="Edge-to-cloud RPC bridge")
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

    bridge = RPCBridge(
        msg_type=DeviceStatusMsg,
        from_uri="edge.devices.status",
        to_uri="cloud.devices.status",
        from_broker_params=edge_params,
        to_broker_params=cloud_params,
    )
    bridge.run()

    print(
        f"[bridge] RPC edge.devices.status ({args.broker_a}) "
        f"-> cloud.devices.status ({args.broker_b})"
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
