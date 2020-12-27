#!/usr/bin/env python

import sys
import time

from commlib.msg import ActionMessage, DataClass
from commlib.node import Node, TransportType


class ExampleAction(ActionMessage):
    @DataClass
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    @DataClass
    class Result(ActionMessage.Result):
        dest_cm: int = 0

    @DataClass
    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_feedback(feedback):
    print(f'ActionClient <on-feedback> callback: {feedback}')


def on_result(result):
    print(f'ActionClient <on-result> callback: {result}')


def on_goal_reached(result):
    print(f'ActionClient <on-goal-reached> callback: {result}')


if __name__ == '__main__':
    action_uri = 'action_example'
    if len(sys.argv) > 1:
        broker_type = str(sys.argv[1])
    else:
        broker_type = 'redis'
    if broker_type == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker_type == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker_type == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='action_client_example_node',
                transport_type=transport,
                transport_connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)
    action_client = node.create_action_client(msg_type=ExampleAction,
                                              action_uri=action_uri,
                                              on_goal_reached=on_goal_reached,
                                              on_feedback=on_feedback,
                                              on_result=on_result)
    node.run()
    goal_msg = ExampleAction.Goal(target_cm=5)
    action_client.send_goal(goal_msg)
    resp = action_client.get_result(wait=True)
    print(f'Action Result: {resp}')
