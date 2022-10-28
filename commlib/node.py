import threading
import time
from enum import IntEnum
from functools import wraps
from typing import Any, Dict, List, Optional
from commlib.compression import CompressionType

from commlib.endpoints import TransportType
from commlib.logger import Logger
from commlib.msg import HeartbeatMessage, RPCMessage
from commlib.utils import gen_random_id

n_logger = None


class NodePort:
    """NodePort.
    """

    def __init__(self):
        pass


class NodeInputPort(NodePort):
    """NodeInputPort.
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)


class NodeOutputPort(NodePort):
    """NodeOutputPort.
    """

    def __init__(self, *args, **kwargs):
        """__init__.

        Args:
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)


class NodePortType(IntEnum):
    """NodePortType.
    """

    Input = 1
    Output = 2


class NodeExecutorType(IntEnum):
    """NodeExecutorType.
    """

    ProcessExecutor = 1
    ThreadExecutor = 2


class NodeState(IntEnum):
    """NodeState.
    """

    IDLE = 1
    RUNNING = 2
    STOPPED = 4
    EXITED = 3


class HeartbeatThread(threading.Thread):
    """HeartbeatThread.
    """
    @classmethod
    def logger(cls) -> Logger:
        global n_logger
        if n_logger is None:
            n_logger = Logger('MQTTHeartbeatThread')
        return n_logger

    def __init__(self, pub_instance=None,
                 interval: int = 10,
                 *args, **kwargs):
        """__init__.

        Args:
            pub_instance:
            interval (int): interval
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._rate_secs = interval
        self._heartbeat_pub = pub_instance
        self.daemon = True

    def run(self):
        """run.
        """
        try:
            msg = HeartbeatMessage(ts=self.get_ts())
            while not self._stop_event.isSet():
                self.logger().debug(
                    f'Sending heartbeat message - {self._heartbeat_pub._topic}')
                if self._heartbeat_pub._msg_type == None:
                    self._heartbeat_pub.publish(msg.dict())
                else:
                    self._heartbeat_pub.publish(msg)
                # Wait for n seconds or until stop event is raised
                self._stop_event.wait(self._rate_secs)
                msg.ts = self.get_ts()
        except Exception as exc:
            self.logger().error(f'Exception in Heartbeat-Thread: {exc}')
        finally:
            self.logger().error('Heartbeat Thread Ended')

    def force_join(self, timeout: float = None):
        """force_join.
        Sudo stop the thread!

        Args:
            timeout (float): timeout
        """
        self._stop_event.set()
        threading.Thread.join(self, timeout)

    def stop(self):
        """stop.
        """
        self._stop_event.set()

    def stopped(self):
        """stopped.
        """
        return self._stop_event.is_set()

    def get_ts(self):
        """get_ts.
        """
        timestamp = (time.time() + 0.5) * 1000000
        return int(timestamp)


class _NodeStartMessage(RPCMessage):
    class Request(RPCMessage.Request):
        pass

    class Response(RPCMessage.Response):
        status: int = 0
        error: str = ''


class _NodeStopMessage(RPCMessage):
    class Request(RPCMessage.Request):
        pass

    class Response(RPCMessage.Response):
        status: int = 0
        error: str = ''


class Node:
    """Node.
    """
    @classmethod
    def logger(cls) -> Logger:
        global n_logger
        if n_logger is None:
            n_logger = Logger(f'node-{cls.__name__}')
        return n_logger

    def __init__(self,
                 node_name: Optional[str] = '',
                 connection_params: Optional[Any] = None,
                 transport_connection_params: Optional[Any] = None,
                 debug: Optional[bool] = False,
                 heartbeat_thread: Optional[bool] = True,
                 heartbeat_uri: Optional[str] = None,
                 compression: CompressionType = CompressionType.NO_COMPRESSION,
                 ctrl_services: Optional[bool] = False):
        """__init__.

        Args:
            node_name (Optional[str]): node_name
            transport_type (Optional[TransportType]): transport_type
            connection_params (Optional[Any]): connection_params
            transport_connection_params (Optional[Any]): Same with connection_params.
                Used for backward compatibility
            debug (Optional[bool]): debug
            heartbeat_thread (Optional[bool]): heartbeat_thread
            heartbeat_uri (Optional[str]): heartbeat_uri
            ctrl_services (Optional[bool]): ctrl_services
        """
        if node_name == '' or node_name is None:
            node_name = gen_random_id()
        node_name = node_name.replace('-', '_')
        self._node_name = node_name
        self._debug = debug
        self._heartbeat_thread = heartbeat_thread
        self._heartbeat_uri = heartbeat_uri
        self._compression = compression
        self._hb_thread = None
        self.state = NodeState.IDLE
        self._has_ctrl_services = ctrl_services
        self._namespace = f'{self._node_name}'

        self._publishers = []
        self._subscribers = []
        self._rpc_services = []
        self._rpc_clients = []
        self._action_services = []
        self._action_clients = []
        self._event_emitters = []


        ## Set default ConnectionParameters ---->
        if transport_connection_params is not None and connection_params is None:
            connection_params = transport_connection_params
        self._conn_params = connection_params
        type_str = str(type(self._conn_params)).split('\'')[1]

        if type_str == 'commlib.transports.mqtt.ConnectionParameters':
            import commlib.transports.mqtt as transport_module
        elif type_str == 'commlib.transports.redis.ConnectionParameters':
            import commlib.transports.redis as transport_module
        elif type_str == 'commlib.transports.amqp.ConnectionParameters':
            import commlib.transports.amqp as transport_module
        else:
            raise ValueError('Transport type is not supported!')
        self._transport_module = transport_module

        self.log.info(f'Created Node <{self._node_name}>')

    @property
    def log(self) -> Logger:
        """logger.

        Args:

        Returns:
            Logger:
        """
        return self.logger()

    def init_heartbeat_thread(self, topic: str = None) -> None:
        """init_heartbeat_thread.
        Starts the heartbeat thread. Heartbeat messages are sent periodically
        to inform about correct execution of the node.

        Args:
            topic (str): topic
        """
        if topic is None:
            topic = f'{self._namespace}.heartbeat'
        self._hb_thread = HeartbeatThread(
            self.create_publisher(topic=topic, msg_type=HeartbeatMessage)
        )
        self._hb_thread.start()
        self.log.info(
            f'Started Heartbeat Publisher <{topic}> in background')

    def init_stop_service(self, uri: str = None) -> None:
        if uri is None:
            uri = f'{self._namespace}.stop'
        stop_rpc = self.create_rpc(rpc_name=uri,
                                   msg_type=_NodeStopMessage,
                                   on_request=self._stop_rpc_callback)
        stop_rpc.run()
        self._stop_rpc = stop_rpc

    def _stop_rpc_callback(self, msg: _NodeStopMessage.Request) -> \
            _NodeStopMessage.Response:
        resp = _NodeStopMessage.Response()
        if self.state == NodeState.RUNNING:
            self.state = NodeState.STOPPED
            self.stop()
        else:
            resp.status = 1
            resp.error = 'Cannot make the transition from current state!'
        return resp

    def init_start_service(self, uri: str = None) -> None:
        if uri is None:
            uri = f'{self._namespace}.start'
        start_rpc = self.create_rpc(rpc_name=uri,
                                    msg_type=_NodeStartMessage,
                                    on_request=self._start_rpc_callback)
        start_rpc.run()
        self._start_rpc = start_rpc

    def _start_rpc_callback(self, msg: _NodeStartMessage.Request) -> \
            _NodeStartMessage.Response:
        resp = _NodeStartMessage.Response()
        if self.state == NodeState.STOPPED:
            self.run()
        else:
            resp.status = 1
            resp.error = 'Cannot make the transition from current state!'
        return resp

    @property
    def input_ports(self) -> dict:
        return {
            'subscriber': self._subscribers,
            'rpc_service': self._rpc_services,
            'action_service': self._action_services
        }

    @property
    def output_ports(self):
        return {
            'publisher': self._publishers,
            'rpc_client': self._rpc_clients,
            'action_client': self._action_clients
        }

    @property
    def ports(self):
        return {
            'input': self.input_ports,
            'output': self.output_ports
        }

    def get_logger(self):
        return self.logger()

    def run(self) -> None:
        """run.
        Starts Services, Subscribers and ActionServices.
        Also starts the heartbeat thread (if enabled).

        Args:

        Returns:
            None:
        """
        for s in self._subscribers:
            s.run()
        for r in self._rpc_services:
            r.run()
        for r in self._action_services:
            r.run()
        if self._heartbeat_thread:
            self.init_heartbeat_thread(self._heartbeat_uri)
        if self._has_ctrl_services:
            self.init_start_service()
        if self._has_ctrl_services:
            self.init_stop_service()
        self.state = NodeState.RUNNING

    def run_forever(self, sleep_rate: float = 0.001) -> None:
        """run_forever.
        Starts Services, Subscribers and ActionServices and blocks
        the main thread from exiting.
        Also starts the heartbeat thread (if enabled).

        Args:
            sleep_rate (float): Rate to sleep between wait-state iterations.
        """
        if self.state != NodeState.RUNNING:
            self.run()
        while self.state != NodeState.EXITED:
            time.sleep(sleep_rate)
        self.stop()

    def stop(self):
        for s in self._subscribers:
            s.stop()
        for r in self._rpc_services:
            r.stop()
        for r in self._action_services:
            r.stop()

    def create_publisher(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        pub = self._transport_module.Publisher(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._publishers.append(pub)
        return pub

    def create_mpublisher(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        pub = self._transport_module.MPublisher(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._publishers.append(pub)
        return pub

    def create_subscriber(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        sub =  self._transport_module.Subscriber(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._subscribers.append(sub)
        return sub

    def create_psubscriber(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        sub =  self._transport_module.PSubscriber(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._subscribers.append(sub)
        return sub

    def subscriber_callback(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return self.create_subscriber(*args, **kwargs)
        return wrapper

    def create_rpc(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        rpc = self._transport_module.RPCService(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._rpc_services.append(rpc)
        return rpc

    def create_rpc_client(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        client = self._transport_module.RPCClient(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._rpc_clients.append(client)
        return client

    def create_action(self, *args, **kwargs):
        """Creates a new ActionService Endpoint.
        """
        action =  self._transport_module.ActionService(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._action_services.append(action)
        return action

    def create_action_client(self, *args, **kwargs):
        """Creates a new ActionClient Endpoint.
        """
        aclient = self._transport_module.ActionClient(
            conn_params=self._conn_params,
            logger=self.logger(),
            compression=self._compression,
            *args, **kwargs
        )
        self._action_clients.append(aclient)
        return aclient

    def create_event_emitter(self, *args, **kwargs):
        """Creates a new EventEmitter Endpoint.
        """
        em = self._transport_module.EventEmitter(
            conn_params=self._conn_params,
            compression=self._compression,
            *args, **kwargs
        )
        self._event_emitters.append(em)
        return em
