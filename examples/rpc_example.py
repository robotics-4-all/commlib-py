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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import (
            RPCService, RPCClient, ConnectionParameters
        )
    elif broker == 'amqp':
        from commlib.transports.amqp import (
            RPCService, RPCClient, ConnectionParameters
        )
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)

    rpc_name = 'example_rpc_service'

    conn_params = ConnectionParameters()

    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     conn_params=conn_params,
                     on_request=add_two_int_handler)
    rpc.run()
    time.sleep(1)

    client = RPCClient(rpc_name=rpc_name, msg_type=AddTwoIntMessage,
                       conn_params=conn_params)
    msg = AddTwoIntMessage.Request(a=1, b=2)
    resp = client.call(msg)
    print(f'Response Message: {resp}')
