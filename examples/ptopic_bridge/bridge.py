#!/usr/bin/env python


import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.bridges import PTopicBridge, TopicBridgeType
from commlib.msg import PubSubMessage


class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


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

    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "sensors.*"
    bB_namespace = "myrobot"

    br = PTopicBridge(
        TopicBridgeType.REDIS_TO_MQTT,
        bA_uri,
        bB_namespace,
        bA_params,
        bB_params,
        msg_type=SonarMessage,
    )
    if args.timeout:
        import threading
        threading.Timer(args.timeout, br.stop).start()
    br.run_forever()
