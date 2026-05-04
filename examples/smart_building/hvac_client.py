#!/usr/bin/env python

"""Smart Building — HVAC Control Client (RPC pattern).

Sends temperature adjustment requests to the HVAC service, including an
intentionally out-of-range request to demonstrate error handling.

Usage::

    python examples/smart_building/hvac_client.py --broker redis
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import RPCMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class SetTemperatureMsg(RPCMessage):
    """Set Temperature Msg."""
    class Request(RPCMessage.Request):
        """Request payload."""
        zone: str = "A"
        target_temp: float = 22.0

    class Response(RPCMessage.Response):
        """Response payload."""
        success: bool = False
        current_temp: float = 0.0
        message: str = ""


if __name__ == "__main__":
    parser = make_broker_parser("HVAC temperature control client")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.hvac.client",
        connection_params=conn_params,
        heartbeats=False,
    )
    rpc = node.create_rpc_client(
        msg_type=SetTemperatureMsg,
        rpc_name="building.hvac.set_temperature",
    )
    node.run()

    requests = [
        SetTemperatureMsg.Request(zone="A", target_temp=22.0),
        SetTemperatureMsg.Request(zone="B", target_temp=30.0),
        SetTemperatureMsg.Request(zone="A", target_temp=35.0),
    ]

    for req in requests:
        print(f"[client] Setting zone {req.zone} to {req.target_temp}°C")
        resp = rpc.call(req)
        status = "OK" if resp.success else "REJECTED"
        print(f"  -> [{status}] {resp.message}")
        time.sleep(1)

    node.stop()
