#!/usr/bin/env python

from commlib.node import Node, TransportType
from commlib.msg import RPCMessage, DataClass
import time
import sys


class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


def on_request(msg):
    print(f'On-Request: {msg}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp


def on_response(msg):
    print(f'On-Response: {msg}')


if __name__ == '__main__':
    rpc_name = 'testrpc'

    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import (
            ConnectionParameters
        )
        conn_params = ConnectionParameters()
        node = Node(node_name='example-node',
                    transport_type=TransportType.REDIS,
                    transport_connection_params=conn_params, debug=True)
    elif broker == 'amqp':
        from commlib.transports.amqp import (
            ConnectionParameters
        )
        conn_params = ConnectionParameters()
        node = Node(node_name='example-node', transport_type=TransportType.AMQP,
                    transport_connection_params=conn_params, debug=True)
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)

    node.init_heartbeat_thread()

    rpc = node.create_rpc(msg_type=AddTwoIntMessage,
                          rpc_name=rpc_name, on_request=on_request)
    rpc.run()
    time.sleep(1)
    rpc_c = node.create_rpc_client(msg_type=AddTwoIntMessage, rpc_name=rpc_name)

    msg = AddTwoIntMessage.Request(a=1, b=2)

    resp = rpc_c.call(msg)
    print(resp)

    _f = rpc_c.call_async(msg, on_response=on_response)

    node.run_forever()
