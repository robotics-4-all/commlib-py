#!/usr/bin/env python

from commlib_py.transports.redis import RPCClient, ConnectionParameters


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name)
    data = {'a': 1, 'b': 'aa'}
    resp = rpcc.call(data)
    print(resp)
