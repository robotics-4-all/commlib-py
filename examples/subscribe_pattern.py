#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, DataClass


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def sensor_data_callback(msg, topic):
    print(f'Sensor Data Message: {topic}:{msg}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'amqp':
        from commlib.transports.amqp import (
            MPublisher, PSubscriber, ConnectionParameters
        )
        topic = 'sensors.#'
    elif broker == 'redis':
        from commlib.transports.redis import (
            MPublisher, PSubscriber, ConnectionParameters
        )
        topic = 'sensors.*'

    sub = PSubscriber(topic=topic,
                     on_message=sensor_data_callback)
    sub.run()

    p1_topic = topic.split('*')[0] + 'sonar.front'
    p2_topic = topic.split('*')[0] + 'ir.rear'
    pub1 = MPublisher()
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
        pub1.publish(msg1, p1_topic)
        pub1.publish(msg2, p2_topic)
        msg1['distance'] += 1
        msg2['distance'] += 1
