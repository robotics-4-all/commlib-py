#!/usr/bin/env python

import sys
import time

from commlib.msg import RPCMessage, DataClass


class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


def add_two_int_handler(msg):
    print(f'Request Message: {msg}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp


def run_amqp(rpc_name):
    from commlib.transports.amqp import (
        RPCService, RPCClient, ConnectionParameters
    )
    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     on_request=add_two_int_handler)
    rpc.run()
    time.sleep(1)

    client = RPCClient(rpc_name=rpc_name, msg_type=AddTwoIntMessage)
    msg = AddTwoIntMessage.Request(a=1, b=2)
    resp = client.call(msg)
    print(resp)

def run_redis(rpc_name):
    from commlib.transports.redis import (
        RPCService, RPCClient, ConnectionParameters
    )
    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     on_request=add_two_int_handler)
    rpc.run()
    time.sleep(1)

    client = RPCClient(rpc_name=rpc_name, msg_type=AddTwoIntMessage)
    msg = AddTwoIntMessage.Request(a=1, b=2)
    resp = client.call(msg)
    print(resp)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    rpc_name = 'example_rpc_service'
    if broker == 'amqp':
        run_amqp(rpc_name)
    elif broker == 'redis':
        run_redis(rpc_name)
