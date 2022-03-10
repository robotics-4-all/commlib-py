from functools import wraps
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures.thread
import time
import threading
from typing import Dict, List, Any, Optional

from commlib.endpoints import TransportType
from commlib.utils import gen_random_id
from commlib.logger import Logger
from commlib.bridges import TopicBridge, RPCBridge
from commlib.msg import HeartbeatMessage, RPCMessage, DataClass, DataField


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

    def __init__(self, pub_instance=None,
                 interval: int = 10,
                 logger: Logger = None,
                 *args, **kwargs):
        """__init__.

        Args:
            pub_instance:
            interval (int): interval
            logger (Logger): logger
            args:
            kwargs:
        """
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._rate_secs = interval
        self._heartbeat_pub = pub_instance
        if logger is None:
            logger = Logger(self.__class__.__name__)
        self.logger = logger
        self.daemon = True

    def run(self):
        """run.
        """
        try:
            msg = HeartbeatMessage(ts=self.get_ts())
            while not self._stop_event.isSet():
                self.logger.info(
                    f'Sending heartbeat message - {self._heartbeat_pub._topic}')
                if self._heartbeat_pub._msg_type == None:
                    self._heartbeat_pub.publish(msg.as_dict())
                else:
                    self._heartbeat_pub.publish(msg)
                # Wait for n seconds or until stop event is raised
                self._stop_event.wait(self._rate_secs)
                msg.ts = self.get_ts()
        except Exception as exc:
            self.logger.info(f'Exception in Heartbeat-Thread: {exc}')
        finally:
            self.logger.info('Heartbeat Thread Ended')

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


class NodeStartMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        pass

    @DataClass
    class Response(RPCMessage.Response):
        status: int = DataField(default=0)
        error: str = DataField(default='')


class NodeStopMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        pass

    @DataClass
    class Response(RPCMessage.Response):
        status: int = DataField(default=0)
        error: str = DataField(default='')


class Node:
    """Node.
    """

    def __init__(self,
                 node_name: Optional[str] = '',
                 transport_type: Optional[TransportType] = TransportType.REDIS,
                 connection_params: Optional[Any] = None,
                 transport_connection_params: Optional[Any] = None,
                 remote_logger: Optional[bool] = False,
                 remote_logger_uri: Optional[str] = '',
                 debug: Optional[bool] = False,
                 heartbeat_thread: Optional[bool] = True,
                 heartbeat_uri: Optional[str] = None,
                 ctrl_services: Optional[bool] = False):
        """__init__.

        Args:
            node_name (Optional[str]): node_name
            transport_type (Optional[TransportType]): transport_type
            connection_params (Optional[Any]): connection_params
            transport_connection_params (Optional[Any]): Same with connection_params.
                Used for backward compatibility
            remote_logger (Optional[bool]): remote_logger
            remote_logger_uri (Optional[str]): remote_logger_uri
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

        if transport_type == TransportType.REDIS:
            import commlib.transports.redis as comm
        elif transport_type == TransportType.AMQP:
            import commlib.transports.amqp as comm
        elif transport_type == TransportType.MQTT:
            import commlib.transports.mqtt as comm
        else:
            raise ValueError('Transport type is not supported!')
        self._commlib = comm

        ## Set default ConnectionParameters ---->
        if transport_connection_params is not None:
            self._conn_params = transport_connection_params
        elif connection_params is None:
            if transport_type == TransportType.REDIS:
                from commlib.transports.redis import \
                    UnixSocketConnectionParameters as ConnParams
            elif transport_type == TransportType.AMQP:
                from commlib.transports.amqp import \
                    ConnectionParameters as ConnParams
            elif transport_type == TransportType.MQTT:
                from commlib.transports.mqtt import \
                    ConnectionParameters as ConnParams
            connection_params = ConnParams()
            self._conn_params = connection_params
        else:
            self._conn_params = connection_params
        ## <--------------------------------------

        self._logger = Logger(self._node_name, debug=debug)
        self._logger.info(f'Created Node <{self._node_name}>')

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
            self.create_publisher(topic=topic, msg_type=HeartbeatMessage),
            logger=self._logger
        )
        self._hb_thread.start()
        self._logger.info(
            f'Started Heartbeat Publisher <{topic}> in background')

    def init_stop_service(self, uri: str = None) -> None:
        if uri is None:
            uri = f'{self._namespace}.stop'
        stop_rpc = self.create_rpc(rpc_name=uri,
                                   msg_type=NodeStopMessage,
                                   on_request=self._stop_rpc_callback)
        stop_rpc.run()
        self._stop_rpc = stop_rpc

    def _stop_rpc_callback(self, msg: NodeStopMessage.Request) -> \
            NodeStopMessage.Response:
        resp = NodeStopMessage.Response()
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
                                    msg_type=NodeStartMessage,
                                    on_request=self._start_rpc_callback)
        start_rpc.run()
        self._start_rpc = start_rpc

    def _start_rpc_callback(self, msg: NodeStartMessage.Request) -> \
            NodeStartMessage.Response:
        resp = NodeStartMessage.Response()
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
        return self._logger

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
        pub = self._commlib.Publisher(conn_params=self._conn_params,
                                      logger = self._logger,
                                      *args, **kwargs)
        self._publishers.append(pub)
        return pub

    def create_mpublisher(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        pub = self._commlib.MPublisher(conn_params=self._conn_params,
                                       logger = self._logger,
                                       *args, **kwargs)
        self._publishers.append(pub)
        return pub

    def create_subscriber(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        sub =  self._commlib.Subscriber(conn_params=self._conn_params,
                                        logger = self._logger,
                                        *args, **kwargs)
        self._subscribers.append(sub)
        return sub

    def create_psubscriber(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        sub =  self._commlib.PSubscriber(conn_params=self._conn_params,
                                         logger = self._logger,
                                         *args, **kwargs)
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
        rpc = self._commlib.RPCService(conn_params=self._conn_params,
                                       logger = self._logger,
                                       *args, **kwargs)
        self._rpc_services.append(rpc)
        return rpc

    def create_rpc_client(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        client = self._commlib.RPCClient(conn_params=self._conn_params,
                                         logger = self._logger,
                                         *args, **kwargs)
        self._rpc_clients.append(client)
        return client

    def create_action(self, *args, **kwargs):
        """Creates a new ActionService Endpoint.
        """
        action =  self._commlib.ActionService(conn_params=self._conn_params,
                                             logger = self._logger,
                                             *args, **kwargs)
        self._action_services.append(action)
        return action

    def create_action_client(self, *args, **kwargs):
        """Creates a new ActionClient Endpoint.
        """
        aclient = self._commlib.ActionClient(conn_params=self._conn_params,
                                             logger = self._logger,
                                             *args, **kwargs)
        self._action_clients.append(aclient)
        return aclient

    def create_event_emitter(self, *args, **kwargs):
        """Creates a new EventEmitter Endpoint.
        """
        em = self._commlib.EventEmitter(conn_params=self._conn_params,
                                        logger = self._logger,
                                        *args, **kwargs)
        self._event_emitters.append(em)
        return em
