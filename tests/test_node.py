#!/usr/bin/env python

import time

from commlib.node import Node


def on_msg(msg, meta):
    print(msg)


if __name__ == '__main__':
    n = Node()
    topic = 'testtopic'
    p = n.create_publisher(topic=topic)
    s = n.create_subscriber(topic=topic, on_message=on_msg)
    s.run()
    while True:
        p.publish({'msg': 'test'})
        time.sleep(1)
