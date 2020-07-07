#!/usr/bin/env python

from commlib_py.transports.amqp import (ActionServer, ActionClient, RPCClient,
                                        ConnectionParameters)
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
    action = ActionServer(conn_params=conn_params, action_name=action_name,
                          on_goal=on_goal)
    time.sleep(1)
    # rpcc = RPCClient(conn_params=conn_params,
    #                  rpc_name='{}.send_goal'.format(action_name))

    action.run()
    ac = ActionClient(conn_params=conn_params, action_name=action_name)
    goal_data = {'a': 1, 'b': 'test'}

    resp = ac.send_goal(goal_data)
    print('Send-Goal Response: {}'.format(resp))
    time.sleep(1)
    resp = ac.get_result(resp['goal_id'])
    print('Cancel-Goal Response: {}'.format(resp))
    while True:
        time.sleep(0.001)

