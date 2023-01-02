from commlib.connection import BaseConnectionParameters
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.transports import BaseTransport


class ConnectionParameters(BaseConnectionParameters):
    pass


class MockTransport(BaseTransport):
    def start(self):
        self._connected = True

    def stop(self):
        self._connected = False

class Publisher(BasePublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport(self._conn_params)


class Subscriber(BaseSubscriber):
    pass
