#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest

from commlib.timer import Timer


class TestTimer(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.count_0 = 0

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_timer(self):
        """Test Timer class"""
        tmr = Timer(1, self.callback_0)
        tmr.start()
        count = 0
        max_iterations = 3
        while count < max_iterations:
            time.sleep(1.5)
            count += 1
        self.assertEqual(self.count_0, max_iterations + 1)

    def callback_0(self, _event):
        self.count_0 += 1
