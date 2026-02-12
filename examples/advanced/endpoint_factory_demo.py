#!/usr/bin/env python

"""Advanced — Endpoint Factory (programmatic endpoint creation).

Demonstrates creating endpoints via ``endpoint_factory()`` without
using the ``Node`` abstraction — useful for lightweight scripts,
testing, or dynamic endpoint creation.

Usage::

    python examples/advanced/endpoint_factory_demo.py --broker redis
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.endpoints import EndpointType, TransportType, endpoint_factory  # noqa: E402


TRANSPORT_MAP = {
    "redis": TransportType.REDIS,
    "amqp": TransportType.AMQP,
    "mqtt": TransportType.MQTT,
    "kafka": TransportType.KAFKA,
}


def on_message(msg) -> None:
    print(f"[factory-sub] received: {msg}")


if __name__ == "__main__":
    parser = make_broker_parser("Endpoint factory demo")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)
    transport = TRANSPORT_MAP[args.broker]

    topic = "factory.demo.counter"

    sub = endpoint_factory(EndpointType.Subscriber, transport)(
        topic=topic,
        on_message=on_message,
        conn_params=conn_params,
    )
    sub.run()

    pub = endpoint_factory(EndpointType.Publisher, transport)(
        topic=topic,
        conn_params=conn_params,
    )
    pub.run()

    start = time.time()
    count = 0
    try:
        while True:
            if args.timeout and time.time() - start > args.timeout:
                break
            pub.publish({"count": count, "ts": time.time()})
            print(f"[factory-pub] published count={count}")
            count += 1
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sub.stop()
