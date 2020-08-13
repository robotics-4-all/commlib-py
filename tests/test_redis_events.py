#!/usr/bin/env python

import time

from commlib.transports.redis import EventEmitter, ConnectionParameters
from commlib.events import Event

ITERATIONS = 5


def test_redis():
    ee = EventEmitter(conn_params=ConnectionParameters(host='localhost'),
                      debug=True)
    event =  Event('test-event', 'test.test')
    count = 0
    while count < ITERATIONS:
        ee.send_event(event)
        time.sleep(1)
        event.uri = '{}.{}'.format(event.uri, count)
        count += 1


if __name__ == '__main__':
    test_redis()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
