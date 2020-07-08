#!/usr/bin/env python

from commlib_py.transports.amqp import (ActionServer, ConnectionParameters,
                                        RemoteLogger)
from commlib_py.action import GoalStatus
import time


def on_goal(goal):
    print(goal.to_dict())
    time.sleep(30)
    return {'result': 1}


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076
    logger = RemoteLogger(action_name, conn_params)
    action = ActionServer(conn_params=conn_params, action_name=action_name,
                          logger=logger, on_goal=on_goal)

    action.run()
    while True:
        time.sleep(0.01)
