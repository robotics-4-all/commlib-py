from commlib.connection import ConnectionParametersBase
from commlib.pubsub import BasePublisher, BaseSubscriber
from commlib.transports import BaseTransport


class ConnectionParameters(ConnectionParametersBase):
    pass


class MockTransport(BaseTransport):
    pass


class Publisher(BasePublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transport = MockTransport()


class Subscriber(BaseSubscriber):
    pass
