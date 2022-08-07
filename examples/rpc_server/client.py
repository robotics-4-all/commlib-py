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


class MultiplyIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='myclient',
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    rpc_a = node.create_rpc_client(msg_type=AddTwoIntMessage,
                                   rpc_name='rpcserver.test.add_two_ints')
    rpc_b = node.create_rpc_client(msg_type=MultiplyIntMessage,
                                   rpc_name='rpcserver.test.multiply_ints')

    node.run()

    # Create an instance of the request object
    msg_a = AddTwoIntMessage.Request()
    msg_b = MultiplyIntMessage.Request()

    while True:
        # returns AddTwoIntMessage.Response instance
        resp = rpc_a.call(msg_a)
        print(resp)
        msg_a.a += 1
        msg_a.b += 1
        resp = rpc_b.call(msg_b)
        print(resp)
        msg_b.a += 1
        msg_b.b += 1
        time.sleep(1)
