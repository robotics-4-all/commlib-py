#!/usr/bin/env python

from commlib_py.transports.amqp import (ActionServer, ConnectionParameters,
                                        RemoteLogger)
import time


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    logger = RemoteLogger(action_name, conn_params)
    action = ActionServer(conn_params=conn_params, action_name=action_name,
                          logger=logger)

    action.run()
    while True:
        time.sleep(120)
