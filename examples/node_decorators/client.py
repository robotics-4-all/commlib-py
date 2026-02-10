#!/usr/bin/env python

import sys
import time

from commlib.msg import MessageHeader, PubSubMessage, RPCMessage
from commlib.node import Node


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class AddTwoIntMessage(RPCMessage):
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
        node_name="sensors.sonar.front",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )

    pub = node.create_publisher(msg_type=SonarMessage, topic="sensors.sonar.front")

    rpc = node.create_rpc_client(
        msg_type=AddTwoIntMessage, rpc_name="add_two_ints_node.add_two_ints"
    )

    node.run()

    msg = SonarMessage()
    msg_b = AddTwoIntMessage.Request()

    while True:
            if args.timeout and time.time() - start_time > args.timeout:
                break
        pub.publish(msg)
        resp = rpc.call(msg_b)
        msg.range += 1
        msg_b.a += 1
        msg_b.b += 1
        time.sleep(1)
