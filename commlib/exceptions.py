"""
Defines a set of custom exceptions used throughout the commlib module.

The `BaseException` class provides a common base for all custom exceptions, with
support for storing additional error information.

The other exception classes inherit from `BaseException` and provide more
specific error types, such as `ConnectionError`, `AMQPError`, `MQTTError`, etc.
These exceptions can be raised by various components of the commlib module to
indicate specific error conditions.
"""


class BaseException(Exception):  # pylint: disable=redefined-builtin
    """Raised for base errors."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


class ConnectionError(BaseException):  # pylint: disable=redefined-builtin
    """Raised for connection errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class AMQPError(BaseException):
    """Raised for AMQP errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class MQTTError(BaseException):
    """Raised for MQTT errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RedisError(BaseException):
    """Raised for redis errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RPCClientError(Exception):
    """Raised for RPC client errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RPCServiceError(Exception):
    """Raised for RPC service errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RPCRequestError(Exception):
    """Raised for RPC request errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RPCClientTimeoutError(RPCClientError):
    """Raised for RPC client timeout errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class RPCServerError(Exception):
    """Raised for RPC server errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class PublisherError(Exception):
    """Raised for publisher errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class SubscriberError(Exception):
    """Raised for subscriber errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class NodeError(Exception):
    """Raised for node errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class SerializationError(Exception):
    """Raised for serialization errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class TaskQueueError(BaseException):
    """Raised for task queue errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class TaskTimeoutError(TaskQueueError):
    """Raised for task timeout errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)


class TaskWorkerError(TaskQueueError):
    """Raised for task worker errors."""

    def __init__(self, message, errors=None):
        super().__init__(message, errors)
