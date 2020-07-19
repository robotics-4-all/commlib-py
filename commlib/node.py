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
                 max_workers: int = 4):
        if executor == NodeExecutorType.ThreadExecutor:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        elif executor == NodeExecutorType.ProcessExecutor:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)

        if node_name is None:
            node_name = gen_random_id()
        self._node_name = node_name

        self._input_ports = []
        self._output_ports = []
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
                                    self._conn_params)

    @property
    def ports(self):
        return {
            'input': self._input_ports,
            'output': self._output_ports
        }

    def create_publisher(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        return self._commlib.Publisher(conn_params=self._conn_params,
                                       logger = self._logger,
                                       *args, **kwargs)

    def create_subscriber(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        return self._commlib.Subscriber(conn_params=self._conn_params,
                                        logger = self._logger,
                                        *args, **kwargs)

    def create_rpc(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        return self._commlib.RPCService(conn_params=self._conn_params,
                                       logger = self._logger,
                                       *args, **kwargs)

    def create_rpc_client(self, *args, **kwargs):
        """Creates a new Publisher Endpoint.
        """
        return self._commlib.RPCClient(conn_params=self._conn_params,
                                       logger = self._logger,
                                       *args, **kwargs)

    def create_action(self, *args, **kwargs):
        """Creates a new ActionServer Endpoint.
        """
        return self._commlib.ActionServer(conn_params=self._conn_params,
                                          logger = self._logger,
                                          *args, **kwargs)

    def create_action_client(self, *args, **kwargs):
        """Creates a new ActionClient Endpoint.
        """
        return self._commlib.ActionClient(conn_params=self._conn_params,
                                          logger = self._logger,
                                          *args, **kwargs)

