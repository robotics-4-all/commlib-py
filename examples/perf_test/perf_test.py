#!/usr/bin/env python

import sys
import time
from typing import Any, List

from commlib.msg import PubSubMessage
from commlib.node import Node


class DataContainer(PubSubMessage):
    data: List[Any]


def on_message(msg):
    print(f'Received data:')
    print(f'- Size (bytes): {sys.getsizeof(msg.data)}')


def run_variable_data_size(initial_data_size: int,
                           final_data_size: int,
                           freq: int, pub):
    initial_data_len = int(initial_data_size / 4)
    # final_data_len = int(final_data_size / sys.getsizeof(int))

    data_len = initial_data_len

    while True:
        data = [int()] * data_len
        data_size = len(data) * 4
        print(data_size)
        if data_size > final_data_size:
            return
        data_len = data_len * 2
        msg = DataContainer(data=data)
        print(f'Sending Data of size {data_size} bytes')
        pub.publish(msg)
        time.sleep(1/freq)


if __name__ == '__main__':
    rate = 1
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

    node = Node(node_name='sensors.sonar.front',
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=False)

    node.create_subscriber(msg_type=DataContainer,
                           topic='perftest.sub',
                           on_message=on_message)

    node.run()

    pub = node.create_publisher(msg_type=DataContainer,
                                topic='perftest.sub')

    run_variable_data_size(2**8, 34724184, rate, pub)
