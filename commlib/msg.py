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
        """Fill message data fields from dict key-value pairs."""
        for key, val in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, val)
            else:
                raise AttributeError(
                    f'{self.__class__.__name__} has no attribute {key}')


@DataClass
class HeaderObject(Object):
    """HeaderObject Class.
    Implements the Header data class.
    """
    seq: int = DataField(default=0)
    timestamp: int = DataField(default=-1)
    node_id: Text = DataField(default='')
    properties: dict = DataField(default_factory=dict)

    def __post_init__(self):
        self.timestamp = int(time.time())


class RPCMessage:
    """RPCObject Class.
    RPC Object Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """
    @DataClass
    class Request(Object):
        header: HeaderObject = HeaderObject()

    @DataClass
    class Response(Object):
        header: HeaderObject = HeaderObject()


@DataClass
class PubSubMessage(Object):
    """PubSubObject Class.
    Implementation of the PubSubObject Base Data class.
    """
    header: HeaderObject = DataField(default=HeaderObject())


class ActionMessage(Object):
    @DataClass
    class Goal(Object):
        header: HeaderObject = HeaderObject()

    @DataClass
    class Result(Object):
        header: HeaderObject = HeaderObject()

    @DataClass
    class Feedback(Object):
        header: HeaderObject = HeaderObject()


@DataClass
class HeartbeatMessage(PubSubMessage):
    ts: int = -1
