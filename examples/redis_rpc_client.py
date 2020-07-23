#!/usr/bin/env python

from commlib.transports.redis import (
    RPCClient, TCPConnectionParameters)
from commlib.logger import Logger
import time


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = TCPConnectionParameters()
    logger = Logger('TestRPC', debug=True)
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name, logger=logger)
    data = {'a': 1, 'b': 'aa'}
    while True:
        resp = rpcc.call(data)
        print('RPC Response: <{}>'.format(resp))
        time.sleep(1)
