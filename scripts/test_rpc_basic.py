#!/usr/bin/env python
"""Basic RPC transport integration test script."""
import time
import argparse

from commlib.msg import RPCMessage
from commlib.node import Node


class AddTwoInts(RPCMessage):
    """Add Two Ints."""

    class Request(RPCMessage.Request):
        """Request payload."""

        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        """Response payload."""

        c: int = 0


def main():
    """Main."""
    parser = argparse.ArgumentParser(description="Test RPC communication")
    parser.add_argument(
        "--broker",
        type=str,
        default="redis",
        choices=["redis", "amqp", "mqtt", "kafka"],
        help="Broker type",
    )
    parser.add_argument(
        "--rpc-name",
        type=str,
        default="test.rpc.add_two_ints",
        help="RPC name to use",
    )
    parser.add_argument(
        "--count", type=int, default=5, help="Number of RPC calls to make"
    )

    args = parser.parse_args()

    broker = args.broker

    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters

    print(f"Connecting to {broker} broker...")

    conn_params = ConnectionParameters()

    node = Node(
        node_name="test_rpc_node", connection_params=conn_params, heartbeats=False
    )

    def on_request(msg: AddTwoInts.Request):
        print(f"Server received request: a={msg.a}, b={msg.b}")
        return AddTwoInts.Response(c=msg.a + msg.b)

    _rpc_service = node.create_rpc(
        msg_type=AddTwoInts, rpc_name=args.rpc_name, on_request=on_request
    )

    rpc_client = node.create_rpc_client(msg_type=AddTwoInts, rpc_name=args.rpc_name)

    node.run()

    # Wait for connection/initialization
    time.sleep(1)

    print(f"Making {args.count} RPC calls to {args.rpc_name}...")

    success_count = 0
    for i in range(args.count):
        a = i
        b = i * 2
        req = AddTwoInts.Request(a=a, b=b)
        try:
            print(f"Client sending request: a={a}, b={b}")
            resp = rpc_client.call(req, timeout=5.0)
            print(f"Client received response: c={resp.c}")

            if resp.c == a + b:
                success_count += 1
            else:
                print(f"FAILURE: Expected {a + b}, got {resp.c}")
        except Exception as e:
            print(f"FAILURE: RPC call failed: {e}")

        time.sleep(0.1)

    if success_count == args.count:
        print(f"SUCCESS: {success_count}/{args.count} RPC calls successful.")
    else:
        print(f"FAILURE: {success_count}/{args.count} RPC calls successful.")

    node.stop()


if __name__ == "__main__":
    main()
