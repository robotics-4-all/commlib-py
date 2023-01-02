import abc
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union
from uuid import UUID
from commlib.utils import gen_timestamp

import base64
from os import path

from pydantic import BaseModel

Primitives = [str, int, float, bool, bytes]


class Message(BaseModel):
    pass


class MessageHeader(BaseModel):
    """MessageHeader Class.
    Implements the Header data class.
    """
    msg_id: Union[int, str, UUID] = -1
    node_id: Union[int, str, UUID] = ''
    agent: str = 'commlib-py'
    timestamp: int = gen_timestamp()
    properties: Dict[str, Any] = {}


class RPCMessage(BaseModel):
    """RPCMessage.
    RPC Object Class. Defines Request and Response data classes for
        instantiation. Used as a namespace.
    """

    class Request(BaseModel):
        """Request.
        RPC Request Message
        """
        pass

    class Response(BaseModel):
        """Response.
        RPC Response Message
        """
        pass


class PubSubMessage(BaseModel):
    """PubSubObject Class.
    Implementation of the PubSubObject Base Data class.
    """
    pass


class ActionMessage(BaseModel):
    """ActionMessage.
    """

    class Goal(BaseModel):
        """Goal.
        Action Goal Message
        """
        pass

    class Result(BaseModel):
        """Result.
        Action Result Message
        """
        pass

    class Feedback(BaseModel):
        """Feedback.
        Action Feedback Message
        """
        pass


class HeartbeatMessage(PubSubMessage):
    """HeartbeatMessage.
    """

    ts: int = gen_timestamp()


class FileObject(BaseModel):
    """Implementation of the File object."""

    data: List[bytes] = []
    filename: str = ''
    encoding: str = 'base64'

    def load_from_file(self, filepath):
        """Load raw bytes from file.
        Args:
            filepath (str): System Path of the file.
        """
        with open(filepath, 'rb') as f:
            fdata = f.read()
            b64 = base64.b64encode(fdata)
            self.data = b64.decode()
            self.filename = path.basename(filepath)
