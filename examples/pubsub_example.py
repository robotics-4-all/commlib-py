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


def run_amqp(topic):
    from commlib.transports.amqp import (
        Publisher, Subscriber, ConnectionParameters
    )
    sub = Subscriber(topic=topic,
                     msg_type=SonarMessage,
                     on_message=sonar_data_callback)
    sub.run()

    pub = Publisher(topic=topic, msg_type=SonarMessage)
    msg = SonarMessage(distance=2.0)
    while True:
        time.sleep(0.5)
        pub.publish(msg)
        msg.distance += 1


def run_redis(topic):
    from commlib.transports.redis import (
        Publisher, Subscriber, ConnectionParameters
    )
    sub = Subscriber(topic=topic,
                     msg_type=SonarMessage,
                     on_message=sonar_data_callback)
    sub.run()

    pub = Publisher(topic=topic, msg_type=SonarMessage)
    msg = SonarMessage(distance=2.0)
    while True:
        time.sleep(0.5)
        pub.publish(msg)
        msg.distance += 1.2

if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    topic = 'example_pubsub'
    if broker == 'amqp':
        run_amqp(topic)
    elif broker == 'redis':
        run_redis(topic)
