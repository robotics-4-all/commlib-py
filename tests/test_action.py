#!/usr/bin/env python

import commlib_py.transports.amqp as acomm
import commlib_py.transports.redis as rcomm
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


def run_amqp():
    print('-----------------------------------------------------------------')
    print('Running AMQP ACtion Test...')
    print('-----------------------------------------------------------------')
    action_name = 'testaction'
    conn_params = acomm.ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'localhost'
    conn_params.port = 8076

    action = acomm.ActionServer(conn_params=conn_params,
                                action_name=action_name,
                                on_goal=on_goal)
    action.run()

    ac = acomm.ActionClient(conn_params=conn_params, action_name=action_name)
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
    print('-----------------------------------------------------------------')


def run_redis():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS ACtion Test...')
    print('-----------------------------------------------------------------')
    action_name = 'testaction'
    conn_params = rcomm.ConnectionParameters()

    action = rcomm.ActionServer(conn_params=conn_params,
                                action_name=action_name,
                                on_goal=on_goal)
    action.run()

    ac = rcomm.ActionClient(conn_params=conn_params,
                            action_name=action_name)
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


if __name__ == '__main__':
    run_amqp()
    run_redis()
