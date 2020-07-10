#!/usr/bin/env python

from commlib_py.transports.redis import RPCClient, TCPConnectionParameters
import time


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = TCPConnectionParameters()
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name)
    data = {'a': 1, 'b': 'aa'}
    while True:
        resp = rpcc.call(data)
        print('RPC Response: <{}>'.format(resp))
        time.sleep(1)
