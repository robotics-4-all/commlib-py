from commlib.connection import ConnectionParametersBase
from commlib.logger import Logger


transport_logger = None


class BaseTransport:
    _connected = False

    @classmethod
    def logger(cls) -> Logger:
        global transport_logger
        if transport_logger is None:
            transport_logger = Logger(__name__)
        return transport_logger

    def __init__(self,
                 conn_params: ConnectionParametersBase
                 ):
        self._conn_params = conn_params

    @property
    def log(self):
        return self.logger()

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def loop_forever(self):
        raise NotImplementedError()