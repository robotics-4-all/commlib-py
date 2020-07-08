#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, RPCClient, ConnectionParameters
import time
from threading import Thread


def thread_runner(c):
    data = {'state': 0}
    while True:
        c.call(data)
        time.sleep(2)


def on_request(msg, meta):
    print(msg)
    time.sleep(0.5)
    return msg


def create_rpc_client(n, conn_params, rpc_name):
    l = [RPCClient(conn_params=conn_params, rpc_name=rpc_name) for i in range(n)]
    return l


if __name__ == '__main__':
    rpc1_name = 'testrpc1'
    rpc2_name = 'testrpc2'
    num_clients = 50
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    s1 = RPCServer(conn_params=conn_params,
                  rpc_name=rpc1_name,
                  on_request=on_request)
    s2 = RPCServer(conn_params=conn_params,
                  rpc_name=rpc2_name,
                  on_request=on_request)
    s1.run()
    s2.run()
    time.sleep(1)
    c1 = RPCClient(conn_params=conn_params,
                   rpc_name=rpc1_name)
    # t = Thread(target=thread_runner, args=(c1,))
    # t.daemon = True
    # t.start()
    c_list = create_rpc_client(num_clients, conn_params, rpc1_name)
    data = {'state': 0}
    while True:
        for c in c_list:
            c.call(data)
        time.sleep(1)
