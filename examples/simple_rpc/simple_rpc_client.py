#!/usr/bin/env python

import sys
import time

from commlib.msg import RPCMessage, DataClass
from commlib.node import Node, TransportType


class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='myclient',
                transport_type=transport,
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    rpc = node.create_rpc_client(msg_type=AddTwoIntMessage,
                                 rpc_name='add_two_ints_node.add_two_ints')

    node.run()

    # Create an instance of the request object
    msg = AddTwoIntMessage.Request()

    while True:
        # returns AddTwoIntMessage.Response instance
        resp = rpc.call(msg)
        print(resp)
        msg.a += 1
        msg.b += 1
        time.sleep(1)
