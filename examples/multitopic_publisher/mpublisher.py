#!/usr/bin/env python

import sys
import time

from commlib.node import Node


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

    node = Node(node_name='example5_publisher',
                connection_params=conn_params,
                debug=True)

    pub = node.create_mpublisher()

    topicA = 'topic.a'
    topicB = 'topic.b'

    while True:
        pub.publish({'a': 1}, topicA)
        pub.publish({'b': 1}, topicB)
        time.sleep(1)
