#!/usr/bin/env python

import sys
import time

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


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

node = Node(node_name='obstacle_avoidance_node',
            connection_params=conn_params,
            # heartbeat_uri='nodes.add_two_ints.heartbeat',
            debug=True)

@node.subscribe('sensors.sonar.front', SonarMessage)
def on_message(msg):
    print(f'Received front sonar data: {msg}')

@node.rpc('add_two_ints_node.add_two_ints', AddTwoIntMessage)
def add_two_int_handler(msg):
    print(f'Request Message: {msg.__dict__}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp

node.run_forever(sleep_rate=1)
