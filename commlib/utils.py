import re
import uuid
import time
import threading


def camelcase_to_snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def gen_random_id():
    """Generate correlationID."""
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
