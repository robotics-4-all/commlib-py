from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

import datetime
import time
import uuid
import json
import hashlib

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


class CommMessageProperties(BaseMessage):
    __slots__ = ['content_type', 'content_encoding']

    def __init__(self, *args, **kwargs):
        super(CommMessageProperties, self).__init__(*args, **kwargs)


class CommHeaderMessagePubSub(BaseMessage):
    __slots__ = ['timestamp', 'properties', 'seq', 'node_id', 'type']

    def __init__(self, *args, **kwargs):
        self.type = 'PUBSUB'
        self.timestamp = -1
        self.seq = 0
        self.node_id = "-1"
        self.properties = CommMessageProperties()
        super(CommHeaderMessagePubSub, self).__init__(*args, **kwargs)


class CommHeaderMessageRPC(BaseMessage):
    __slots__ = ['timestamp', 'properties', 'seq',
                 'node_id', 'type', 'reply_to']

    def __init__(self, *args, **kwargs):
        self.type = 'RPC'
        self.timestamp = datetime.datetime.now(
            datetime.timezone.utc).timestamp()
        self.seq = 0
        self.node_id = "-1"
        self.reply_to = ''
        self.properties = CommMessageProperties()
        super(CommHeaderMessageRPC, self).__init__(*args, **kwargs)


class PubSubMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = CommHeaderMessagePubSub() if header is None else header
        data = BaseMessage() if data is None else data
        assert isinstance(header, CommHeaderMessagePubSub)
        assert isinstance(data, BaseMessage)
        super(PubSubMessage, self).__init__(header=header, data=data)


class RPCRequestMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = CommHeaderMessagePubSub() if header is None else header
        data = BaseMessage() if data is None else data
        assert isinstance(header, CommHeaderMessageRPC)
        assert isinstance(data, BaseMessage)
        super(RPCRequestMessage, self).__init__(header=header, data=data)


class RPCResponseMessage(BaseMessage):
    __slots__ = ['header', 'data']

    def __init__(self, header=None, data=None):
        header = CommHeaderMessageRPC() if header is None else header
        assert isinstance(header, CommHeaderMessageRPC)
        assert isinstance(data, BaseMessage)
        super(RPCResponseMessage, self).__init__(header=header, data=data)


class RPCMessage(BaseMessage):
    __slots__ = ['request', 'response']

    def __init__(self, request=None, response=None):
        request = RPCRequestMessage() if request is None else request
        response = RPCResponseMessage() if response is None else response
        assert isinstance(request, RPCRequestMessage)
        assert isinstance(response, RPCResponseMessage)
        super(RPCMessage, self).__init__(request=request,
                                         response=response)
