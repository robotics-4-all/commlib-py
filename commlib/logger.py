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


class Logger:
    """Logger.
    Tiny wrapper around python's logging module
    """

    def __init__(self, namespace: str, debug: bool = False,
                 log_file: str = None):
        """__init__.

        Args:
            namespace (str): namespace
            debug (bool): debug
        """
        self.namespace = namespace
        self.std_logger = logging.getLogger(namespace)
        self.log_file = log_file
        self._debug_mode = debug
        self.set_debug(self._debug_mode)

        if self.log_file is not None:
            fh = logging.FileHandler(self.log_file)
            self.std_logger.addHandler(fh)

    def set_debug(self, status: bool):
        """set_debug.
        Set debug mode (Enable/Disable)

        Args:
            status (bool): status
        """
        if not isinstance(status, bool):
            raise TypeError('Value should be boolean')
        if status:
            self.std_logger.setLevel(logging.DEBUG)
        else:
            self.std_logger.setLevel(logging.INFO)
        self._debug_mode = status

    def debug(self, msg: str, exc_info: bool = False):
        """debug.
        Log debug messages.

        Args:
            msg (str): msg
            exc_info (bool): exc_info
        """
        self.std_logger.debug(msg, exc_info=exc_info)

    def info(self, msg: str, exc_info: bool = False):
        """info.
        Log info messages.

        Args:
            msg (str): msg
            exc_info (bool): exc_info
        """
        self.std_logger.info(msg, exc_info=exc_info)

    def warn(self, msg: str, exc_info: bool = False):
        """warn.
        Log warning messages.

        Args:
            msg (str): msg
            exc_info (bool): exc_info
        """
        self.std_logger.warning(msg, exc_info=exc_info)

    def warning(self, msg: str, exc_info: bool = False):
        """warning.
        Same as warn(...)

        Args:
            msg (str): msg
            exc_info (bool): exc_info
        """
        self.warn(msg, exc_info)

    def error(self, msg, exc_info=False):
        """error.
        Log error messages.

        Args:
            msg:
            exc_info:
        """
        self.std_logger.error(msg, exc_info=exc_info)


s_logger = None
