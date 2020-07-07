#!/usr/bin/env python

from commlib_py.transports.amqp import (ActionServer, ActionClient, RPCClient,
                                        ConnectionParameters)
import time


def on_goal(goalh):
    count = 0
    while True:
        time.sleep(1)
        if goalh.cancel_event.is_set():
            return {'result': 0}
        count += 1
        if count > 10:
            return {'result': 1}


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076

    action = ActionServer(conn_params=conn_params, action_name=action_name,
                          on_goal=on_goal)
    action.run()

    ac = ActionClient(conn_params=conn_params, action_name=action_name)
    goal_data = {'a': 1, 'b': 'test'}

    resp = ac.send_goal(goal_data)
    _goal_id = resp['goal_id']
    print('Send-Goal Response: {}'.format(resp))
    time.sleep(2)
    resp = ac.get_result(_goal_id)
    print('Get-Result Response: {}'.format(resp))
    time.sleep(2)
    resp = ac.cancel_goal(_goal_id)
    print('Cancel-Goal Response: {}'.format(resp))
    time.sleep(2)
    resp = ac.get_result(_goal_id)
    print('Get-Result Response: {}'.format(resp))

    resp = ac.send_goal(goal_data)
    _goal_id = resp['goal_id']
    print('Send-Goal Response: {}'.format(resp))
    time.sleep(13)
    resp = ac.get_result(_goal_id)
    print('Get-Result Response: {}'.format(resp))
    while True:
        time.sleep(0.001)

