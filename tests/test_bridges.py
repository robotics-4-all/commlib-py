#!/usr/bin/env python

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
from commlib.bridges import RPCBridge, BridgeType
import time


def on_request(msg, meta):
    print('RPC Server Request')
    return msg


def run_amqp_to_redis_rpc():
    print()
    print('-----------------------------------------------------------------')
    print('Running AMQP-to-REDIS RPC Bridge Test...')
    print('-----------------------------------------------------------------')
    rpc_name = 'testrpc1'
    client_params = conn_params = rcomm.ConnectionParameters()
    server_params = conn_params = acomm.ConnectionParameters()
    br = RPCBridge(BridgeType.AMQP_TO_REDIS_RPC, client_params,
                   server_params, rpc_name)
    # br.run_forever()

    client = acomm.RPCClient(conn_params=server_params,
                             rpc_name=rpc_name)

    server = rcomm.RPCServer(
        conn_params=client_params,
        rpc_name=rpc_name,
        on_request=on_request
    )
    server.run()

    count = 0
    while count < 5:
        resp = client.call({'a': 1})
        print(f'Response from REDIS RPC Server: {resp}')
        time.sleep(1)
        count += 1


def run_redis_to_amqp_rpc():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS-to-AMQP RPC Bridge Test...')
    print('-----------------------------------------------------------------')
    rpc_name = 'testrpc2'
    client_params = conn_params = acomm.ConnectionParameters()
    server_params = conn_params = rcomm.ConnectionParameters()
    br = RPCBridge(BridgeType.REDIS_TO_AMQP_RPC, client_params,
                   server_params, rpc_name)
    # br.run_forever()

    client = rcomm.RPCClient(conn_params=server_params,
                             rpc_name=rpc_name)

    server = acomm.RPCServer(
        conn_params=client_params,
        rpc_name=rpc_name,
        on_request=on_request
    )
    server.run()

    count = 0
    while count < 5:
        resp = client.call({'a': 1})
        print(f'Response from AMQP RPC Server: {resp}')
        time.sleep(1)
        count += 1
    server.stop()
    br.stop()


if __name__ == '__main__':
    run_redis_to_amqp_rpc()
    run_amqp_to_redis_rpc()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
