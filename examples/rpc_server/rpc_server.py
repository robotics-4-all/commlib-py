#!/usr/bin/env python

import sys

from commlib.msg import RPCMessage


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
        raise ValueError("Not yet supported")
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        raise ValueError("Not yet supported")
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters, RPCServer
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    svc_map = {
        "add_two_ints": (add_two_int_handler, AddTwoIntMessage),
        "multiply_ints": (multiply_int_handler, MultiplyIntMessage),
    }
    base_uri = "rpcserver.test"

    server = RPCServer(base_uri=base_uri, svc_map=svc_map, conn_params=conn_params)
    server.run_forever()
