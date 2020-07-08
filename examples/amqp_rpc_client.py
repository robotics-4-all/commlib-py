#!/usr/bin/env python

from commlib_py.transports.amqp import RPCClient, ConnectionParameters


if __name__ == '__main__':
    rpc_name = 'testaction.send_goal'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name)
    data = {'a': 1, 'b': 'aa'}
    resp = rpcc.call(data)
    print(resp)
