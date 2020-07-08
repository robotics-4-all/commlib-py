#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, ConnectionParameters, RemoteLogger
import time


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'etsardou'
    conn_params.credentials.password = 'etsardou'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 8076
    conn_params.vhost = 'etsardou'
    logger = RemoteLogger(rpc_name, conn_params)
    rpcs = RPCServer(conn_params=conn_params, on_request=callback,
                     rpc_name=rpc_name, logger=logger)
    rpcs.run()
    while True:
        try:
            time.sleep(0.001)
        except Exception:
            break
