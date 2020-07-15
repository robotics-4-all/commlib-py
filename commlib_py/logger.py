# -*- coding: utf-8 -*-
# Copyright (C) 2020  Panayiotou, Konstantinos <klpanagi@gmail.com>
# Author: Panayiotou, Konstantinos <klpanagi@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import logging.config

from .endpoints import TransportType


class LoggingLevel(object):
    DEBUG = logging.DEBUG
    INFO = logging.INFO


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')

__LOGGING = dict(
    version=1,
    formatters={
        'f': {'format':
              '[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
              'datefmt': '%s'
              }
    },
    handlers={
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
    },
    root={
        'handlers': ['h'],
        'level': logging.DEBUG,
    },
)

logging.config.dictConfig(__LOGGING)

logging.addLevelName(
    logging.WARNING,
    '\033[1;33m%s\033[1;0m' % logging.getLevelName(logging.WARNING)
)

logging.addLevelName(
    logging.ERROR,
    '\033[1;31m%s\033[1;0m' % logging.getLevelName(logging.ERROR)
)

logging.addLevelName(
    logging.DEBUG,
    '\033[1;34m%s\033[1;0m' % logging.getLevelName(logging.DEBUG)
)


def create_logger(namespace):
    return logging.getLogger(namespace)


class Logger(object):
    """Tiny wrapper around python's logging module"""
    def __init__(self, namespace, debug=False):
        self.namespace = namespace
        self.std_logger = create_logger(namespace)
        self._debug_mode = debug
        self.set_debug(self._debug_mode)

    def set_debug(self, status):
        if not isinstance(status, bool):
            raise TypeError('Value should be boolean')
        if status:
            self.std_logger.setLevel(logging.DEBUG)
        else:
            self.std_logger.setLevel(logging.INFO)
        self._debug_mode = status

    def debug(self, msg, exc_info=False):
        self.std_logger.debug(msg, exc_info=exc_info)

    def info(self, msg, exc_info=False):
        self.std_logger.info(msg, exc_info=exc_info)

    def warn(self, msg, exc_info=False):
        self.std_logger.warning(msg, exc_info=exc_info)

    def warning(self, msg, exc_info=False):
        self.warn(msg, exc_info)

    def error(self, msg, exc_info=False):
        self.std_logger.error(msg, exc_info=exc_info)


class RemoteLogger(Logger):
    """Remote Logger Class."""
    def __init__(self, namespace, transport_type, conn_params):
        if transport_type == TransportType.REDIS:
            from commlib_py.transports.redis import Publisher
        else:
            from commlib_py.transports.amqp import Publisher
        super(RemoteLogger, self).__init__(namespace)
        self.conn_params = conn_params
        self.remote_topic = '{}.logs'.format(namespace)
        self.log_pub = Publisher(conn_params=conn_params,
                                 topic=self.remote_topic)
        self._remote_state = 1
        self._std_state = 1

        self._formatting = '[{timestamp}][{namespace}][{level}]'

    @property
    def remote(self):
        return self._remote_state

    @remote.setter
    def remote(self, val):
        assert isinstance(val, bool)
        if val:
            self._remote_state = 1
        else:
            self._remote_state = 0

    @property
    def std(self):
        return self._std_state

    @std.setter
    def std(self, val):
        assert isinstance(val, bool)
        if val:
            self._std_state = 1
        else:
            self._std_state = 0

    def format_msg(self, msg, level):
        fmsg = self._formatting.format(timestamp=-1,
                                       namespace=self.namespace,
                                       level=level)
        return {'msg': fmsg}

    def debug(self, msg, exc_info=False):
        if self._std_state:
            self.std_logger.debug(msg, exc_info=exc_info)
        if self._remote_state:
            self.log_pub.publish(self.format_msg(msg, 'DEBUG'))

    def info(self, msg, exc_info=False):
        if self._std_state:
            self.std_logger.info(msg, exc_info=exc_info)
        if self._remote_state:
            self.log_pub.publish(self.format_msg(msg, 'INFO'))

    def warn(self, msg, exc_info=False):
        if self._std_state:
            self.std_logger.warning(msg, exc_info=exc_info)
        if self._remote_state:
            self.log_pub.publish(self.format_msg(msg, 'WARNING'))

    def error(self, msg, exc_info=False):
        if self._std_state:
            self.std_logger.error(msg, exc_info=exc_info)
        if self._remote_state:
            self.log_pub.publish(self.format_msg(msg, 'ERROR'))
