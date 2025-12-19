"""Message serialization and deserialization.

Provides JSON and custom serialization backends for encoding and decoding
message content and metadata.
"""

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

import enum
from decimal import Decimal
from typing import Any, Dict

DEFAULT_JSON_SERIALIZER = "ujson"


if DEFAULT_JSON_SERIALIZER == "json":
    import json as json
elif DEFAULT_JSON_SERIALIZER == "ujson":
    import ujson as json
elif DEFAULT_JSON_SERIALIZER == "orjson":
    import orjson as json


class SerializationTypes(enum.IntEnum):
    JSON = 0


class ContentType:
    """Content Types."""

    json: str = "application/json"
    raw_bytes: str = "application/octet-stream"
    text: str = "plain/text"


class Serializer:
    """Serializer Base Class."""

    CONTENT_TYPE: str = "None"
    CONTENT_ENCODING: str = "None"

    @staticmethod
    def serialize(data: Any) -> str:
        """serialize.

        Args:
            data (dict): Serialize a dict
        """
        raise NotImplementedError()

    @staticmethod
    def deserialize(data: str) -> Any:
        """deserialize.

        Args:
            data (str): -
        """
        raise NotImplementedError()


class JSONSerializer(Serializer):
    """Thin wrapper to implement json serializer.

    Static class.
    """

    CONTENT_TYPE: str = ContentType.json
    CONTENT_ENCODING: str = "utf8"

    @staticmethod
    def serialize(data: Dict[str, Any]) -> str:
        """serialize.

        Args:
            data (dict): Serialize to json string
        """
        return str(json.dumps(JSONSerializer.make_primitives(data)))

    @staticmethod
    def deserialize(data: str) -> Dict[str, Any]:
        """deserialize.

        Args:
            data (str): json str to dict
        """
        return json.loads(data)

    @staticmethod
    def make_primitive_value(val: Any):
        """
        Converts a value to a primitive type that can be serialized to JSON.

        Args:
            val (Any): The value to convert.

        Returns:
            Any: The converted value.
        """

        if isinstance(val, dict):
            return JSONSerializer.make_primitives(val)
        elif isinstance(val, list) or isinstance(val, tuple):
            return list([JSONSerializer.make_primitive_value(v) for v in val])
        elif isinstance(val, Decimal) or isinstance(val, float):
            return float(val)
        elif isinstance(val, int) and str(val).isdigit():
            return int(val)
        elif isinstance(val, bool):
            return bool(val)
        elif val is None:
            return None
        else:
            return str(val)

    @staticmethod
    def make_primitives(data: Dict[str, Any]):
        """
        Converts a dictionary to only contain primitive types that can be serialized to JSON.

        Args:
            data (Dict[str, Any]): The dictionary to convert.

        Returns:
            Dict[str, Any]: The dictionary with all values converted to primitive types.
        """

        for key, val in data.items():
            data[key] = JSONSerializer.make_primitive_value(val)
        return data


class BinarySerializer(Serializer):
    """Serializer for raw byte streams.

    Static class.
    """

    CONTENT_TYPE: str = ContentType.raw_bytes
    CONTENT_ENCODING: str = "binary"

    @staticmethod
    def serialize(data: Dict[str, Any]) -> bytes:
        """Serialize a dictionary to a raw byte stream.

        Args:
            data (Dict[str, Any]): The dictionary to serialize.

        Returns:
            bytes: The serialized byte stream.
        """
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary.")
        json_data = JSONSerializer.serialize(data)
        return json_data.encode("utf-8")

    @staticmethod
    def deserialize(data: bytes) -> Dict[str, Any]:
        """Deserialize a raw byte stream to a dictionary.

        Args:
            data (bytes): The byte stream to deserialize.

        Returns:
            Dict[str, Any]: The deserialized dictionary.
        """
        if not isinstance(data, bytes):
            raise ValueError("Input data must be bytes.")
        json_data = data.decode("utf-8")
        return JSONSerializer.deserialize(json_data)


class TextSerializer(Serializer):
    """Serializer for plain text data.

    Static class.
    """

    CONTENT_TYPE: str = ContentType.text
    CONTENT_ENCODING: str = "utf8"

    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to plain text.

        Args:
            data (Any): The data to serialize.

        Returns:
            str: The serialized plain text.
        """
        if not isinstance(data, (str, int, float, bool, list)):
            raise ValueError(
                "Input data must be a primitive type (str, int, float, bool) or a list."
            )
        if isinstance(data, list):
            return ",".join(map(str, data))
        return str(data)

    @staticmethod
    def deserialize(data: str) -> Any:
        """Deserialize plain text to its original form.

        Args:
            data (str): The plain text to deserialize.

        Returns:
            Any: The deserialized data.
        """
        if "," in data:
            return data.split(",")
        return data
