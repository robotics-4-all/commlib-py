#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest

from commlib.msg import as_dict
from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from commlib.msg import MessageHeader, RPCMessage, PubSubMessage, Object
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
        while count < 3:
            time.sleep(1)
            count += 1
        assert self.count_0 == count

    def callback_0(self, event):
        self.count_0 += 1
