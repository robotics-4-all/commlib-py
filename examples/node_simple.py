#!/usr/bin/env python

from commlib.transports.amqp import ConnectionParameters
from commlib.node import Node, TransportType
import time


def on_request(msg, meta):
    print(f'On-Request: {msg}')
    return {'c': msg['a'] + msg['b']}


def on_response(msg):
    print(f'On-Response: {msg}')


if __name__ == '__main__':
    topic_name = 'testtopic'
    rpc_name = 'testrpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = '155.207.33.189'
    conn_params.port = 5672
    n = Node(node_name='test-node', transport_type=TransportType.AMQP,
             transport_connection_params=conn_params, debug=True)
    rpc = n.create_rpc(rpc_name=rpc_name, on_request=on_request)
    rpc.run()
    rpc_c = n.create_rpc_client(rpc_name=rpc_name)

    _f = rpc_c.call_async({'a': 1, 'b': 2}, on_response=on_response)

    n.run_forever()
