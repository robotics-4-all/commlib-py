from commlib.connection import ConnectionParametersBase


class BaseTransport:
    _connected = False

    def __init__(self,
                 conn_params: ConnectionParametersBase
                 ):
        self._conn_params = conn_params

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
