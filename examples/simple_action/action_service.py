#!/usr/bin/env python

import sys
import time

from commlib.action import GoalStatus
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


if __name__ == '__main__':
    action_name = 'action_example'
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

    node = Node(node_name='action_service_example_node',
                transport_type=transport,
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)
    node.create_action(msg_type=ExampleAction,
                       action_name=action_name,
                       on_goal=on_goal)

    node.run_forever()
