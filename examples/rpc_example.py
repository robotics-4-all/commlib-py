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


def add_two_int_handler_dict(msg):
    print(f'Request Message: {msg}')
    resp = {
        'c': msg['a'] + msg['b']
    }
    return resp


def client_onrespone(msg):
    print('[*] - Client async onresponse callback')
    print(msg)


def run_with_msg(RPCService, RPCClient, conn_params):
    rpc_name = 'example_rpc_service'

    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     conn_params=conn_params,
                     on_request=add_two_int_handler)
    rpc.run()
    time.sleep(1)

    client = RPCClient(rpc_name=rpc_name,
                       msg_type=AddTwoIntMessage,
                       conn_params=conn_params)
    msg = AddTwoIntMessage.Request(a=1, b=2)

    while True:
        resp = client.call(msg)
        print(f'Response Message: {resp}')
        client.call_async(msg, on_response=client_onrespone)
        time.sleep(2)


def run_with_dict(RPCService, RPCClient, conn_params):
    rpc_name = 'example_rpc_service'

    rpc = RPCService(rpc_name=rpc_name,
                     conn_params=conn_params,
                     on_request=add_two_int_handler_dict)
    rpc.run()
    time.sleep(1)

    client = RPCClient(rpc_name=rpc_name,
                       conn_params=conn_params)
    msg = {
        'a': 1,
        'b': 2
    }
    while True:
        resp = client.call(msg)
        print(f'Response Message: {resp}')
        client.call_async(msg, on_response=client_onrespone)
        time.sleep(2)



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
    elif broker == 'mqtt':
        from commlib.transports.mqtt import (
            RPCService, RPCClient, ConnectionParameters
        )
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)

    conn_params = ConnectionParameters()
    run_with_msg(RPCService, RPCClient, conn_params)
    # run_with_dict(RPCService, RPCClient, conn_params)

    while True:
        time.sleep(1)
