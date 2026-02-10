#!/usr/bin/env python

import sys

from commlib.msg import ActionMessage
from commlib.node import Node


class ExampleAction(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_feedback(feedback):
    print(f"ActionClient <on-feedback> callback: {feedback}")


def on_result(result):
    print(f"ActionClient <on-result> callback: {result}")


def on_goal_reached(result):
    print(f"ActionClient <on-goal-reached> callback: {result}")


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
        node_name="action_client_example_node",
        connection_params=conn_params,
        heartbeats=False
    )
    action_client = node.create_action_client(
        msg_type=ExampleAction,
        action_name=action_name,
        on_goal_reached=on_goal_reached,
        on_feedback=on_feedback,
        on_result=on_result,
    )
    node.run()
    goal_msg = ExampleAction.Goal(target_cm=5)
    action_client.send_goal(goal_msg)
    resp = action_client.get_result(wait=True)
    print(f"Action Result: {resp}")
    node.stop()
