import logging
import time
from enum import IntEnum
from typing import List, Union

from commlib.connection import BaseConnectionParameters
from commlib.endpoints import EndpointType, TransportType, endpoint_factory
from commlib.msg import PubSubMessage, RPCMessage

br_logger = None


class RPCBridgeType(IntEnum):
    """RPCBridgeType.
    """
    REDIS_TO_AMQP = 1
    AMQP_TO_REDIS = 2
    AMQP_TO_AMQP = 3
    REDIS_TO_REDIS = 4
    MQTT_TO_REDIS = 5
    MQTT_TO_AMQP = 6
    MQTT_TO_MQTT = 7
    REDIS_TO_MQTT = 8
    AMQP_TO_MQTT = 9


class TopicBridgeType(IntEnum):
    """TopicBridgeType.
    """
    REDIS_TO_AMQP = 1
    AMQP_TO_REDIS = 2
    AMQP_TO_AMQP = 3
    REDIS_TO_REDIS = 4
    MQTT_TO_REDIS = 5
    MQTT_TO_AMQP = 6
    MQTT_TO_MQTT = 7
    REDIS_TO_MQTT = 8
    AMQP_TO_MQTT = 9


class Bridge:
    """Bridge.
    Base Bridge Class.
    """
    @classmethod
    def logger(cls) -> logging.Logger:
        global br_logger
        if br_logger is None:
            br_logger = logging.getLogger(__name__)
        return br_logger

    def __init__(self,
                 btype: Union[TopicBridgeType, RPCBridgeType],
                 from_uri: str,
                 to_uri: str,
                 from_broker_params: BaseConnectionParameters,
                 to_broker_params: BaseConnectionParameters,
                 debug: bool = False):
        """__init__.

        Args:
            btype:
            debug (bool): debug
        """
        self._btype = btype
        self._from_broker_params = from_broker_params
        self._to_broker_params = to_broker_params
        self._from_uri = from_uri
        self._to_uri = to_uri
        self._debug = debug

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def log(self) -> Logger:
        return self.logger()

    def run(self):
        raise NotImplementedError()

    def run_forever(self):
        """run_forever.
        """
        self.run()
        while True:
            time.sleep(0.001)


class RPCBridge(Bridge):
    """RPCBridge.
    Bridge implementation for RPC Communication.


    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
          <from>           <to>
    """

    def __init__(self,
                 btype: RPCBridgeType,
                 msg_type: RPCMessage = None,
                 *args, **kwargs):
        """__init__.

        Args:
            btype (RPCBridgeType): RPC Bridge Type
        """
        super().__init__(btype, *args, **kwargs)
        self._msg_type = msg_type

        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            from_transport = TransportType.REDIS
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            from_transport = TransportType.AMQP
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            from_transport = TransportType.AMQP
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            from_transport = TransportType.REDIS
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_REDIS:
            from_transport = TransportType.MQTT
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_AMQP:
            from_transport = TransportType.MQTT
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.MQTT_TO_MQTT:
            from_transport = TransportType.MQTT
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.REDIS_TO_MQTT:
            from_transport = TransportType.REDIS
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.AMQP_TO_MQTT:
            from_transport = TransportType.AMQP
            to_transport = TransportType.MQTT
        self._server = endpoint_factory(
            EndpointType.RPCService, from_transport)(
                conn_params=self._from_broker_params,
                msg_type=self._msg_type,
                rpc_name=self._from_uri,
                on_request=self.on_request,
                debug=self.debug
            )
        self._client = endpoint_factory(
            EndpointType.RPCClient, to_transport)(
                rpc_name=self._to_uri,
                msg_type=self._msg_type,
                conn_params=self._to_broker_params,
                debug=self.debug
            )

    def on_request(self, msg: RPCMessage.Request):
        """on_request.

        Args:
            msg (RPCMessage.Request): RPC request message
        """
        resp = self._client.call(msg)
        return resp

    def stop(self):
        """stop.
        """
        self._server.stop()

    def run(self):
        """run.
        """
        self._server.run()
        self.log.info(
            f'Started RPC B2B Bridge <{self._from_uri} -> {self._to_uri}')


class TopicBridge(Bridge):
    """TopicBridge.
    Bridge implementation for Topic-based/PubSub Communication.


    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
          <from>           <to>
    """
    def __init__(self,
                 btype: TopicBridgeType,
                 msg_type: PubSubMessage = None,
                 *args, **kwargs):
        """__init__.

        Args:
            btype (TopicBridgeType): btype
            msg_type (PubSubMessage): msg_type
        """
        super().__init__(btype, *args, **kwargs)
        self._msg_type = msg_type

        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            from_transport = TransportType.REDIS
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            from_transport = TransportType.AMQP
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            from_transport = TransportType.AMQP
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            from_transport = TransportType.REDIS
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_REDIS:
            from_transport = TransportType.MQTT
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_AMQP:
            from_transport = TransportType.MQTT
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.MQTT_TO_MQTT:
            from_transport = TransportType.MQTT
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.REDIS_TO_MQTT:
            from_transport = TransportType.REDIS
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.AMQP_TO_MQTT:
            from_transport = TransportType.AMQP
            to_transport = TransportType.MQTT
        self._sub = endpoint_factory(
            EndpointType.Subscriber, from_transport
        )(
            topic=self._from_uri,
            msg_type=self._msg_type,
            conn_params=self._from_broker_params,
            on_message=self.on_message
        )
        self._pub = endpoint_factory(
            EndpointType.Publisher, to_transport
        )(
            topic=self._to_uri,
            msg_type=self._msg_type,
            conn_params=self._to_broker_params,
        )

    def on_message(self, msg: PubSubMessage):
        """on_message.

        Args:
            msg (PubSubMessage): Published Message
        """
        self._pub.publish(msg)

    def stop(self):
        """stop.
        """
        self._sub.stop()

    def run(self):
        """run.
        """
        self._sub.run()
        self.log.info(
            f'Started Topic B2B Bridge ' + \
            f'<{self._from_broker_params.host}:' + \
            f'{self._from_broker_params.port}[{self._from_uri}] ' + \
            f'-> {self._to_broker_params.host}:' + \
            f'{self._to_broker_params.port}[{self._to_uri}]>')


class PTopicBridge(Bridge):
    """PTopicBridge.
    Pattern-based Bridge implementation for Topic-based/PubSub Communication.


    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
          <from>           <to>
    """
    def __init__(self,
                 btype: TopicBridgeType,
                 msg_type: PubSubMessage = None,
                 uri_transform: List = [],
                 *args, **kwargs):
        """__init__.

        Args:
            btype (TopicBridgeType): btype
            from_uri (str): from_uri
            to_uri (str): to_uri
            from_broker_params:
            to_broker_params:
            msg_type (PubSubMessage): msg_type
            debug (bool): debug
        """
        super().__init__(btype, *args, **kwargs)
        if not '*' in from_uri:
            raise ValueError('from_uri must be defined using topic patterns')
        self._from_broker_params = from_broker_params
        self._to_broker_params = to_broker_params
        self._from_uri = from_uri
        self._to_uri = to_uri
        self._msg_type = msg_type
        self._uri_transform = uri_transform

        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            from_transport = TransportType.REDIS
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            from_transport = TransportType.AMQP
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            from_transport = TransportType.AMQP
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            from_transport = TransportType.REDIS
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_REDIS:
            from_transport = TransportType.MQTT
            to_transport = TransportType.REDIS
        elif self._btype == RPCBridgeType.MQTT_TO_AMQP:
            from_transport = TransportType.MQTT
            to_transport = TransportType.AMQP
        elif self._btype == RPCBridgeType.MQTT_TO_MQTT:
            from_transport = TransportType.MQTT
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.REDIS_TO_MQTT:
            from_transport = TransportType.REDIS
            to_transport = TransportType.MQTT
        elif self._btype == RPCBridgeType.AMQP_TO_MQTT:
            from_transport = TransportType.AMQP
            to_transport = TransportType.MQTT
        self._sub = endpoint_factory(
            EndpointType.PSubscriber, from_transport
        )(
            topic=self._from_uri,
            msg_type=self._msg_type,
            conn_params=self._from_broker_params,
            on_message=self.on_message
        )
        self._pub = endpoint_factory(
            EndpointType.MPublisher, to_transport
        )(
            msg_type=self._msg_type,
            conn_params=self._to_broker_params,
        )

    def _transform_uri(self, uri: str):
        if self._btype == RPCBridgeType.REDIS_TO_AMQP:
            uri = uri.replace('/', '.')
        elif self._btype == RPCBridgeType.AMQP_TO_REDIS:
            pass
        elif self._btype == RPCBridgeType.AMQP_TO_AMQP:
            pass
        elif self._btype == RPCBridgeType.REDIS_TO_REDIS:
            pass
        elif self._btype == RPCBridgeType.MQTT_TO_REDIS:
            pass
            # uri = uri.replace('/', '.')
        elif self._btype == RPCBridgeType.MQTT_TO_AMQP:
            uri = uri.replace('/', '.')
        elif self._btype == RPCBridgeType.MQTT_TO_MQTT:
            pass
        elif self._btype == RPCBridgeType.REDIS_TO_MQTT:
            uri = uri.replace('.', '/')
        elif self._btype == RPCBridgeType.AMQP_TO_MQTT:
            uri =  uri.replace('.', '/')
        return uri

    def on_message(self, msg: PubSubMessage, topic: str):
        """on_message.

        Args:
            msg (PubSubMessage): Published Message.
            topic (str): topic
        """
        if self._to_uri != '':
            to_topic = f'{self._to_uri}.{topic}'
        else:
            to_topic = topic
        to_topic = self._transform_uri(to_topic)
        for tr in self._uri_transform:
            _from = tr[0]
            _to = tr[1]
            to_topic = to_topic.replace(_from, _to)
        self._pub.publish(msg, to_topic)

    def stop(self):
        """stop.
        """
        self._sub.stop()

    def run(self):
        """run.
        """
        self._sub.run()
        self.log.info(
            f'Started B2B Multi-Topic Bridge ' + \
            f'<{self._from_broker_params.host}:' + \
            f'{self._from_broker_params.port}[{self._from_uri}] ' + \
            f'-> {self._to_broker_params.host}:' + \
            f'{self._to_broker_params.port}[{self._to_uri}.*]>')
