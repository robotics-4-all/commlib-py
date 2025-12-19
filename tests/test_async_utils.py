#!/usr/bin/env python

"""Tests for async utilities."""

import unittest
import asyncio
import time

from commlib.async_utils import (
    safe_wrapper,
    safe_ensure_future,
    safe_gather,
    wait_til,
    run_command,
    call_sync,
)


class TestAsyncUtils(unittest.TestCase):
    """Test async utility functions."""

    def test_safe_wrapper_success(self):
        """Test safe_wrapper with successful coroutine."""
        async def test_coro():
            return "success"

        result = asyncio.run(safe_wrapper(test_coro()))
        self.assertEqual(result, "success")

    def test_safe_wrapper_exception(self):
        """Test safe_wrapper with exception."""
        async def test_coro():
            raise ValueError("test error")

        async def run_test():
            try:
                result = await safe_wrapper(test_coro())
                return False  # Should not reach here
            except ValueError:
                return True  # Expected

        result = asyncio.run(run_test())
        self.assertTrue(result)

    def test_safe_wrapper_cancelled(self):
        """Test safe_wrapper with cancelled task."""
        async def test_coro():
            await asyncio.sleep(10)

        async def run_test():
            task = asyncio.create_task(safe_wrapper(test_coro()))
            await asyncio.sleep(0.01)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                return True
            return False

        result = asyncio.run(run_test())
        self.assertTrue(result)

    def test_safe_ensure_future(self):
        """Test safe_ensure_future."""
        async def test_coro():
            return "test"

        async def run_test():
            task = safe_ensure_future(test_coro())
            result = await task
            return result

        result = asyncio.run(run_test())
        self.assertEqual(result, "test")

    def test_safe_gather_multiple(self):
        """Test safe_gather with multiple coroutines."""
        async def test_gather():
            async def coro1():
                return 1

            async def coro2():
                return 2

            result = await safe_gather(coro1(), coro2())
            return result

        result = asyncio.run(test_gather())
        self.assertEqual(result, [1, 2])

    def test_safe_gather_exception(self):
        """Test safe_gather with exception."""
        async def test_gather():
            async def coro_ok():
                return "ok"

            async def coro_fail():
                raise ValueError("fail")

            try:
                await safe_gather(coro_ok(), coro_fail())
            except ValueError:
                return True
            return False

        result = asyncio.run(test_gather())
        self.assertTrue(result)

    def test_wait_til_success(self):
        """Test wait_til with condition met."""
        async def test_wait():
            counter = 0

            def condition():
                nonlocal counter
                counter += 1
                return counter >= 3

            try:
                await wait_til(condition, timeout=5)
                return True
            except Exception:
                return False

        result = asyncio.run(test_wait())
        self.assertTrue(result)

    def test_wait_til_timeout(self):
        """Test wait_til with timeout."""
        async def test_wait():
            def condition():
                return False  # Always false

            try:
                await wait_til(condition, timeout=0.1)
                return False
            except Exception:
                return True  # Expected to timeout

        result = asyncio.run(test_wait())
        self.assertTrue(result)

    def test_run_command(self):
        """Test run_command."""
        async def test_exec():
            result = await run_command("echo", "hello")
            return result

        result = asyncio.run(test_exec())
        self.assertEqual(result, "hello")

    def test_call_sync(self):
        """Test call_sync."""
        async def test_coro():
            await asyncio.sleep(0.01)
            return "done"

        loop = asyncio.new_event_loop()
        try:
            result = call_sync(test_coro(), loop, timeout=5.0)
            self.assertEqual(result, "done")
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
