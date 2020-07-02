from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

"""Top-level package for commlib-py."""

__author__ = """Konstantinos Panayiotou"""
__email__ = 'klpanagi@gmail.com'
__version__ = '0.1.0'

from .amqp_transport import ConnectionParameters as AMQPConnectionParams
from .amqp_rpc import AMQPRPCServer as AMQPRPCServer
