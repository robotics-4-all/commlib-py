from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import time
from enum import IntEnum
from commlib.endpoints import endpoint_factory, EndpointType, TransportType
from commlib.logger import Logger


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
    """Bridge.
    Base Bridge Class.
    """

    def __init__(self, btype, logger=None):
        """__init__.

        Args:
            btype:
            logger:
        """
        self._btype = btype
        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

    @property
    def logger(self):
        """logger.
        """
        return self._logger

    def run_forever(self):
        """run_forever.
        """
        try:
            while True:
                time.sleep(0.001)
        except Exception as exc:
            self.logger.error(exc)


class RPCBridge(Bridge):
    """RPCBridge.
    Bridge implementation for RPC Communication.


    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
          <from>           <to>
    """

    def __init__(self,
                 btype: RPCBridgeType,
                 from_uri: str,
                 to_uri: str,
                 from_broker_params,
                 to_broker_params,
                 logger: Logger = None,
                 debug: bool = False):
        """__init__.

        Args:
            btype (RPCBridgeType): RPC Bridge Type
            from_uri (str):
            to_uri (str):
            from_broker_params:
            to_broker_params:
            logger (Logger):
            debug (bool): debug flag
        """
        super(RPCBridge, self).__init__(btype, logger)
        self._from_broker_params = from_broker_params
        self._to_broker_params = to_broker_params
        self._from_uri = from_uri
        self._to_uri = to_uri
        self._debug = debug

        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.REDIS)(
                    conn_params=self._from_broker_params,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._to_uri,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._from_broker_params,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._to_uri,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._from_broker_params,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._to_uri,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.REDIS)(
                    conn_params=self._from_broker_params,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._to_uri,
                    conn_params=self._to_broker_params,
                    debug=debug
                )

    def on_request(self, msg, meta):
        """on_request.

        Args:
            msg:
            meta:
        """
        resp = self._client.call(msg)
        return resp

    def stop(self):
        self._server.stop()

    def run(self):
        self._server.run()


class TopicBridge(Bridge):
    def __init__(self, btype: TopicBridgeType,
                 topic_name: str,
                 sub_conn_params,
                 pub_conn_params):
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
