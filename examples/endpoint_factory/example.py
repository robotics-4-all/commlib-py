#!/usr/bin/env python3

import time

from commlib.endpoints import EndpointType, TransportType, endpoint_factory


def callback(data):
    print(data)


if __name__ == "__main__":
    topic = "factory_test_topic"
    mqtt_sub = endpoint_factory(EndpointType.Subscriber, TransportType.MQTT)(
        topic=topic, on_message=callback
    )
    mqtt_sub.run()
    mqtt_pub = endpoint_factory(EndpointType.Publisher, TransportType.MQTT)(
        topic=topic, debug=True
    )

    data = {"a": 1, "b": 2}
    while True:
        mqtt_pub.publish(data)
        time.sleep(1)
