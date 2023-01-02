from typing import Text, Dict, Any

from commlib.serializer import JSONSerializer, Serializer
from commlib.logger import Logger
from commlib.utils import gen_random_id
from pydantic import BaseModel, NoneIsAllowedError
from commlib.connection import BaseConnectionParameters

em_logger = None


class Event(BaseModel):
    """Event.
    """

    name: Text
    uri: Text
    description: Text = ''
    data: Dict[str, Any] = {}


class BaseEventEmitter:
    """BaseEventEmitter.
    """
    @classmethod
    def logger(cls) -> Logger:
        global em_logger
        if em_logger is None:
            em_logger = Logger(__name__)
        return em_logger

    def __init__(self,
                 name: Text = None,
                 debug: bool = False,
                 conn_params: BaseConnectionParameters = None,
                 serializer: Serializer = None):
        """__init__.

        Args:
            name (Text): name
            debug (bool): debug
            serializer (Serializer): serializer
        """
        self._conn_params = conn_params
        if name is None:
            name = gen_random_id()
        self._name = name
        self._debug = debug
        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self.log.info(f'Initiated Event Emitter <{self._name}>')

    @property
    def debug(self) -> bool:
        """debug.

        Args:

        Returns:
            bool:
        """
        return self._debug

    @property
    def log(self) -> Logger:
        """logger.

        Args:

        Returns:
            Logger:
        """
        return self.logger()

    def send_event(self, event: Event) -> None:
        """send_event.

        Args:
            event (Event): event

        Returns:
            None:
        """
        raise NotImplementedError()

    def run(self):
        self._transport.start()

    def stop(self) -> None:
        self._transport.stop()

    def __del__(self):
        self.stop()
