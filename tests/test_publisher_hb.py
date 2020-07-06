#!/usr/bin/env python

from commlib_py.transports.amqp import Publisher, ConnectionParameters
import time
from threading import Thread


HB_TIMEOUT = 1


def thread_runner(p):
    data = {'state': 0}
    while True:
        p.publish(data)
        time.sleep(HB_TIMEOUT * 10)


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    conn_params.heartbeat_timeout = HB_TIMEOUT  ## Seconds
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    t = Thread(target=thread_runner, args=(p,))
    t.daemon = True
    t.start()
    data = {'state': 0}
    while True:
        p.publish(data)
        time.sleep(HB_TIMEOUT * 10)
