from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import time
from enum import IntEnum
from commlib.endpoints import endpoint_factory, EndpointType, TransportType


class BridgeType(IntEnum):
    REDIS_TO_AMQP_RPC = 1
    AMQP_TO_REDIS_RPC = 2
    REDIS_TO_AMQP_TOPIC = 3
    AMQP_TO_REDIS_TOPIC = 4


class RPCBridgeType(IntEnum):
    REDIS_TO_AMQP = 1
    AMQP_TO_REDIS = 2
    AMQP_TO_AMQP = 3
    REDIS_TO_REDIS = 4


class TopicBridgeType(IntEnum):
    REDIS_TO_AMQP = 1
    AMQP_TO_REDIS = 2
    AMQP_TO_AMQP = 3
    REDIS_TO_REDIS = 4


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
                EndpointType.RPCService, TransportType.REDIS)(
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
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._server_conn_params,
                    rpc_name=self._rpc_name,
                    on_request=self.on_request
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._rpc_name,
                    conn_params=self._client_conn_params,
                )
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._server_conn_params,
                    rpc_name=self._rpc_name,
                    on_request=self.on_request
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._rpc_name,
                    conn_params=self._client_conn_params,
                )
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.REDIS)(
                    conn_params=self._server_conn_params,
                    rpc_name=self._rpc_name,
                    on_request=self.on_request
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._rpc_name,
                    conn_params=self._client_conn_params,
                )

    def on_request(self, msg, meta):
        # print(msg, meta)
        resp = self._client.call(msg)
        return resp

    def stop(self):
        self._server.stop()

    def run(self):
        self._server.run()


class TopicBridge(Bridge):
    def __init__(self, btype, sub_conn_params, pub_conn_params,
                 topic_name):
        super(TopicBridge, self).__init__(btype)
        self._sub_conn_params = sub_conn_params
        self._pub_conn_params = pub_conn_params
        self._topic_name = topic_name
        if self._btype == TopicBridgeType.REDIS_TO_AMQP:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.REDIS
            )(
                topic=self._topic_name,
                conn_params=self._sub_conn_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.AMQP
            )(
                topic=self._topic_name,
                conn_params=self._pub_conn_params,
            )
        elif self._btype == TopicBridgeType.AMQP_TO_REDIS:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.AMQP
            )(
                topic=self._topic_name,
                conn_params=self._sub_conn_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.REDIS
            )(
                topic=self._topic_name,
                conn_params=self._pub_conn_params,
            )
        elif self._btype == TopicBridgeType.AMQP_TO_AMQP:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.AMQP
            )(
                topic=self._topic_name,
                conn_params=self._sub_conn_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.AMQP
            )(
                topic=self._topic_name,
                conn_params=self._pub_conn_params,
            )
        elif self._btype == TopicBridgeType.REDIS_TO_REDIS:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.REDIS
            )(
                topic=self._topic_name,
                conn_params=self._sub_conn_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.REDIS
            )(
                topic=self._topic_name,
                conn_params=self._pub_conn_params,
            )

    def on_message(self, msg, meta):
        self._pub.publish(msg)

    def stop(self):
        self._sub.stop()

    def run(self):
        self._sub.run()
