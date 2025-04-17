#!/usr/bin/env python

from itertools import zip_longest
import itertools
import sys
import time
from typing import Any, Dict, List

from commlib.msg import PubSubMessage
from commlib.node import Node


class DataContainer(PubSubMessage):
    data: Dict[Any, Any]
    ts: float = -1


def get_datasize(data: Dict[Any, Any], seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(data)
    if seen is None:
        seen = set()
    obj_id = id(data)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(data, dict):
        size += sum([get_datasize(v, seen) for v in data.values()])
        size += sum([get_datasize(k, seen) for k in data.keys()])
    elif hasattr(data, '__dict__'):
        size += get_datasize(obj.__dict__, seen)
    elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes, bytearray)):
        size += sum([get_datasize(i, seen) for i in data])
    size_kb = size / 2**10
    size_mb = size_kb / 2**10
    return size_kb


def get_ts_ns():
    return time.time_ns()


def on_message(msg):
    delay_ns = get_ts_ns() - msg.ts
    delay_ms = delay_ns / 1e6
    print(f"[Listener] Size (kb): {get_datasize(msg.model_dump())}")
    print(f"[Listener] Relevant Delay (ms): {delay_ms}")


def run_variable_data_size(initial_data_pow: int, final_data_pow: int, freq: int, pub):
    current_pow = initial_data_pow

    while True:
        data_size = 2**current_pow
        data = dict(zip_longest(range(data_size), (), fillvalue=None))
        # data = dict(zip(range(data_len), itertools.cycle([1])))

        if current_pow > final_data_pow:
            return

        msg = DataContainer(data=data, ts=get_ts_ns())
        print(f"[Producer] Sending Data of size (kb): {get_datasize(msg.model_dump())}")
        pub.publish(msg)

        current_pow += 1

        time.sleep(1 / freq)


if __name__ == "__main__":
    rate = 1
    if len(sys.argv) < 2:
        broker = "redis"
    else:
        broker = str(sys.argv[1])
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="sensors.sonar.front",
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=False,
    )

    node.create_subscriber(
        msg_type=DataContainer, topic="perftest.sub", on_message=on_message
    )

    node.run()

    pub = node.create_publisher(msg_type=DataContainer, topic="perftest.sub")
    node.run()

    run_variable_data_size(8, 20, rate, pub)
