from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import time
from enum import IntEnum
from commlib_py.endpoints import endpoint_factory, EndpointType, TransportType


class BridgeType(IntEnum):
    REDIS_TO_AMQP_RPC = 1
    AMQP_TO_REDIS_RPC = 2
    REDIS_TO_AMQP_PUB = 3
    AMQP_TO_REDIS_PUB = 4
    REDIS_TO_AMQP_PUBSUB = 5
    AMQP_TO_REDIS_PUBSUB = 6  # Same with 5


class RPCBridgeType(IntEnum):
    REDIS_TO_AMQP = 1
    AMQP_TO_REDIS = 2


class Bridge(object):
    def __init__(self, btype):
        self._btype = btype

    def run_forever(self):
        try:
            while True:
                time.sleep(0.001)
        except Exception as exc:
            pass


class RPCBridge(Bridge):
    def __init__(self, btype, client_conn_params, server_conn_params,
                 rpc_name):
        super(RPCBridge, self).__init__(btype)
        self._client_conn_params = client_conn_params
        self._server_conn_params = server_conn_params
        self._rpc_name = rpc_name
        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCServer, TransportType.REDIS)(
                    conn_params=self._server_conn_params,
                    rpc_name=self._rpc_name,
                    on_request=self.on_request
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._rpc_name,
                    conn_params=self._client_conn_params
                )
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCServer, TransportType.AMQP)(
                    conn_params=self._server_conn_params,
                    rpc_name=self._rpc_name,
                    on_request=self.on_request
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._rpc_name,
                    conn_params=self._client_conn_params,
                )
        self._server.run()

    def on_request(self, msg, meta):
        # print(msg, meta)
        resp = self._client.call(msg)
        return resp

    def stop(self):
        self._server.stop()
