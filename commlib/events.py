import logging
from typing import Any, Dict, Text

from pydantic import BaseModel, NoneIsAllowedError

from commlib.endpoints import BaseEndpoint
from commlib.connection import BaseConnectionParameters
from commlib.serializer import JSONSerializer, Serializer
from commlib.utils import gen_random_id

em_logger = None


class Event(BaseModel):
    name: Text
    uri: Text
    description: Text = ''
    data: Dict[str, Any] = {}


class BaseEventEmitter(BaseEndpoint):
    """BaseEventEmitter.
    """
    def __init__(self,
                 name: Text = None,
                 *args, **kwargs):
        """__init__.

        Args:
            name (Text): name
            *args (List):
            **kwargs (Dict):
        """
        super().__init__(*args, **kwargs)
        if name is None:
            name = gen_random_id()
        self._name = name
        self.log.info(f'Initiated Event Emitter <{self._name}>')

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
