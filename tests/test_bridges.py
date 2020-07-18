#!/usr/bin/env python

import commlib_py.transports.amqp as acomm
import commlib_py.transports.redis as rcomm
from commlib_py.bridges import RPCBridge, BridgeType
import time


def on_request(msg, meta):
    print('AMQP RPC Server Request')
    return msg


def run_redis_to_amqp_rpc():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS-to-AMQP RPC Bridge Test...')
    print('-----------------------------------------------------------------')
    rpc_name = 'testrpc'
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

    while True:
        resp = client.call({'a': 1})
        print(resp)
        time.sleep(2)


if __name__ == '__main__':
    run_redis_to_amqp_rpc()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
