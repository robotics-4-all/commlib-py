import time
import abc

from typing import (Any, Callable, Dict, List, Optional, Tuple, Type,
                    TypeVar, Union, Text)

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from dataclasses import fields as DataFields
from dataclasses import is_dataclass
from dataclasses import make_dataclass
from dataclasses import asdict as as_dict
from dataclasses import astuple as as_tuple


Primitives = [str, int, float, bool, bytes]


@DataClass
class Object(abc.ABC):
    """Object Class.
    Base Object Class. Implements base methods to inherit.
    """
    def __iter__(self) -> Tuple[str, Any]:
        yield from as_tuple(self)

    def as_dict(self) -> Dict[str, Any]:
        """as_dict.

        Args:

        Returns:
            dict:
        """
        return as_dict(self)

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """from_dict.
        Fill message data fields from dict key-value pairs.

        Args:
            data_dict (dict): data_dict

        Returns:
            None:
        """
        fieldtypes = {f.name:f.type for f in DataFields(self.__class__)}
        for key, val in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, object_from_dict(fieldtypes[key], val))
            else:
                raise AttributeError(
                    f'{self.__class__.__name__} has no attribute {key}')


@DataClass
class MessageHeader(Object):
    """MessageHeader Class.
    Implements the Header data class.
    """
    seq: int = DataField(default=0)
    timestamp: int = DataField(default=-1)
    node_id: Text = DataField(default='')
    agent: Text = DataField(default='commlib-py')

    def __post_init__(self):
        self.timestamp = int(time.time())


class RPCMessage(abc.ABC):
    """RPCObject Class.
    RPC Object Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """

    @DataClass
    class Request(Object):
        """Request.
        RPC Request Message
        """

    @DataClass
    class Response(Object):
        """Response.
        RPC Response Message
        """


@DataClass
class PubSubMessage(Object):
    """PubSubObject Class.
    Implementation of the PubSubObject Base Data class.
    """


class ActionMessage(Object):
    """ActionMessage.
    """

    @DataClass
    class Goal(Object):
        """Goal.
        Action Goal Message
        """

    @DataClass
    class Result(Object):
        """Result.
        Action Result Message
        """

    @DataClass
    class Feedback(Object):
        """Feedback.
        Action Feedback Message
        """


@DataClass
class HeartbeatMessage(PubSubMessage):
    """HeartbeatMessage.
    """

    ts: int = -1


def object_from_dict(klass: Object, dikt: Dict[str, Any]):
    try:
        fieldtypes = {f.name:f.type for f in DataFields(klass)}
        return klass(**{f:object_from_dict(fieldtypes[f],dikt[f]) for f in dikt})
    except:
        # Not an object (dataclass) field
        return dikt

