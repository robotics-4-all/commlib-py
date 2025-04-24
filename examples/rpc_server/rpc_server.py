#!/usr/bin/env python

import sys

from commlib.msg import RPCMessage
from commlib.node import Node


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


class MultiplyIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


def multiply_int_handler(msg):
    print(f"Request Message: {msg}")
    resp = MultiplyIntMessage.Response(c=msg.a * msg.b)
    return resp


def add_two_int_handler(msg):
    print(f"Request Message: {msg}")
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
        raise ValueError("Not yet supported")
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="my_rpc_server_node",
        connection_params=conn_params,
        heartbeats=False,
    )

    base_uri = "rpcserver.example.com"
    svc_map = {
        "add_two_ints": (add_two_int_handler, AddTwoIntMessage),
        "multiply_ints": (multiply_int_handler, MultiplyIntMessage),
    }

    # Create the RPC server. Preregister the RPC endpoints via the svc_map.
    # The svc_map is a dictionary where the key is the RPC name and the value is a tuple
    # containing the handler function and the message type.
    # The base_uri is the base URI for the RPC server.
    # The workers parameter specifies the number of worker threads to use for handling requests.
    server = node.create_rpc_server(base_uri=base_uri, svc_map=svc_map, workers=4)
    # Register the RPC endpoints with the server.
    # server.register_endpoint("multiply_ints", multiply_int_handler, MultiplyIntMessage)
    server.run_forever()
