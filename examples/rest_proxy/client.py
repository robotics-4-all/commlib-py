#!/usr/bin/env python

import sys
import time

from commlib.node import Node, TransportType
from commlib.rest_proxy import RESTProxyMessage

if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='rest_proxy_client',
                transport_type=transport,
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    rpc = node.create_rpc_client(msg_type=RESTProxyMessage,
                                 rpc_name='proxy.rest')

    node.run()

    # Create an instance of the request object
    # msg = RESTProxyMessage.Request(base_url='https://httpbin.org',
    #                                path='/get', verb='GET',
    #                                query_params={'a': 1, 'b': 2})
    msg = RESTProxyMessage.Request(base_url='https://httpbin.org',
                                   path='/put', verb='PUT',
                                   query_params={'a': 1, 'b': 2},
                                   body_params={'c': 3, 'd': 4})

    while True:
        # returns AddTwoIntMessage.Response instance
        resp = rpc.call(msg)
        print(resp)
        time.sleep(10)
