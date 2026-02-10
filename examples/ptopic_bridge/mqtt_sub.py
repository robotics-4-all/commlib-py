#!/usr/bin/env python

from commlib.msg import PubSubMessage
from commlib.transports.mqtt import ConnectionParameters, PSubscriber


class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def on_message(msg: SonarMessage, topic: str):
    print(f"[Broker-B] - Data received at topic - {topic}:{msg}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", type=str, default="mqtt",
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
        from commlib.transports.redis import ConnectionParameters, PSubscriber
    elif args.broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters, PSubscriber
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters, PSubscriber
    elif args.broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters, PSubscriber
    
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port

    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "sensors.*"
    bB_namespace = "myrobot"

    sub = PSubscriber(
        conn_params=conn_params,
        topic=f"{bB_namespace}.{bA_uri}",
        msg_type=SonarMessage,
        on_message=on_message,
    )
    if args.timeout:
        import threading
        import time
        threading.Timer(args.timeout, sub.stop).start()
    sub.run_forever()
