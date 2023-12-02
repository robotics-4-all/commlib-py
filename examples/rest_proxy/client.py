#!/usr/bin/env python

import sys
import time

from commlib.node import Node
from commlib.rest_proxy import RESTProxyMessage


if __name__ == "__main__":
    if len(sys.argv) < 2:
        broker = "redis"
    else:
        broker = str(sys.argv[1])
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="rest_proxy_client",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )

    rpc = node.create_rpc_client(msg_type=RESTProxyMessage, rpc_name="proxy.rest")
    node.run()

    msg = RESTProxyMessage.Request(
        host="httpbin.org",
        port=443,
        ssl=True,
        base_url="",
        path="/put",
        verb="PUT",
        query_params={"a": 1, "b": 2},
        body_params={"c": 3, "d": 4},
    )

    while True:
        # returns AddTwoIntMessage.Response instance
        resp = rpc.call(msg)
        print(resp)
        time.sleep(10)
