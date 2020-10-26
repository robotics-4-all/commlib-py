#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, DataClass


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def sonar_data_callback(msg):
    print(f'Message: {msg}')
    # print(f'{msg["distance"]}')
    # print(f'{msg.distance}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'amqp':
        from commlib.transports.amqp import (
            Publisher, Subscriber, ConnectionParameters
        )
        topic = 'sensors.#'
    elif broker == 'redis':
        from commlib.transports.redis import (
            Publisher, Subscriber, ConnectionParameters
        )
        topic = 'sensors.*'

    sub = Subscriber(topic=topic,
                     on_message=sonar_data_callback)
    sub.run()

    p1_topic = topic.split('*')[0] + 'sonar.front'
    p2_topic = topic.split('*')[0] + 'ir.rear'
    pub1 = Publisher(topic=p1_topic)
    pub2 = Publisher(topic=p2_topic)
    msg1 = {
        'id': 'sensor',
        'distance': 0
    }
    msg2 = {
        'id': 'ir',
        'distance': 0
    }
    while True:
        time.sleep(1)
        pub1.publish(msg1)
        pub2.publish(msg2)
        msg1['distance'] += 1
        msg2['distance'] += 1
