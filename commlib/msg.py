import datetime
import time
import uuid
import json
import hashlib

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from dataclasses import is_dataclass as is_msgclass
from dataclasses import make_dataclass as make_msgclass
from dataclasses import asdict as as_dict
from dataclasses import astuple as as_tuple
from typing import List, Dict, Tuple, Sequence

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

    def from_dict(self, data_dict) -> None:
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
    node_id: str = DataField(default='')
    properties: dict = DataField(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == -1:
            self.time = datetime.datetime.now(
                datetime.timezone.utc).timestamp()


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


class _BaseObject(object):
    __slots__ = []

    def __init__(self, *args, **kwargs):
        self._set_props(*args, **kwargs)

    def _set_props(self, *args, **kwargs):
        """Constructor."""
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError(
                    '{}{}{}'.format(
                        self.__class__.__name__,
                        ' object does not have a property named ',
                        str(key)
                    )
                )

    def _to_dict(self):
        """Serialize message object to a dict."""
        _d = {}
        for k in self.__slots__:
            # Recursive object seriazilation to dictionary
            if not k.startswith('_'):
                _prop = getattr(self, k)
                if isinstance(_prop, _BaseObject):
                    _d[k] = _prop._to_dict()
                else:
                    _d[k] = _prop
        return _d

    def _from_dict(self, data_dict):
        """Fill message data fields from dict key-value pairs."""
        for key, val in data_dict.items():
            setattr(self, key, val)

    def to_dict(self):
        """Serialize Object to dictionary."""
        return self._to_dict()

    def __hash__(self):
        return hashlib.sha1(
            json.dumps(self.to_dict(), sort_keys=True)).hexdigest()

    def __eq__(self, other):
        """! Equality method """
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return json.dumps(self.to_dict(), sort_keys=True)

    def __call__(self, *args, **kwargs):
        return _BaseObject(*args, **kwargs)


class _CommObjectProperties(_BaseObject):
    __slots__ = ['content_type', 'content_encoding']

    def __init__(self, *args, **kwargs):
        super(_CommObjectProperties, self).__init__(*args, **kwargs)
