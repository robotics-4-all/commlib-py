#!/usr/bin/env python

import time

from commlib.msg import RPCMessage, DataClass
from commlib.transports.redis import RPCService, RPCClient, ConnectionParameters


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


if __name__ == '__main__':
    rpc_name = 'example_rpc_service'
    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     on_request=add_two_int_handler)
    rpc.run()

    client = RPCClient(rpc_name=rpc_name, msg_type=AddTwoIntMessage)
    msg = AddTwoIntMessage.Request(a=1, b=2)
    resp = client.call(msg)
    print(resp)
    while True:
        time.sleep(0.001)

