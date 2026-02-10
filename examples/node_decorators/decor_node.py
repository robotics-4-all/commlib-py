#!/usr/bin/env python

import sys

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
    
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port

    node = Node(
        node_name="obstacle_avoidance_node",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )


    @node.subscribe("sensors.sonar.front", SonarMessage)
    def on_message(msg):
        print(f"Received front sonar data: {msg}")


    @node.rpc("add_two_ints_node.add_two_ints", AddTwoIntMessage)
    def add_two_int_handler(msg):
        print(f"Request Message: {msg.__dict__}")
        resp = AddTwoIntMessage.Response(c=msg.a + msg.b)
        return resp


    if args.timeout:
        import threading
        threading.Timer(args.timeout, node.stop).start()
    node.run_forever(sleep_rate=1)
