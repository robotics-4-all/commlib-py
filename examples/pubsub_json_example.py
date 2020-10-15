#!/usr/bin/env python

import sys
import time


def sonar_data_callback(msg):
    print(f'Message: {msg}')


def run_amqp(topic):
    from commlib.transports.amqp import (
        _Publisher, _Subscriber, ConnectionParameters
    )
    sub = _Subscriber(topic=topic,
                      on_message=sonar_data_callback)
    sub.run()

    pub = _Publisher(topic=topic)
    msg = {
        'distance': 0
    }
    while True:
        time.sleep(0.5)
        pub.publish(msg)
        msg['distance'] += 1


def run_redis(topic):
    from commlib.transports.redis import (
        _Publisher, _Subscriber, ConnectionParameters
    )
    sub = _Subscriber(topic=topic,
                      on_message=sonar_data_callback)
    sub.run()

    pub = _Publisher(topic=topic)
    msg = {
        'distance': 0
    }
    while True:
        time.sleep(0.5)
        pub.publish(msg)
        msg['distance'] += 1


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
