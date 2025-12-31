#!/usr/bin/env python

import sys
import time

from commlib.msg import RPCMessage
from commlib.node import Node


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


class MultiplyIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


import time

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", type=str, default="redis",
                        choices=["redis", "amqp", "mqtt", "kafka"],
                        help="Broker type")
    parser.add_argument("--host", type=str, default="localhost",
                        help="Broker host")
    parser.add_argument("--port", type=int, default=None,
                        help="Broker port")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Max time to run (seconds)")
    args = parser.parse_args()

    if args.broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif args.broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif args.broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters
    
    start_time = time.time()
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port


    node = Node(
        node_name="myclient",
        connection_params=conn_params,
    )

    rpc_a = node.create_rpc_client(
        msg_type=AddTwoIntMessage, rpc_name="rpcserver.test.add_two_ints"
    )
    rpc_b = node.create_rpc_client(
        msg_type=MultiplyIntMessage, rpc_name="rpcserver.test.multiply_ints"
    )

    node.run()

    # Create an instance of the request object
    msg_a = AddTwoIntMessage.Request()
    msg_b = MultiplyIntMessage.Request()

    while True:
        if args.timeout and time.time() - start_time > args.timeout:
            break
        # returns AddTwoIntMessage.Response instance
        resp = rpc_a.call(msg_a)
        print(f'SUM: {msg_a.a} + {msg_a.b} = {resp}')
        msg_a.a += 1
        msg_a.b += 1
        resp = rpc_b.call(msg_b)
        print(f'MULTIPLY: {msg_b.a} * {msg_b.b} = {resp}')
        msg_b.a += 1
        msg_b.b += 1
        time.sleep(1)
