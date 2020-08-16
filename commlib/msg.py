import datetime
import time
import uuid
import json
import hashlib

from dataclasses import dataclass as MessageClass
from dataclasses import field as MessageField
from dataclasses import is_dataclass as is_msgclass
from dataclasses import make_dataclass as make_msgclass
from dataclasses import asdict as as_dict
from dataclasses import astuple as as_tuple
from typing import List, Dict, Tuple, Sequence

import redis

from .serializer import JSONSerializer


@MessageClass
class Message:
    """Message Class.
    Base Message Class. Implements base methods to inherit.
    """
    def __iter__(self):
        yield from as_tuple(self)

    def as_dict(self):
        return as_dict(self)

    def from_dict(self, data_dict):
        """Fill message data fields from dict key-value pairs."""
        for key, val in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, val)
            else:
                raise AttributeError(
                    f'{self.__class__.__name__} has no attribute {key}')


@MessageClass
class HeaderMessage(Message):
    """HeaderMessage Class.
    Implements the Header data class.
    """
    seq: int = MessageField(default=0)
    timestamp: int = MessageField(default=-1)
    node_id: str = MessageField(default='')
    properties: dict = MessageField(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == -1:
            self.time = datetime.datetime.now(
                datetime.timezone.utc).timestamp()


class RPCMessage:
    """RPCMessage Class.
    RPC Message Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """
    @MessageClass
    class Request(Message):
        header: HeaderMessage = HeaderMessage()

    @MessageClass
    class Response(Message):
        header: HeaderMessage = HeaderMessage()


@MessageClass
class PubSubMessage(Message):
    """PubSubMessage Class.
    Implementation of the PubSubMessage Base Data class.
    """
    header: HeaderMessage = MessageField(default=HeaderMessage())


class _BaseMessage(object):
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
                if isinstance(_prop, _BaseMessage):
                    _d[k] = _prop._to_dict()
                else:
                    _d[k] = _prop
        return _d

    def _from_dict(self, data_dict):
        """Fill message data fields from dict key-value pairs."""
        for key, val in data_dict.items():
            setattr(self, key, val)

    def to_dict(self):
        """Serialize Message to dictionary."""
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
        return _BaseMessage(*args, **kwargs)


class _CommMessageProperties(_BaseMessage):
    __slots__ = ['content_type', 'content_encoding']

    def __init__(self, *args, **kwargs):
        super(_CommMessageProperties, self).__init__(*args, **kwargs)


class _TopicMessageHeader(_BaseMessage):
    __slots__ = ['timestamp', 'properties', 'seq', 'node_id', 'type']

    def __init__(self, *args, **kwargs):
        self.type = 'PUBSUB'
        self.timestamp = -1
        self.seq = 0
        self.node_id = "-1"
        self.properties = _CommMessageProperties()
        super(_TopicMessageHeader, self).__init__(*args, **kwargs)


class _RPCMessageHeader(_BaseMessage):
    __slots__ = ['timestamp', 'properties', 'seq',
                 'node_id', 'type', 'reply_to']

    def __init__(self, *args, **kwargs):
        self.type = 'RPC'
        self.timestamp = datetime.datetime.now(
            datetime.timezone.utc).timestamp()
        self.seq = 0
        self.node_id = "-1"
        self.reply_to = ''
        self.properties = _CommMessageProperties()
        super(_RPCMessageHeader, self).__init__(*args, **kwargs)


class _TopicMessage(_BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _TopicMessageHeader() if header is None else header
        data = _BaseMessage() if data is None else data
        assert isinstance(header, _TopicMessageHeader)
        assert isinstance(data, _BaseMessage)
        super(_TopicMessage, self).__init__(header=header, data=data)


class _RPCRequestMessage(_BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _RPCMessageHeader() if header is None else header
        data = _BaseMessage() if data is None else data
        assert isinstance(header, _RPCMessageHeader)
        assert isinstance(data, _BaseMessage)
        super(_RPCRequestMessage, self).__init__(header=header, data=data)


class _RPCResponseMessage(_BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _RPCMessageHeader() if header is None else header
        assert isinstance(header, _RPCMessageHeader)
        assert isinstance(data, _BaseMessage)
        super(_RPCResponseMessage, self).__init__(header=header, data=data)


class _RPCMessage(_BaseMessage):
    __slots__ = ['request', 'response']

    def __init__(self, request=None, response=None):
        request = _RPCRequestMessage() if request is None else request
        response = _RPCResponseMessage() if response is None else response
        assert isinstance(request, _RPCRequestMessage)
        assert isinstance(response, _RPCResponseMessage)
        super(_RPCMessage, self).__init__(request=request,
                                         response=response)
