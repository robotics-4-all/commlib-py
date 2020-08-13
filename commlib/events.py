import time
import datetime

from .serializer import JSONSerializer
from .logger import Logger
from.utils import gen_random_id


class Event(object):
    """Implementation of the Event object.
    Args:
        name (str): The name of the event.
        payload (dict): Dictionary payload of the event.
        headers (dict): Event headers to set.
    """

    __slots__ = ['name', 'uri', 'payload', 'header']

    def __init__(self, name, uri, payload={}, headers={}):
        self.name = name
        self.uri = uri
        self.payload = payload
        _header = {
            'timestamp': -1,
            'seq': -1,
            'agent': 'commlib-py',
            # 'semantics': [],
            # 'desctiption:',
            'custom': {}
        }
        _header['custom'].update(headers)
        self.header = _header

    def to_dict(self):
        """Serialize message object to a dict."""
        _d = {}
        for k in self.__slots__:
            # Recursive object seriazilation to dictionary
            if not k.startswith('_'):
                _prop = getattr(self, k)
                _d[k] = _prop
        return _d

    def _inc_seq(self):
        self.header['seq'] += 1

    def _set_timestamp(self, ts=None):
        """Set timestamp header"""
        if ts is None:
            self.header['timestamp'] = (1.0 * (time.time() + 0.5) * 1000)
        else:  # TODO: Check if is integer
            self.header['timestamp'] = ts


class BaseEventEmitter(object):
    def __init__(self, name=None, logger=None, debug=False, serializer=None):
        if name is None:
            name = gen_random_id()
        self._name = name
        self._debug = debug
        if serializer is not None:
            self._serializer = serializer
        else:
            self._serializer = JSONSerializer

        self._logger = Logger(self.__class__.__name__, debug=debug) if \
            logger is None else logger
        self.logger.debug('Created Event Emitter <{}>'.format(self._name))

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def send_event(self, event):
        raise NotImplementedError()
