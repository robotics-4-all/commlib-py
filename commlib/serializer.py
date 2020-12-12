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

from typing import Text
import json


class ContentType:
    """Content Types."""
    json: Text = 'application/json'
    raw_bytes: Text = 'application/octet-stream'
    text: Text = 'plain/text'


class Serializer:
    """Serializer Abstract Class."""
    CONTENT_TYPE: Text = 'None'
    CONTENT_ENCODING: Text = 'None'

    @staticmethod
    def serialize(data: dict):
        """serialize.

        Args:
            data (dict): Serialize a dict
        """
        raise NotImplementedError()

    @staticmethod
    def deserialize(data: Text):
        """deserialize.

        Args:
            data (Text): -
        """
        raise NotImplementedError()


class JSONSerializer(Serializer):
    """Thin wrapper to implement json serializer.

    Static class.
    """
    CONTENT_TYPE: Text = 'application/json'
    CONTENT_ENCODING: Text = 'utf8'

    @staticmethod
    def serialize(data: dict):
        """serialize.

        Args:
            data (dict): Serialize to json string
        """
        if not isinstance(data, dict):
            raise TypeError('Data are not of type Dict.')
        return json.dumps(data)

    @staticmethod
    def deserialize(data: str):
        """deserialize.

        Args:
            data (str): json str to dict
        """
        return json.loads(data)
