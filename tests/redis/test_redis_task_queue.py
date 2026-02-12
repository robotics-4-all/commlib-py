#!/usr/bin/env python

"""Integration tests for Redis task queue endpoints.

Requires a running Redis broker. Set COMMLIB_REDIS_HOST and
COMMLIB_REDIS_PORT environment variables if not localhost:6379.
"""

import os
import time
import unittest

import pytest

from commlib.msg import TaskMessage
from commlib.node import Node
from commlib.task_queue import TaskQueueConfig, TaskStatus
from commlib.transports.redis import ConnectionParameters, TaskProducer, TaskWorker


class ComputeTaskMessage(TaskMessage):
    """Compute Task Message."""
    class Task(TaskMessage.Task):
        """Task."""
        x: int = 0
        y: int = 0

    class Result(TaskMessage.Result):
        """Result payload."""
        result: int = 0

    class Progress(TaskMessage.Progress):
        """Progress."""
        percent: float = 0.0


@pytest.mark.redis
@pytest.mark.integration
class TestRedisTaskQueue(unittest.TestCase):
    """Integration tests for Redis TaskProducer and TaskWorker."""

    def setUp(self):
        redis_host = os.getenv("COMMLIB_REDIS_HOST", "localhost")
        redis_port = int(os.getenv("COMMLIB_REDIS_PORT", "6379"))
        self.conn_params = ConnectionParameters(
            host=redis_host,
            port=redis_port,
            db=0,
            username="",
            password="",
            socket_timeout=None,
        )

    def test_submit_and_process_task(self):
        """Test basic task submission and processing via Redis."""
        results = []

        def on_task(ctx):
            data = ctx.data
            return {"sum": data["x"] + data["y"]}

        def on_result(task_id, result_data):
            results.append((task_id, result_data))

        worker = TaskWorker(
            queue_name="redis.test.compute",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="redis.test.compute",
            on_result=on_result,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"x": 10, "y": 20})
        result = handle.wait_result(timeout=10.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["sum"], 30)

        time.sleep(0.5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1]["sum"], 30)

        producer.stop()
        worker.stop()

    def test_typed_task_message(self):
        """Test task submission with typed TaskMessage."""
        results = []

        def on_task(ctx):
            data = ctx.data
            self.assertIsInstance(data, ComputeTaskMessage.Task)
            return ComputeTaskMessage.Result(result=data.x * data.y)

        def on_result(_task_id, result_data):
            results.append(result_data)

        worker = TaskWorker(
            queue_name="redis.test.typed",
            msg_type=ComputeTaskMessage,
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="redis.test.typed",
            msg_type=ComputeTaskMessage,
            on_result=on_result,
            conn_params=self.conn_params,
        )
        producer.run()

        task = ComputeTaskMessage.Task(x=6, y=7)
        handle = producer.submit(task)
        result = handle.wait_result(timeout=10.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["result"], 42)

        time.sleep(0.5)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ComputeTaskMessage.Result)
        self.assertEqual(results[0].result, 42)

        producer.stop()
        worker.stop()

    def test_fire_and_forget(self):
        """Test fire-and-forget task submission."""
        processed = []

        def on_task(ctx):
            processed.append(ctx.task_id)
            return None

        worker = TaskWorker(
            queue_name="redis.test.fandf",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="redis.test.fandf",
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1}, fire_and_forget=True)
        time.sleep(2.0)

        self.assertEqual(len(processed), 1)
        self.assertEqual(handle.task_id, processed[0])

        producer.stop()
        worker.stop()

    def test_progress_reporting(self):
        """Test progress reporting through Redis pub/sub."""
        progress_reports = []

        def on_task(ctx):
            ctx.send_progress({"step": 1}, percent=50.0)
            ctx.send_progress({"step": 2}, percent=100.0)
            return {"done": True}

        def on_progress(task_id, progress_data, percent):
            progress_reports.append((task_id, progress_data, percent))

        worker = TaskWorker(
            queue_name="redis.test.progress",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="redis.test.progress",
            on_progress=on_progress,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"work": True})
        handle.wait_result(timeout=10.0)

        time.sleep(1.0)
        self.assertEqual(len(progress_reports), 2)
        self.assertEqual(progress_reports[0][2], 50.0)
        self.assertEqual(progress_reports[1][2], 100.0)

        producer.stop()
        worker.stop()

    def test_task_failure_and_retry(self):
        """Test task retry on failure."""
        attempts = []

        def on_task(ctx):
            attempts.append(ctx.retry_count)
            if ctx.retry_count < 2:
                raise ValueError("Simulated failure")
            return {"recovered": True}

        config = TaskQueueConfig(
            queue_name="redis.test.retry",
            max_retries=3,
            retry_delay=0.2,
            retry_backoff_multiplier=1.0,
        )

        worker = TaskWorker(
            queue_name="redis.test.retry",
            on_task=on_task,
            config=config,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="redis.test.retry",
            config=config,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1})
        result = handle.wait_result(timeout=15.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["recovered"], True)
        self.assertEqual(len(attempts), 3)

        producer.stop()
        worker.stop()

    def test_node_task_queue_flow(self):
        """Test task queue via Node API with Redis transport."""
        results = []

        def on_task(ctx):
            data = ctx.data
            return {"doubled": data["value"] * 2}

        def on_result(_task_id, result_data):
            results.append(result_data)

        node = Node(
            node_name="redis_task_node",
            connection_params=self.conn_params,
            heartbeats=False,
        )

        _worker = node.create_task_worker(
            queue_name="redis.test.node_flow",
            on_task=on_task,
        )

        producer = node.create_task_producer(
            queue_name="redis.test.node_flow",
            on_result=on_result,
        )

        node.run()

        handle = producer.submit({"value": 21})
        result = handle.wait_result(timeout=10.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["doubled"], 42)

        time.sleep(0.5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["doubled"], 42)

        node.stop()


if __name__ == "__main__":
    unittest.main()
