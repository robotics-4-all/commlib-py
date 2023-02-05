class ConnectionError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class AMQPError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class MQTTError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RedisError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RPCClientError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RPCServiceError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RPCRequestError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RPCClientTimeoutError(RPCClientError):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class RPCServerError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class PublisherError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class SubscriberError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class NodeError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors


class SerializationError(Exception):
    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors

