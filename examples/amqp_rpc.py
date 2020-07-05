#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, ConnectionParameters, RemoteLogger


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
    rpcs = RPCServer(conn_params, on_request=callback, rpc_name=rpc_name,
                     logger=logger)
    rpcs.run_forever()
