#!/usr/bin/env python3

import time

from commlib.endpoints import EndpointType, TransportType, endpoint_factory


def callback(data):
    print(data)


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

    transport_map = {
        "redis": TransportType.REDIS,
        "amqp": TransportType.AMQP,
        "mqtt": TransportType.MQTT,
        "kafka": TransportType.KAFKA
    }
    transport = transport_map[args.broker]

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

    topic = "factory_test_topic"
    mqtt_sub = endpoint_factory(EndpointType.Subscriber, transport)(
        topic=topic, on_message=callback, conn_params=conn_params
    )
    mqtt_sub.run()
    mqtt_pub = endpoint_factory(EndpointType.Publisher, transport)(
        topic=topic, debug=True, conn_params=conn_params
    )

    data = {"a": 1, "b": 2}
    start_time = time.time()
    while True:
        if args.timeout and time.time() - start_time > args.timeout:
            break
        mqtt_pub.publish(data)
        time.sleep(1)
    mqtt_sub.stop()
