#!/usr/bin/env python

from commlib_py.transports.amqp import (
    RPCClient, ConnectionParameters, AMQPConnection)
from commlib_py.logger import Logger
import time
from threading import Thread


def thread_runner(c):
    data = {'state': 0}
    while True:
        c.call(data)
        time.sleep(2)


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    logger = Logger('TestAMQPRPC', debug=True)
    conn = AMQPConnection(conn_params)
    rpcc1 = RPCClient(rpc_name=rpc_name, connection=conn, logger=logger)
    rpcc2 = RPCClient(rpc_name=rpc_name, connection=conn, logger=logger)
    rpcc3 = RPCClient(rpc_name=rpc_name, connection=conn, logger=logger)
    t = Thread(target=thread_runner, args=(rpcc3,))
    t.daemon = True
    t.start()
    conn.detach_amqp_events_thread()
    data = {'a': 1, 'b': 'aa'}
    while True:
        resp = rpcc1.call(data)
        print('RPC Client 1 Response: <{}>'.format(resp))
        resp = rpcc2.call(data)
        print('RPC Client 2 Response: <{}>'.format(resp))
        time.sleep(1)
