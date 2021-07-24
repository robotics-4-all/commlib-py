#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass
from commlib.node import Node, TransportType
from typing import List, Any


@DataClass
class DataContainer(PubSubMessage):
    data: List[Any]


if __name__ == '__main__':
    data_length = 10000000
    rate = 10
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
                transport_type=transport,
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=False)

    pub = node.create_publisher(msg_type=DataContainer,
                                topic='perf_test')

    data = [int()] * data_length
    data_size = sys.getsizeof(data)
    print(f'Sending Data of size {data_size} bytes with rate={rate}hz')
    msg = DataContainer(data=data)
    while True:
        pub.publish(msg)
        time.sleep(1/rate)
