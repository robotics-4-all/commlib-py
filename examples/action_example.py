#!/usr/bin/env python

from commlib.action import GoalStatus
from commlib.msg import ActionMessage, DataClass
import sys
import time


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


def on_goal(goal_h, result_msg, feedback_msg):
    c = 0
    res = result_msg()
    while c < 5:
        if goal_h.cancel_event.is_set():
            break
        goal_h.send_feedback(feedback_msg(current_cm=c))
        c += 1
        time.sleep(1)
    res.dest_cm = c
    return res

def on_feedback(feedback):
    print(f'ActionClient <on-feedback> callback: {feedback}')


def on_result(result):
    print(f'ActionClient <on-result> callback: {result}')


def on_goal_reached(result):
    print(f'ActionClient <on-goal-reached> callback: {result}')


if __name__ == '__main__':
    action_name = 'testaction'
    broker_type = 'redis'
    if len(sys.argv) > 1:
        broker_type = str(sys.argv[1])
    if broker_type == 'redis':
        from commlib.transports.redis import (
            ActionServer, ActionClient, ConnectionParameters
        )
    elif broker_type == 'amqp':
        from commlib.transports.amqp import (
            ActionServer, ActionClient, ConnectionParameters
        )
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)


    conn_params = ConnectionParameters()
    action = ActionServer(msg_type=ExampleAction,
                          conn_params=conn_params,
                          action_name=action_name,
                          on_goal=on_goal)
    action_c = ActionClient(msg_type=ExampleAction,
                            conn_params=conn_params,
                            action_name=action_name,
                            on_feedback=on_feedback,
                            on_result=on_result,
                            on_goal_reached=on_goal_reached)

    action.run()
    time.sleep(1)

    goal_msg = ExampleAction.Goal()

    action_c.send_goal(goal_msg)
    # res = action_c.get_result(wait=True)
    time.sleep(1)
    # resp = action_c.cancel_goal(wait_for_result=True)
    resp = action_c.get_result(wait=True)
    print(resp)

    action.stop()
    action_c.stop()
