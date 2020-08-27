from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures.thread

from commlib.endpoints import TransportType
from commlib.utils import gen_random_id
from commlib.logger import RemoteLogger


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


class Node(object):
    def __init__(self, node_name=None, namespace: str = '',
                 executor: NodeExecutorType = NodeExecutorType.ThreadExecutor,
                 transport_type: TransportType = TransportType.REDIS,
                 transport_connection_params=None,
                 max_workers: int = 4,
                 debug: bool = False):
        if executor == NodeExecutorType.ThreadExecutor:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        elif executor == NodeExecutorType.ProcessExecutor:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)

        if node_name is None:
            node_name = gen_random_id()
        self._node_name = node_name

        self._debug = debug

        self._publishers = []
        self._subscribers = []
        self._rpc_services = []
        self._rpc_clients = []
        self._action_servers = []
        self._action_clients = []

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

        self._logger = RemoteLogger(self._node_name, transport_type,
                                    self._conn_params, debug=debug)

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
