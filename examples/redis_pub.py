#!/usr/bin/env python

from commlib_py.transports.redis import Publisher, ConnectionParameters
import time


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    data = {'state': 0}
    while True:
        try:
            p.publish(data)
            time.sleep(2)
        except:
            break

