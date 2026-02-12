#!/usr/bin/env python

"""Advanced — Node Decorators.

Uses ``@node.subscribe`` and ``@node.rpc`` decorators for a concise,
declarative endpoint setup — ideal for simple nodes.

Usage::

    python examples/advanced/decorator_node.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import PubSubMessage, RPCMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class TemperatureReading(PubSubMessage):
    """Temperature Reading."""
    sensor_id: str = ""
    temperature: float = 0.0


class AddTwoIntsMsg(RPCMessage):
    """Add Two Ints Msg."""
    class Request(RPCMessage.Request):
        """Request payload."""
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        """Response payload."""
        result: int = 0


if __name__ == "__main__":
    parser = make_broker_parser("Declarative node with decorators")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="advanced.decorator_node",
        connection_params=conn_params,
        heartbeats=False,
        debug=True,
    )

    @node.subscribe("sensors.temperature", TemperatureReading)
    def on_temperature(msg: TemperatureReading) -> None:
        print(f"[sub] {msg.sensor_id}: {msg.temperature}°C")

    @node.rpc("math.add_two_ints", AddTwoIntsMsg)
    def handle_add(msg: AddTwoIntsMsg.Request) -> AddTwoIntsMsg.Response:
        print(f"[rpc] {msg.a} + {msg.b}")
        return AddTwoIntsMsg.Response(result=msg.a + msg.b)

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever(sleep_rate=1)
