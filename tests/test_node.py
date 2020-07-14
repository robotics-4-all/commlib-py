#!/usr/bin/env python

import time

from commlib_py.node import Node


if __name__ == '__main__':
    n = Node()
    p = n.create_publisher(topic='testtopic')
    while True:
        p.publish({'msg': 'test'})
        time.sleep(1)
