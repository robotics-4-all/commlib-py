#!/usr/bin/env python

import sys
import time

from commlib.msg import DataClass, PubSubMessage


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
        from commlib.transports.amqp import (ConnectionParameters, MPublisher,
                                             PSubscriber)
        topic = 'sensors.#'
    elif broker == 'redis':
        from commlib.transports.redis import (ConnectionParameters, MPublisher,
                                              PSubscriber)
        topic = 'sensors.*'
    elif broker == 'mqtt':
        from commlib.transports.redis import (ConnectionParameters, MPublisher,
                                              PSubscriber)
        topic = 'sensors.*'

    sub = PSubscriber(topic=topic, msg_type=SonarMessage,
                      on_message=sensor_data_callback)
    sub.run()

    msg = SonarMessage()

    p1_topic = topic.split('*')[0] + 'sonar.front'
    p2_topic = topic.split('*')[0] + 'ir.rear'
    pub = MPublisher(msg_type=SonarMessage)
    while True:
        time.sleep(1)
        pub.publish(msg, p1_topic)
        pub.publish(msg, p2_topic)
        msg.distance += 1
