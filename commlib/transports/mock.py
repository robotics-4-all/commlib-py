from commlib.connection import ConnectionParametersBase
from commlib.pubsub import BasePublisher, BaseSubscriber


class ConnectionParameters(ConnectionParametersBase):
    pass


class MockTransport:
    _connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self):
        pass

    def disconnect(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def loop_forever(self):
        pass


class Publisher(BasePublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport()


class Subscriber(BaseSubscriber):
    pass
