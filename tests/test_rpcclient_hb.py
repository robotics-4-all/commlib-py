#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, RPCClient, ConnectionParameters
import time
from threading import Thread


HB_TIMEOUT = 2


def thread_runner(c):
    data = {'state': 0}
    while True:
        c.call(data)
        time.sleep(HB_TIMEOUT * 5)

def on_request(msg, meta):
    print(msg)
    return msg


if __name__ == '__main__':
    rpc_name = 'testrpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    conn_params.heartbeat_timeout = HB_TIMEOUT  ## Seconds
    s = RPCServer(conn_params=conn_params,
                  rpc_name=rpc_name,
                  on_request=on_request)
    s.run()
    time.sleep(1)
    c = RPCClient(conn_params=conn_params,
                  rpc_name=rpc_name)
    c.run()
    t = Thread(target=thread_runner, args=(c,))
    t.daemon = True
    t.start()
    data = {'state': 0}
    while True:
        c.call(data)
        time.sleep(HB_TIMEOUT * 5)
