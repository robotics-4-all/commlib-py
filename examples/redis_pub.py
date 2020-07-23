#!/usr/bin/env python

from commlib.transports.redis import (
    Publisher, UnixSocketConnectionParameters)
import time


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = UnixSocketConnectionParameters()
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    data = {'state': 0}
    while True:
        try:
            p.publish(data)
            time.sleep(2)
        except:
            break

