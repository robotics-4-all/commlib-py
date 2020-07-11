#!/usr/bin/env python

from commlib_py.transports.amqp import (
    RPCServer, RPCClient, ConnectionParameters, AMQPConnection)
import time
from threading import Thread


HB_TIMEOUT = 2
SLEEP_MULTIPLIER = 5
ITERATIONS = 2
RPC_NAME = 'testrpc'
rpc1_name = 'testrpc1'
rpc2_name = 'testrpc2'
num_clients = 10
conn_params = ConnectionParameters()
conn_params.credentials.username = 'testuser'
conn_params.credentials.password = 'testuser'
conn_params.host = 'localhost'
conn_params.port = 8076
conn_params.heartbeat_timeout = HB_TIMEOUT  ## Seconds


def thread_runner(c):
    data = {'msg': 'Sent from Child Thread.'}
    counter = 0
    while counter < ITERATIONS:
        c.call(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1


def on_request(msg, meta):
    print(msg)
    return msg


def create_rpc_client(n, rpc_name, connection):
    l = [RPCClient(connection=connection, rpc_name=rpc_name) for i in range(n)]
    return l


def test_multiple_clients():
    print('[*] - Running multiple clients shared connection test')
    print('[*] - Configuration:')
    print(f'[*] - Number of Clients: {num_clients}')
    print('=================================================================')
    s1 = RPCServer(conn_params=conn_params,
                   rpc_name=rpc1_name,
                   on_request=on_request)
    s2 = RPCServer(conn_params=conn_params,
                   rpc_name=rpc2_name,
                   on_request=on_request)
    s1.run()
    s2.run()
    time.sleep(1)
    conn = AMQPConnection(conn_params)
    c1 = RPCClient(connection=conn,
                   rpc_name=rpc1_name)
    c_list = create_rpc_client(num_clients, rpc1_name, conn)
    conn.detach_amqp_events_thread()

    t = Thread(target=thread_runner, args=(c1,))
    t.daemon = True
    t.start()

    data = {'msg': 'Send from main Thread'}
    counter = 0
    while counter < ITERATIONS:
        for c in c_list:
            c.call(data)
        time.sleep(1)
        counter += 1
    print('[*] - Finished Test!')
    print('=================================================================')


def test_simple_clients():
    print('[*] - Running <Heartbeat Timeout> test with simple connection client')
    print('[*] - Configuration:')
    print(f'[*] - Heartbeat Timeout: {HB_TIMEOUT}')
    print(f'[*] - Sleep Multiplier: {SLEEP_MULTIPLIER}')
    print(f'[*] - Iterations: {ITERATIONS}')
    print('=================================================================')
    s = RPCServer(conn_params=conn_params,
                  rpc_name=RPC_NAME,
                  on_request=on_request)
    s.run()
    time.sleep(1)
    c = RPCClient(conn_params=conn_params,
                  rpc_name=RPC_NAME)
    # c.run()
    t = Thread(target=thread_runner, args=(c,))
    t.daemon = True
    t.start()
    data = {'msg': 'Sent from Main Thread.'}
    counter = 0
    while counter < ITERATIONS:
        c.call(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1
    s.stop()
    print('[*] - Finished Heartbeat Timeout Test!')
    print('=================================================================')


def test_shared_connection_clients():
    print('[*] - Running <Heartbeat Timeout> test with Shared Connection client')
    print('[*] - Configuration:')
    print(f'[*] - Heartbeat Timeout: {HB_TIMEOUT}')
    print(f'[*] - Sleep Multiplier: {SLEEP_MULTIPLIER}')
    print(f'[*] - Iterations: {ITERATIONS}')
    print('=================================================================')
    s = RPCServer(conn_params=conn_params,
                  rpc_name=RPC_NAME,
                  on_request=on_request)
    s.run()
    time.sleep(1)
    conn = AMQPConnection(conn_params)
    c = RPCClient(connection=conn,
                  rpc_name=RPC_NAME)
    # c.run()
    c2 = RPCClient(connection=conn,
                  rpc_name=RPC_NAME)
    t = Thread(target=thread_runner, args=(c,))
    t.daemon = True
    t.start()
    conn.detach_amqp_events_thread()
    data = {'msg': 'Sent from Main Thread.'}
    counter = 0
    while counter < ITERATIONS:
        c2.call(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1
    s.stop()
    print('[*] - Finished Heartbeat Timeout Test!')
    print('=================================================================')


if __name__ == '__main__':
    test_multiple_clients()
    test_shared_connection_clients()
    test_simple_clients()
