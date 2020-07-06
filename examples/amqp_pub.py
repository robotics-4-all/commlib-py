#!/usr/bin/env python

from commlib_py.transports.amqp import Publisher, ConnectionParameters
import time


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    data = {'state': 0}
    while True:
        try:
            p.publish(data)
            time.sleep(2)
        except:
            break

