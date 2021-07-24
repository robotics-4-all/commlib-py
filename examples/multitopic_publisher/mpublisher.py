#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass
from commlib.node import Node, TransportType


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

    node = Node(node_name='example5_publisher',
                transport_type=transport,
                connection_params=conn_params,
                debug=True)

    pub = node.create_mpublisher()

    topicA = 'topic.a'
    topicB = 'topic.b'

    while True:
        pub.publish({'a': 1}, topicA)
        pub.publish({'b': 1}, topicB)
        time.sleep(1)
