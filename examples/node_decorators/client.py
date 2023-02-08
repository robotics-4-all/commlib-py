#!/usr/bin/env python

import sys
import time

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node, TransportType


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

    node = Node(node_name='sensors.sonar.front',
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    pub = node.create_publisher(msg_type=SonarMessage,
                                topic='sensors.sonar.front')

    rpc = node.create_rpc_client(msg_type=AddTwoIntMessage,
                                 rpc_name='add_two_ints_node.add_two_ints')

    node.run()

    msg = SonarMessage()
    msg_b = AddTwoIntMessage.Request()

    while True:
        pub.publish(msg)
        resp = rpc.call(msg_b)
        msg.range += 1
        msg_b.a += 1
        msg_b.b += 1
        time.sleep(1)
