#!/usr/bin/env python

"""Tests for commlib utils module."""

import unittest
import time

from commlib.utils import (
    camelcase_to_snakecase,
    gen_timestamp,
    get_timestamp_ns,
    gen_random_id,
    Rate,
)


class TestCamelCaseToSnakeCase(unittest.TestCase):
    """Test camelcase_to_snakecase function."""

    def test_simple_camelcase(self):
        """Test simple camelcase conversion."""
        result = camelcase_to_snakecase("helloWorld")
        self.assertEqual(result, "hello_world")

    def test_multiple_words(self):
        """Test multiple words conversion."""
        result = camelcase_to_snakecase("myVariableName")
        self.assertEqual(result, "my_variable_name")

    def test_already_snakecase(self):
        """Test string already in snakecase."""
        result = camelcase_to_snakecase("my_variable")
        self.assertEqual(result, "my_variable")

    def test_single_word(self):
        """Test single word string."""
        result = camelcase_to_snakecase("hello")
        self.assertEqual(result, "hello")

    def test_consecutive_capitals(self):
        """Test consecutive capital letters."""
        result = camelcase_to_snakecase("HTTPServer")
        self.assertEqual(result, "http_server")

    def test_with_numbers(self):
        """Test conversion with numbers."""
        result = camelcase_to_snakecase("version2Name")
        self.assertEqual(result, "version2_name")

    def test_empty_string(self):
        """Test empty string."""
        result = camelcase_to_snakecase("")
        self.assertEqual(result, "")


class TestTimestamps(unittest.TestCase):
    """Test timestamp generation functions."""

    def test_gen_timestamp(self):
        """Test gen_timestamp returns nanoseconds."""
        ts1 = gen_timestamp()
        ts2 = gen_timestamp()
        self.assertGreater(ts2, ts1)
        self.assertIsInstance(ts1, int)

    def test_get_timestamp_ns(self):
        """Test get_timestamp_ns returns nanoseconds."""
        ts = get_timestamp_ns()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)

    def test_timestamps_ordering(self):
        """Test that timestamps increase over time."""
        ts_ns1 = get_timestamp_ns()
        time.sleep(0.001)  # Sleep 1ms
        ts_ns2 = get_timestamp_ns()
        self.assertGreater(ts_ns2, ts_ns1)


class TestGenRandomId(unittest.TestCase):
    """Test random ID generation function."""

    def test_gen_random_id(self):
        """Test gen_random_id returns a string."""
        random_id = gen_random_id()
        self.assertIsInstance(random_id, str)

    def test_gen_random_id_uniqueness(self):
        """Test that gen_random_id generates unique IDs."""
        ids = {gen_random_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_gen_random_id_format(self):
        """Test gen_random_id format (should be uuid without dashes)."""
        random_id = gen_random_id()
        self.assertEqual(len(random_id), 32)  # UUID without dashes
        self.assertNotIn("-", random_id)

    def test_gen_random_id_hex_chars(self):
        """Test that gen_random_id contains only hex characters."""
        random_id = gen_random_id()
        for char in random_id:
            self.assertIn(char, "0123456789abcdef")


class TestRate(unittest.TestCase):
    """Test Rate class."""

    def test_rate_creation(self):
        """Test Rate object creation."""
        rate = Rate(10)  # 10 Hz
        self.assertEqual(rate._hz, 10)
        self.assertAlmostEqual(rate._tsleep, 0.1, places=5)

    def test_rate_high_frequency(self):
        """Test Rate with high frequency."""
        rate = Rate(1000)  # 1000 Hz
        self.assertAlmostEqual(rate._tsleep, 0.001, places=6)

    def test_rate_low_frequency(self):
        """Test Rate with low frequency."""
        rate = Rate(1)  # 1 Hz
        self.assertAlmostEqual(rate._tsleep, 1.0, places=5)

    def test_rate_sleep_timing(self):
        """Test that Rate.sleep() respects timing."""
        rate = Rate(10)  # 10 Hz = 0.1s per iteration
        start = time.time()
        rate.sleep()
        elapsed = time.time() - start
        # Allow 20% tolerance for timing
        self.assertGreaterEqual(elapsed, 0.08)
        self.assertLess(elapsed, 0.15)

    def test_rate_multiple_sleeps(self):
        """Test multiple consecutive sleeps."""
        rate = Rate(5)  # 5 Hz = 0.2s per iteration
        start = time.time()
        for _ in range(3):
            rate.sleep()
        elapsed = time.time() - start
        expected = 0.6  # 3 * 0.2s
        # Allow 20% tolerance
        self.assertGreaterEqual(elapsed, expected * 0.8)
        self.assertLess(elapsed, expected * 1.2)


if __name__ == '__main__':
    unittest.main()
