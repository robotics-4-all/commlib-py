#!/usr/bin/env python

from commlib.transports.amqp import ConnectionParameters
from commlib.node import Node, TransportType
import time


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
    rpc = n.create_rpc(rpc_name='test')
    sub = n.create_subscriber(topic=topic_name)
    n.run_forever()
