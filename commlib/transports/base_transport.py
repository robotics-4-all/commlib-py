import logging

from commlib.connection import BaseConnectionParameters

transport_logger = None


class BaseTransport:
    _connected = False

    @classmethod
    def logger(cls) -> logging.Logger:
        global transport_logger
        if transport_logger is None:
            transport_logger = logging.getLogger(__name__)
        return transport_logger

    def __init__(self,
                 conn_params: BaseConnectionParameters,
                 debug: bool = False
                 ):
        self._conn_params = conn_params
        self._debug = debug

    @property
    def log(self):
        return self.logger()

    @property
    def debug(self):
        return self._debug

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
