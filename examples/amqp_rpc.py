#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, ConnectionParameters


def callback(msg, meta):
    print(msg)
    print(meta)


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    rpcs = RPCServer(rpc_name, conn_params)
    rpcs.run_forever()

