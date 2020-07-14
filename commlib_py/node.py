from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures.thread

from commlib_py.endpoints import TransportType
from commlib_py.utils import gen_random_id


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
    def __init__(self, node_name=None,
                 executor: NodeExecutorType = NodeExecutorType.ThreadExecutor,
                 transport_type: TransportType = TransportType.REDIS,
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
            import commlib_py.transports.redis as comm
        elif transport_type == TransportType.AMQP:
            import commlib_py.transports.amqp as comm
        self._commlib = comm

        self._conn_params = comm.UnixSocketConnectionParameters()

    @property
    def ports(self):
        return self._input_ports + self._output_ports

    def create_publisher(self, transport_type=None, *args, **kwargs):
        """Creates a new Publisher Endpoint.

        Args:
            transport_type (TransportType): The type of the transport to use.
            If None it uses the Node's default transport.
        """
        return self._commlib.Publisher(*args, **kwargs)

