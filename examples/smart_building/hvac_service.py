#!/usr/bin/env python

"""Smart Building — HVAC Control Service (RPC pattern).

Exposes a ``set_temperature`` RPC that validates target temperature and
returns the new HVAC state.  Pair with ``hvac_client.py``.

Usage::

    python examples/smart_building/hvac_service.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import RPCMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class SetTemperatureMsg(RPCMessage):
    class Request(RPCMessage.Request):
        zone: str = "A"
        target_temp: float = 22.0

    class Response(RPCMessage.Response):
        success: bool = False
        current_temp: float = 0.0
        message: str = ""


CURRENT_TEMPS = {"A": 21.5, "B": 23.0, "C": 19.8}


def handle_set_temperature(
    msg: SetTemperatureMsg.Request,
) -> SetTemperatureMsg.Response:
    zone = msg.zone
    target = msg.target_temp

    if target < 16.0 or target > 30.0:
        return SetTemperatureMsg.Response(
            success=False,
            current_temp=CURRENT_TEMPS.get(zone, 0.0),
            message=f"Target {target}°C out of range [16-30]",
        )

    CURRENT_TEMPS[zone] = target
    print(f"[hvac] Zone {zone} -> {target}°C")
    return SetTemperatureMsg.Response(
        success=True,
        current_temp=target,
        message=f"Zone {zone} set to {target}°C",
    )


if __name__ == "__main__":
    parser = make_broker_parser("HVAC temperature control service")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.hvac.controller",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_rpc(
        msg_type=SetTemperatureMsg,
        rpc_name="building.hvac.set_temperature",
        on_request=handle_set_temperature,
    )

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
