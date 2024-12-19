#!/usr/bin/env python

import sys
import time

from commlib.msg import RPCMessage
from commlib.node import Node


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


def add_two_int_handler(msg):
    print(f"Request Message: {msg.__dict__}")
    resp = AddTwoIntMessage.Response(c=msg.a + msg.b)
    return resp


if __name__ == "__main__":
    if len(sys.argv) < 2:
        broker = "redis"
    else:
        broker = str(sys.argv[1])
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="add_two_ints_node",
        connection_params=conn_params,
        heartbeats=False,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )

    rpc = node.create_rpc(
        msg_type=AddTwoIntMessage,
        rpc_name="add_two_ints_node.add_two_ints",
        on_request=add_two_int_handler,
    )

    node.run_forever()
