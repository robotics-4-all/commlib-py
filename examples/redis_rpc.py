#!/usr/bin/env python

from commlib_py.transports.redis import RPCServer, ConnectionParameters


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    rpcs = RPCServer(conn_params, on_request=callback, rpc_name=rpc_name)
    rpcs.run_forever()
