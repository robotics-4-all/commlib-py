#!/usr/bin/env python

from commlib.transports.amqp import RPCServer, ConnectionParameters, RemoteLogger
import time


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    conn_params.vhost = '/'
    logger = RemoteLogger(rpc_name, conn_params)
    rpcs = RPCServer(conn_params=conn_params, on_request=callback,
                     rpc_name=rpc_name, logger=logger)
    rpcs.run()
    while True:
        try:
            time.sleep(0.001)
        except Exception:
            break
