#!/usr/bin/env python

import commlib.transports.amqp as acomm
import time


def on_goal(goalh):
    count = 0
    while True:
        time.sleep(1)
        if goalh.cancel_event.is_set():
            return {'a': 0}
        count += 1
        if count > 4:
            return {'a': 1}


def run_simple():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS ACtion Test...')
    print('-----------------------------------------------------------------')
    action_name = 'testaction'
    conn_params = acomm.ConnectionParameters()

    action = acomm.ActionServer(conn_params=conn_params,
                                action_name=action_name,
                                on_goal=on_goal)
    action.run()

    ac = acomm.ActionClient(conn_params=conn_params,
                            action_name=action_name)
    goal_data = {'a': 1, 'b': 'test'}

    resp = ac.send_goal(goal_data)
    _goal_id = resp['goal_id']
    if _goal_id is None:
        pass
    print('Send-Goal Response: {}'.format(resp))
    time.sleep(1)
    resp = ac.get_result(_goal_id)
    # print('Get-Result Response: {}'.format(resp))
    assert resp == {'status': 1, 'result': {}}
    time.sleep(1)
    resp = ac.cancel_goal(_goal_id)
    assert resp == {'status': 1, 'result': {}}
    # print('Cancel-Goal Response: {}'.format(resp))
    time.sleep(1)
    resp = ac.get_result(_goal_id)
    assert resp == {'status': 6, 'result': {'a': 0}}
    # print('Get-Result Response: {}'.format(resp))

    resp = ac.send_goal(goal_data)
    _goal_id = resp['goal_id']
    print('Send-Goal Response: {}'.format(resp))
    time.sleep(6)
    resp = ac.get_result(_goal_id)
    # print('Get-Result Response: {}'.format(resp))
    assert resp == {'status': 4, 'result': {'a': 1}}
    action.stop()


if __name__ == '__main__':
    run_simple()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
