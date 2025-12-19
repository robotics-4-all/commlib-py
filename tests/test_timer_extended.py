#!/usr/bin/env python

"""Extended tests for Timer class."""

import time
import unittest
from threading import Event

from commlib.timer import Timer, TimerEvent


class TestTimerEvent(unittest.TestCase):
    """Test TimerEvent class."""

    def test_timer_event_creation(self):
        """Test TimerEvent object creation."""
        event = TimerEvent(
            last_expected=1.0,
            last_real=1.1,
            current_expected=2.0,
            current_real=2.05,
            last_duration=0.5
        )
        self.assertEqual(event.last_expected, 1.0)
        self.assertEqual(event.last_real, 1.1)
        self.assertEqual(event.current_expected, 2.0)
        self.assertEqual(event.current_real, 2.05)
        self.assertEqual(event.last_duration, 0.5)

    def test_timer_event_with_none_values(self):
        """Test TimerEvent with None values."""
        event = TimerEvent(
            last_expected=None,
            last_real=None,
            current_expected=1.0,
            current_real=1.0,
            last_duration=None
        )
        self.assertIsNone(event.last_expected)
        self.assertIsNone(event.last_real)
        self.assertIsNone(event.last_duration)


class TestTimerBasic(unittest.TestCase):
    """Test Timer class basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.callback_count = 0
        self.timer_events = []

    def callback(self, event: TimerEvent):
        """Test callback function."""
        self.callback_count += 1
        self.timer_events.append(event)

    def test_timer_creation(self):
        """Test Timer object creation."""
        timer = Timer(1.0, self.callback)
        self.assertEqual(timer._period, 1.0)
        self.assertEqual(timer._callback, self.callback)
        self.assertFalse(timer._oneshot)
        self.assertFalse(timer._shutdown)
        self.assertTrue(timer.daemon)

    def test_timer_oneshot(self):
        """Test Timer with oneshot=True."""
        timer = Timer(0.1, self.callback, oneshot=True)
        self.assertTrue(timer._oneshot)
        timer.start()
        time.sleep(0.3)
        # Should only fire once
        self.assertEqual(self.callback_count, 1)

    def test_timer_multiple_callbacks(self):
        """Test Timer calls callback multiple times."""
        timer = Timer(0.1, self.callback)
        timer.start()
        time.sleep(0.35)
        timer.shutdown()
        # Should fire at least 3 times in 0.35 seconds with 0.1s period
        self.assertGreaterEqual(self.callback_count, 3)

    def test_timer_shutdown(self):
        """Test Timer shutdown."""
        timer = Timer(0.05, self.callback)
        timer.start()
        time.sleep(0.2)
        count_before_shutdown = self.callback_count
        timer.shutdown()
        time.sleep(0.1)
        count_after_shutdown = self.callback_count
        # Should not increase after shutdown
        self.assertEqual(count_before_shutdown, count_after_shutdown)

    def test_timer_event_first_call_has_none_values(self):
        """Test that first timer event has None for last_* values."""
        timer = Timer(0.1, self.callback, oneshot=True)
        timer.start()
        time.sleep(0.15)
        # First event should have None for last_* values
        first_event = self.timer_events[0]
        self.assertIsNone(first_event.last_expected)
        self.assertIsNone(first_event.last_real)
        self.assertIsNone(first_event.last_duration)

    def test_timer_event_contains_timing_info(self):
        """Test that timer event contains proper timing information."""
        timer = Timer(0.1, self.callback, oneshot=True)
        timer.start()
        time.sleep(0.15)
        event = self.timer_events[0]
        # current_expected and current_real should be set
        self.assertIsNotNone(event.current_expected)
        self.assertIsNotNone(event.current_real)

    def test_timer_period_accuracy(self):
        """Test that timer respects period."""
        period = 0.05
        timer = Timer(period, self.callback)
        timer.start()
        time.sleep(0.2)
        timer.shutdown()
        # With 0.05s period, should fire ~4 times in 0.2s
        self.assertGreaterEqual(self.callback_count, 3)
        self.assertLessEqual(self.callback_count, 6)

    def test_timer_daemon_flag(self):
        """Test that timer is daemon thread."""
        timer = Timer(1.0, self.callback)
        self.assertTrue(timer.daemon)

    def test_timer_thread_properties(self):
        """Test timer inherits from threading.Thread."""
        timer = Timer(1.0, self.callback)
        self.assertTrue(hasattr(timer, 'start'))
        self.assertTrue(hasattr(timer, 'run'))
        self.assertTrue(callable(timer.start))
        self.assertTrue(callable(timer.run))


if __name__ == '__main__':
    unittest.main()
