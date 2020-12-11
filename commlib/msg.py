import time
import uuid
import json
import hashlib

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from dataclasses import is_dataclass
from dataclasses import make_dataclass
from dataclasses import asdict as as_dict
from dataclasses import astuple as as_tuple
from typing import List, Dict, Tuple, Sequence, Any, Text

import redis

from .serializer import JSONSerializer


@DataClass
class Object:
    """Object Class.
    Base Object Class. Implements base methods to inherit.
    """
    def __iter__(self) -> tuple:
        yield from as_tuple(self)

    def as_dict(self) -> dict:
        return as_dict(self)

    def from_dict(self, data_dict: dict) -> None:
        """from_dict.
        Fill message data fields from dict key-value pairs.

        Args:
            data_dict (dict): data_dict

        Returns:
            None:
        """
        for key, val in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, val)
            else:
                raise AttributeError(
                    f'{self.__class__.__name__} has no attribute {key}')


@DataClass
class MetaInfoObject(Object):
    """MetaInfoObject Class.
    Implements the Header data class.
    """
    seq: int = DataField(default=0)
    timestamp: int = DataField(default=-1)
    node_id: Text = DataField(default='')
    agent: Text = DataField(default='commlib-py')

    def __post_init__(self):
        self.timestamp = int(time.time())


class RPCMessage:
    """RPCObject Class.
    RPC Object Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """

    @DataClass
    class Request(Object):
        """Request.
        RPC Request Message
        """

        meta: MetaInfoObject = MetaInfoObject()

    @DataClass
    class Response(Object):
        """Response.
        RPC Response Message
        """

        meta: MetaInfoObject = MetaInfoObject()


@DataClass
class PubSubMessage(Object):
    """PubSubObject Class.
    Implementation of the PubSubObject Base Data class.
    """
    meta: MetaInfoObject = DataField(default=MetaInfoObject())


class ActionMessage(Object):
    """ActionMessage.
    """

    @DataClass
    class Goal(Object):
        """Goal.
        Action Goal Message
        """

        meta: MetaInfoObject = MetaInfoObject()

    @DataClass
    class Result(Object):
        """Result.
        Action Result Message
        """

        meta: MetaInfoObject = MetaInfoObject()

    @DataClass
    class Feedback(Object):
        """Feedback.
        Action Feedback Message
        """

        meta: MetaInfoObject = MetaInfoObject()


@DataClass
class HeartbeatMessage(PubSubMessage):
    ts: int = -1
