import re
import uuid
import time
import threading
import socket
import socketserver

from typing import (Any, Callable, Dict, List, Optional, Tuple, Type,
                    TypeVar, Union, Text)


def camelcase_to_snakecase(_str: str) -> str:
    """camelcase_to_snakecase.
    Transform a camelcase string to  snakecase

    Args:
        _str (str): String to apply transformation.

    Returns:
        str: Transformed string
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', _str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def gen_timestamp() -> int:
    """gen_timestamp.
    Generate a timestamp.

    Args:

    Returns:
        int: Timestamp in integer representation. User `str()` to
            transform to string.
    """
    return int(1.0 * (time.time() + 0.5) * 1000)


def gen_random_id() -> str:
    """gen_random_id.
    Generates a random unique id, using the uuid library.

    Args:

    Returns:
        str: String representation of the random unique id
    """
    return str(uuid.uuid4()).replace('-', '')


class Rate:
    def __init__(self, hz):
        self._hz = hz
        self._tsleep = 1.0 / hz

    def sleep(self):
        time.sleep(self._tsleep)


class TimerEvent:
    def __init__(self, last_expected, last_real,
                 current_expected, current_real,
                 last_duration):
        self.last_expected = last_expected
        self.last_real = last_real
        self.current_expected = current_expected
        self.current_real = current_real
        self.last_duration = last_duration


class Timer(threading.Timer):
    def __init__(self, period, callback, oneshot=False):
        """
        Constructor.
        @param period: desired period between callbacks in seconds
        @type period: double
        @param callback: callback to be called
        @type callback: function taking TimerEvent
        @param oneshot: if True, fire only once, otherwise fire continuously
            until shutdown is called [default: False]
        @type oneshot: bool
        """
        super(Timer, self).__init__()
        self._period = period
        self._callback = callback
        self._oneshot = oneshot
        self._shutdown = False
        self.setDaemon(True)

    def shutdown(self):
        """
        Stop firing callbacks.
        """
        self._shutdown = True

    def run(self):
        r = Rate(1.0 / self._period)
        current_expected = time.time() + self._period
        last_expected, last_real, last_duration = None, None, None
        while True:
            try:
                r.sleep()
            except KeyboardInterrupt as exc:
                print(exc)
                break
            if self._shutdown:
                break
            start = time.time()
            current_real = start
            self._callback(TimerEvent(last_expected, last_real,
                                      current_expected,
                                      current_real,
                                      last_duration))
            if self._oneshot:
                break
            last_duration = time.time() - start
            last_expected, last_real = current_expected, current_real
            current_expected += self._period


class TCPProxyRequestHandler(socketserver.BaseRequestHandler):
    """
    TCP Proxy Server
    Instantiated once time for each connection, and must
    override the handle() method for client communication.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024)
        print("Passing data from: {}".format(self.client_address[0]))
        print(self.data)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Try to connect to the server and send data
            try:
                sock.connect((self.server.host_ep2, self.server.port_ep2))
                sock.sendall(self.data)
                # Receive data from the server
                while 1:
                    received = sock.recv(1024)
                    if not received: break
                    # Send back received data
                    self.request.sendall(received)
            except Exception as exc:
              print(exc)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class TCPProxy(ThreadedTCPServer):
    def __init__(self, host_ep1: str, port_ep1: str,
                 host_ep2: str, port_ep2: str):
        self.host_ep1 = host_ep1
        self.host_ep2 = host_ep2
        self.port_ep1 = port_ep1
        self.port_ep2 = port_ep2
        super(TCPProxy, self).__init__((host_ep1, port_ep1), TCPProxyRequestHandler)
