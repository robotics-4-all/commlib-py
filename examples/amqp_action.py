#!/usr/bin/env python

from commlib_py.transports.amqp import (ActionServer, ConnectionParameters,
                                        RemoteLogger)
import time


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    logger = RemoteLogger(rpc_name, conn_params)
    actions = ActionServer(conn_params, action_name=action_name, logger=logger)
