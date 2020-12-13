from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures.thread
import time
import threading
from typing import Dict, List, Any, Text

from commlib.endpoints import TransportType
from commlib.utils import gen_random_id
from commlib.logger import RemoteLogger, Logger
from commlib.bridges import TopicBridge, RPCBridge
from commlib.msg import HeartbeatMessage


class NodePort(object):
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


class Node(object):
    """Node.
    """

    def __init__(self, node_name: Text = '',
                 transport_type: TransportType = TransportType.REDIS,
                 ## DEPRECATED - Used only for backward compatibility
                 transport_connection_params=None,
                 connection_params=None,
                 max_workers: int = 4,
                 remote_logger: bool = False,
                 remote_logger_uri: Text = '',
                 debug: bool = False,
                 heartbeat_thread: bool = True,
                 heartbeat_uri: str = None,
                 device_id: Text = None):
        """__init__.

        Args:
            node_name (Text): node_name
            transport_type (TransportType): transport_type
            transport_connection_params:
            connection_params:
            max_workers (int): max_workers
            remote_logger (bool): remote_logger
            remote_logger_uri (Text): remote_logger_uri
            debug (bool): debug
            device_id (Text): device_id
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
        self._device_id = device_id
        if device_id is None:
            self._namespace = f'{self._node_name}'
        else:
            self._namespace = f'thing.{device_id}.{self._node_name}'

        self._publishers = []
        self._subscribers = []
        self._rpc_services = []
        self._rpc_clients = []
        self._action_servers = []
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

        if transport_connection_params is None:
            if transport_type == TransportType.REDIS:
                from commlib.transports.redis import \
                    UnixSocketConnectionParameters as ConnParams
            elif transport_type == TransportType.AMQP:
                from commlib.transports.amqp import \
                    ConnectionParameters as ConnParams
            elif transport_type == TransportType.MQTT:
                from commlib.transports.mqtt import \
                    ConnectionParameters as ConnParams
            transport_connection_params = ConnParams()
        self._conn_params = transport_connection_params
        if connection_params is not None:
            self._conn_params = connection_params

        if remote_logger:
            self._logger = RemoteLogger(self._node_name, transport_type,
                                        self._conn_params,
                                        remote_topic=remote_logger_uri,
                                        debug=debug)
        else:
            self._logger = Logger(self._node_name, debug=debug)
        self._logger.info(f'Created Node <{self._node_name}>')

    def init_heartbeat_thread(self, topic: str = None):
        """init_heartbeat_thread.

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

    @property
    def input_ports(self):
        return {
            'subscriber': self._subscribers,
            'rpc_service': self._rpc_services,
            'action_server': self._action_servers
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
        Starts Services, Subscribers and ActionServers.
        Also starts the heartbeat thread (if enabled).

        Args:

        Returns:
            None:
        """
        for s in self._subscribers:
            s.run()
        for r in self._rpc_services:
            r.run()
        for r in self._action_servers:
            r.run()
        if self._heartbeat_thread:
            self.init_heartbeat_thread(self._heartbeat_uri)
        self.state = NodeState.RUNNING

    def run_forever(self, sleep_rate: float = 0.001) -> None:
        """run_forever.
        Starts Services, Subscribers and ActionServers and blocks
        the main thread from exiting.
        Also starts the heartbeat thread (if enabled).

        Args:
            sleep_rate (float): Rate to sleep between wait-state iterations.
        """
        if self.state != NodeState.RUNNING:
            self.run()
        while True:
            time.sleep(sleep_rate)

    def create_publisher(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        pub = self._commlib.Publisher(conn_params=self._conn_params,
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
        """Creates a new ActionServer Endpoint.
        """
        action =  self._commlib.ActionServer(conn_params=self._conn_params,
                                             logger = self._logger,
                                             *args, **kwargs)
        self._action_servers.append(action)
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
