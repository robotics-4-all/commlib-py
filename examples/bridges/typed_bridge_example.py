#!/usr/bin/env python

import time

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
from commlib.bridges import RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType
from commlib.msg import PubSubMessage, RPCMessage


class TopicMessage(PubSubMessage):
    a: int = 0


class ExampleRPCMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


def on_request(msg):
    print(f"[Broker-B] - RPC Service received request: {msg}")
    resp = ExampleRPCMessage.Response(c=msg.a + msg.b)
    return resp


def on_message(msg):
    print(f"[Broker-B] - Data received at topic - {msg}")


def get_conn_params(broker, host, port):
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters
    params = ConnectionParameters(host=host)
    if port:
        params.port = port
    return params


def redis_to_amqp_topic_bridge(bA_params, bB_params, timeout=None):
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "rpc.bridge.testA"
    bB_uri = "rpc.bridge.testB"

    # Create and run the bridge
    br = TopicBridge(
        msg_type=TopicMessage,
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params)
    br.run()

    ## For Testing Bridge ------------------>
    from commlib.endpoints import EndpointType, endpoint_factory
    pub = endpoint_factory(EndpointType.Publisher, bA_params.__class__)(
        conn_params=bA_params, msg_type=TopicMessage, topic=bA_uri)

    # Create and run the subscriber
    sub = endpoint_factory(EndpointType.Subscriber, bB_params.__class__)(
        conn_params=bB_params,
        msg_type=TopicMessage,
        topic=bB_uri,
        on_message=on_message,
    )
    sub.run()

    count = 0
    msg = TopicMessage()
    # Publish messages to the topic on Broker A and receive them on Broker B
    # with the subscriber
    start_time = time.time()
    while True:
        if timeout and time.time() - start_time > timeout:
            break
        if count >= 5 and not timeout:
            break
        msg.a = count
        pub.publish(msg)
        time.sleep(1)
        count += 1
    sub.stop()
    ## <-------------------------------------
    br.stop()


def redis_to_amqp_rpc_bridge(bA_params, bB_params, timeout=None):
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "rpc.bridge.testA"
    bB_uri = "rpc.bridge.testB"
    br = RPCBridge(
        msg_type=ExampleRPCMessage,
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params)
    br.run()

    ## For Testing Bridge ------------------>
    from commlib.endpoints import EndpointType, endpoint_factory
    # Create and run the RPC client on Broker A
    client = endpoint_factory(EndpointType.RPCClient, bA_params.__class__)(
        msg_type=ExampleRPCMessage, conn_params=bA_params, rpc_name=bA_uri
    )
    client.run()

    # Create and run the RPC service on Broker B
    server = endpoint_factory(EndpointType.RPCService, bB_params.__class__)(
        msg_type=ExampleRPCMessage,
        conn_params=bB_params,
        rpc_name=bB_uri,
        on_request=on_request,
    )
    server.run()

    count = 0
    req_msg = ExampleRPCMessage.Request()
    # Call the RPC service on Broker B from Broker A
    start_time = time.time()
    while True:
        if timeout and time.time() - start_time > timeout:
            break
        if count >= 5 and not timeout:
            break
        req_msg.a = count
        resp = client.call(req_msg)
        print(f"[Broker-A Client] - Response from AMQP RPC Service: {resp}")
        time.sleep(1)
        count += 1
    server.stop()
    ## <-------------------------------------
    br.stop()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker-a", type=str, default="redis",
                        choices=["redis", "amqp", "mqtt", "kafka"],
                        help="Broker A type")
    parser.add_argument("--host-a", type=str, default="localhost",
                        help="Broker A host")
    parser.add_argument("--port-a", type=int, default=None,
                        help="Broker A port")
    parser.add_argument("--broker-b", type=str, default="amqp",
                        choices=["redis", "amqp", "mqtt", "kafka"],
                        help="Broker B type")
    parser.add_argument("--host-b", type=str, default="localhost",
                        help="Broker B host")
    parser.add_argument("--port-b", type=int, default=None,
                        help="Broker B port")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Max time to run (seconds)")
    args = parser.parse_args()

    bA_params = get_conn_params(args.broker_a, args.host_a, args.port_a)
    bB_params = get_conn_params(args.broker_b, args.host_b, args.port_b)

    redis_to_amqp_rpc_bridge(bA_params, bB_params, args.timeout)
    redis_to_amqp_topic_bridge(bA_params, bB_params, args.timeout)
