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
    def __init__(self):
        pass


class NodeInputPort(NodePort):
    def __init__(self, *args, **kwargs):
        super(NodeInputPort, self).__init__(*args, **kwargs)


class NodeOutputPort(NodePort):
    def __init__(self, *args, **kwargs):
        super(NodeOutputPort, self).__init__(*args, **kwargs)


class NodePortType(IntEnum):
    Input = 1
    Output = 2


class NodeExecutorType(IntEnum):
    ProcessExecutor = 1
    ThreadExecutor = 2


class HeartbeatThread(threading.Thread):
    def __init__(self, pub_instance=None,
                 interval: int = 10,
                 logger: Logger = None,
                 *args, **kwargs):
        super(HeartbeatThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._rate_secs = interval
        self._heartbeat_pub = pub_instance
        if logger is None:
            logger = Logger(self.__class__.__name__)
        self.logger = logger
        self.daemon = True

    def run(self):
        try:
            msg = HeartbeatMessage(ts=self.get_ts())
            while not self._stop_event.isSet():
                if self._heartbeat_pub._msg_type == None:
                    self._heartbeat_pub.publish(msg.as_dict())
                else:
                    self._heartbeat_pub.publish(msg)
                self._stop_event.wait(self._rate_secs)
        except Exception as exc:
            self.logger.info(f'Exception in Heartbeat-Thread: {exc}')
        finally:
            self.logger.info('Heartbeat Thread Ended')

    def force_join(self, timeout=None):
        """ Stop the thread. """
        self._stop_event.set()
        threading.Thread.join(self, timeout)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def get_ts(self):
        timestamp = (time.time() + 0.5) * 1000000
        return int(timestamp)


class Node(object):
    def __init__(self, node_name: Text = '',
                 executor: NodeExecutorType = NodeExecutorType.ThreadExecutor,
                 transport_type: TransportType = TransportType.REDIS,
                 transport_connection_params=None,
                 max_workers: int = 4,
                 remote_logger: bool = False,
                 remote_logger_uri: str = '',
                 debug: bool = False,
                 device_id: str = None):
        if executor == NodeExecutorType.ThreadExecutor:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        elif executor == NodeExecutorType.ProcessExecutor:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)

        if node_name == '' or node_name is None:
            node_name = gen_random_id()
        self._node_name = node_name

        self._device_id = device_id
        if device_id is None:
            self._namespace = f'{self._node_name}'
        else:
            self._namespace = f'thing.{device_id}.{self._node_name}'

        self._debug = debug

        self._publishers = []
        self._subscribers = []
        self._rpc_services = []
        self._rpc_clients = []
        self._action_servers = []
        self._action_clients = []
        self._event_emitters = []
        self._rpc_bridges = []
        self._topic_bridges = []

        self._global_tranport_type = transport_type
        if transport_type == TransportType.REDIS:
            import commlib.transports.redis as comm
        elif transport_type == TransportType.AMQP:
            import commlib.transports.amqp as comm
        self._commlib = comm

        if transport_connection_params is None:
            if transport_type == TransportType.REDIS:
                from commlib.transports.redis import \
                    UnixSocketConnectionParameters as conn_params
            elif transport_type == TransportType.AMQP:
                from commlib.transports.amqp import \
                    ConnectionParameters as conn_params
            transport_connection_params = conn_params()
        self._conn_params = transport_connection_params

        if remote_logger:
            self._logger = RemoteLogger(self._node_name, transport_type,
                                        self._conn_params,
                                        remote_topic=remote_logger_uri,
                                        debug=debug)
        else:
            self._logger = Logger(self._node_name, debug=debug)
        self._logger.info(f'Created Node <{self._node_name}>')

    def init_heartbeat_thread(self):
        topic = f'{self._namespace}.heartbeat'
        self._hb_thread = HeartbeatThread(
            self.create_publisher(topic=topic, msg_type=HeartbeatMessage))
        self._hb_thread.start()
        self._logger.info(f'Started Publishing heartbeats: <{topic}>')

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

    def run_forever(self):
        while True:
            time.sleep(0.001)

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

    def create_rpc_bridge(self, *args, **kwargs):
        br = self._commlib.RPCBridge(logger=self._logger,
                                     *args, **kwargs)
        self._rpc_bridges.append(br)
        return br

    def create_topic_bridge(self, *args, **kwargs):
        br = self._commlib.TopicBridge(logger=self._logger,
                                       *args, **kwargs)
        self._topic_bridges.append(br)
        return br
