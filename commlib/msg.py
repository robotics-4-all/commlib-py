import base64
from os import path
from typing import Any, Dict, List, Union
from uuid import UUID

from pydantic import BaseModel, Field

from commlib.utils import get_timestamp_ns
import json

Primitives = [str, int, float, bool, bytes]


class Message(BaseModel):
    """Message Class.
    Base class for all message types. Provides methods for serialization and deserialization.
    """
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create a Message instance from a JSON string.

        Args:
            json_str (str): JSON string representing the message.

        Returns:
            Message: An instance of the Message class.
        """
        data = json.loads(json_str)
        return cls(**data)

    def to_json(self) -> str:
        """Convert the Message instance to a JSON string.

        Returns:
            str: JSON string representing the message.
        """
        return json.dumps(self.model_dump())


class MessageHeader(Message):
    """MessageHeader Class.
    Implements the Header data class.
    """

    msg_id: Union[int, str, UUID] = -1
    node_id: Union[int, str, UUID] = ""
    agent: str = "commlib-py"
    timestamp: int = Field(default_factory=lambda: get_timestamp_ns())
    properties: Dict[str, Any] = {}


class RPCMessage(Message):
    """RPCMessage.
    RPC Object Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """

    class Request(Message):
        """Request.
        RPC Request Message
        """

        pass

    class Response(Message):
        """Response.
        RPC Response Message
        """

        pass


class PubSubMessage(Message):
    """PubSubObject Class.
    Implementation of the PubSubObject Base Data class.
    """

    pass


class ActionMessage(Message):
    """ActionMessage."""

    class Goal(Message):
        """Goal.
        Action Goal Message
        """

        pass

    class Result(Message):
        """Result.
        Action Result Message
        """

        pass

    class Feedback(Message):
        """Feedback.
        Action Feedback Message
        """

        pass


class HeartbeatMessage(PubSubMessage):
    """HeartbeatMessage
    A PubSubMessage that contains a timestamp.

    The `ts` attribute is an integer representing the timestamp of the heartbeat message.
    """

    ts: int = get_timestamp_ns()


class FileObject(BaseModel):
    """FileObject Class.
    Represents a file object with its raw data, filename, and encoding.

    The `data` attribute contains the raw bytes of the file, encoded in the specified encoding.
    The `filename` attribute contains the name of the file.
    The `encoding` attribute specifies the encoding used for the `data` attribute, defaulting to "base64".

    The `load_from_file` method reads the raw bytes from the specified file path and stores them in the `data` attribute, encoding them in the specified encoding.
    """

    data: List[bytes] = []
    filename: str = ""
    encoding: str = "base64"

    def load_from_file(self, filepath):
        """Load raw bytes from file.
        Args:
            filepath (str): System Path of the file.
        """
        with open(filepath, "rb") as f:
            fdata = f.read()
            b64 = base64.b64encode(fdata)
            self.data = b64.decode()
            self.filename = path.basename(filepath)


class Event(PubSubMessage):
    """Event
    A PubSubMessage that contains a header and a payload.

    The `header` attribute is a `MessageHeader` object that contains metadata about the event.
    The `payload` attribute is a dictionary that contains the event data.
    """

    header: MessageHeader = MessageHeader()
    payload: Dict[str, Any] = dict()
