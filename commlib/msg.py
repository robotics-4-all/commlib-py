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
from typing import List

import redis

from .serializer import JSONSerializer
from .logger import create_logger


class BaseMessage(object):
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
                if isinstance(_prop, BaseMessage):
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
        return BaseMessage(*args, **kwargs)


class _CommMessageProperties(BaseMessage):
    __slots__ = ['content_type', 'content_encoding']

    def __init__(self, *args, **kwargs):
        super(_CommMessageProperties, self).__init__(*args, **kwargs)


class _TopicMessageHeader(BaseMessage):
    __slots__ = ['timestamp', 'properties', 'seq', 'node_id', 'type']

    def __init__(self, *args, **kwargs):
        self.type = 'PUBSUB'
        self.timestamp = -1
        self.seq = 0
        self.node_id = "-1"
        self.properties = _CommMessageProperties()
        super(_TopicMessageHeader, self).__init__(*args, **kwargs)


class _RPCMessageHeader(BaseMessage):
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


class _TopicMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _TopicMessageHeader() if header is None else header
        data = BaseMessage() if data is None else data
        assert isinstance(header, _TopicMessageHeader)
        assert isinstance(data, BaseMessage)
        super(_TopicMessage, self).__init__(header=header, data=data)


class _RPCRequestMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _RPCMessageHeader() if header is None else header
        data = BaseMessage() if data is None else data
        assert isinstance(header, _RPCMessageHeader)
        assert isinstance(data, BaseMessage)
        super(_RPCRequestMessage, self).__init__(header=header, data=data)


class _RPCResponseMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = _RPCMessageHeader() if header is None else header
        assert isinstance(header, _RPCMessageHeader)
        assert isinstance(data, BaseMessage)
        super(_RPCResponseMessage, self).__init__(header=header, data=data)


class _RPCMessage(BaseMessage):
    __slots__ = ['request', 'response']

    def __init__(self, request=None, response=None):
        request = _RPCRequestMessage() if request is None else request
        response = _RPCResponseMessage() if response is None else response
        assert isinstance(request, _RPCRequestMessage)
        assert isinstance(response, _RPCResponseMessage)
        super(_RPCMessage, self).__init__(request=request,
                                         response=response)
