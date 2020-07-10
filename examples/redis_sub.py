#!/usr/bin/env python

from commlib_py.transports.redis import Subscriber, TCPConnectionParameters
import time


def callback(msg, meta):
    print('Message: {}'.format(msg))


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = TCPConnectionParameters()
    s = Subscriber(conn_params=conn_params,
                   topic=topic_name,
                   on_message=callback)
    s.run_forever()

