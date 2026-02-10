#!/usr/bin/env python

import sys
import time

from commlib.msg import ActionMessage
from commlib.node import Node


class ExampleAction(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_goal(goal_h):
    c = 0
    res = ExampleAction.Result()
    while c < goal_h.data.target_cm:
        if goal_h.cancel_event.is_set():
            break
        goal_h.send_feedback(ExampleAction.Feedback(current_cm=c))
        c += 1
        time.sleep(1)
    res.dest_cm = c
    return res


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
        node_name="action_service_example_node",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_action(msg_type=ExampleAction, action_name=action_name, on_goal=on_goal)

    if args.timeout:
        import threading
        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
