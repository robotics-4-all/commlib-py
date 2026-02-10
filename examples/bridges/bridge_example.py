#!/usr/bin/env python

import time

import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.bridges import RPCBridge, TopicBridge
from rich import print, pretty
from commlib.msg import RPCMessage
from commlib.endpoints import EndpointType, endpoint_factory

pretty.install()


def on_request(msg) -> RPCMessage.Response:
    print(f"[Broker-B] - RPC Service received request: {msg}")
    c = msg["a"] + msg["b"]
    resp = {"c": c}
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


def redis_to_mqtt_rpc_bridge(bA_params, bB_params, timeout=None):
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "ops.start_navigation"
    bB_uri = "thing.robotA.ops.start_navigation"
    br = RPCBridge(
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params,
        debug=False,
    )
    br.run()


def redis_to_mqtt_topic_bridge(bA_params, bB_params, timeout=None):
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "sonar.front"
    bB_uri = "thing.robotA.sensors.sonar.font"
    br = TopicBridge(
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params,
    )
    br.run()


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
    parser.add_argument("--broker-b", type=str, default="mqtt",
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

    redis_to_mqtt_rpc_bridge(bA_params, bB_params, args.timeout)
    redis_to_mqtt_topic_bridge(bA_params, bB_params, args.timeout)

    while not args.timeout:
        time.sleep(1)
