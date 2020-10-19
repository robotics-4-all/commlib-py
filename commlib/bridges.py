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
from commlib.msg import PubSubMessage, RPCMessage


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

    def __init__(self, btype, logger=None, debug=False):
        """__init__.

        Args:
            btype:
            logger:
        """
        self._btype = btype
        self._logger = Logger(self.__class__.__name__, debug=debug) if \
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
                 msg_type: RPCMessage,
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
        super(RPCBridge, self).__init__(btype, logger, debug)
        self._from_broker_params = from_broker_params
        self._to_broker_params = to_broker_params
        self._from_uri = from_uri
        self._to_uri = to_uri
        self._msg_type = msg_type

        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.REDIS)(
                    conn_params=self._from_broker_params,
                    msg_type=self._msg_type,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._to_uri,
                    msg_type=self._msg_type,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._from_broker_params,
                    msg_type=self._msg_type,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._to_uri,
                    msg_type=self._msg_type,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.AMQP)(
                    conn_params=self._from_broker_params,
                    msg_type=self._msg_type,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.AMQP)(
                    rpc_name=self._to_uri,
                    msg_type=self._msg_type,
                    conn_params=self._to_broker_params,
                    debug=debug
                )
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            self._server = endpoint_factory(
                EndpointType.RPCService, TransportType.REDIS)(
                    conn_params=self._from_broker_params,
                    msg_type=self._msg_type,
                    rpc_name=self._from_uri,
                    on_request=self.on_request,
                    debug=debug
                )
            self._client = endpoint_factory(
                EndpointType.RPCClient, TransportType.REDIS)(
                    rpc_name=self._to_uri,
                    msg_type=self._msg_type,
                    conn_params=self._to_broker_params,
                    debug=debug
                )

    def on_request(self, msg):
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
        self.logger.info(f'Started RPC B2B Bridge <{self._from_uri} -> {self._to_uri}')


class TopicBridge(Bridge):
    """TopicBridge.
    Bridge implementation for Topic-based/PubSub Communication.


    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
          <from>           <to>
    """
    def __init__(self,
                 btype: TopicBridgeType,
                 msg_type: PubSubMessage,
                 from_uri: str,
                 to_uri: str,
                 from_broker_params,
                 to_broker_params,
                 logger: Logger = None,
                 debug: bool = False):
        super(TopicBridge, self).__init__(btype, logger, debug)
        self._from_broker_params = from_broker_params
        self._to_broker_params = to_broker_params
        self._from_uri = from_uri
        self._to_uri = to_uri
        self._msg_type = msg_type

        if self._btype == TopicBridgeType.REDIS_TO_AMQP:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.REDIS
            )(
                topic=self._from_uri,
                msg_type=self._msg_type,
                conn_params=self._from_broker_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.AMQP
            )(
                topic=self._to_uri,
                msg_type=self._msg_type,
                conn_params=self._to_broker_params,
            )
        elif self._btype == TopicBridgeType.AMQP_TO_REDIS:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.AMQP
            )(
                topic=self._from_uri,
                msg_type=self._msg_type,
                conn_params=self._from_broker_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.REDIS
            )(
                topic=self._to_uri,
                msg_type=self._msg_type,
                conn_params=self._to_broker_params,
            )
        elif self._btype == TopicBridgeType.AMQP_TO_AMQP:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.AMQP
            )(
                topic=self._from_uri,
                msg_type=self._msg_type,
                conn_params=self._from_broker_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.AMQP
            )(
                topic=self._to_uri,
                msg_type=self._msg_type,
                conn_params=self._to_broker_params,
            )
        elif self._btype == TopicBridgeType.REDIS_TO_REDIS:
            self._sub = endpoint_factory(
                EndpointType.Subscriber, TransportType.REDIS
            )(
                topic=self._from_uri,
                msg_type=self._msg_type,
                conn_params=self._from_broker_params,
                on_message=self.on_message
            )
            self._pub = endpoint_factory(
                EndpointType.Publisher, TransportType.REDIS
            )(
                topic=self._to_uri,
                msg_type=self._msg_type,
                conn_params=self._to_broker_params,
            )

    def on_message(self, msg):
        print(msg)
        self._pub.publish(msg)

    def stop(self):
        self._sub.stop()

    def run(self):
        self._sub.run()
        self.logger.info(
            f'Started Topic B2B Bridge ' + \
            f'<{self._from_broker_params.host}:{self._from_broker_params.port}[{self._from_uri}] ' + \
            f'-> {self._to_broker_params.host}:{self._to_broker_params.port}[{self._to_uri}]>')
