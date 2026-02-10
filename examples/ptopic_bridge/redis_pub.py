#!/usr/bin/env python

import time

from commlib.msg import PubSubMessage
from commlib.transports.redis import ConnectionParameters, MPublisher


class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


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
        from commlib.transports.redis import ConnectionParameters, MPublisher
    elif args.broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters, MPublisher
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters, MPublisher
    elif args.broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters, MPublisher
    
    conn_params = ConnectionParameters(host=args.host)
    if args.port:
        conn_params.port = args.port

    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    p1 = "sensors.sonar.front"
    p2 = "sensors.ir.rear"

    pub = MPublisher(conn_params=conn_params, msg_type=SonarMessage, debug=True)

    msg = SonarMessage()
    start_time = time.time()
    while True:
        if args.timeout and time.time() - start_time > args.timeout:
            break
        pub.publish(msg, p1)
        pub.publish(msg, p2)
        time.sleep(1)
        msg.distance += 1
