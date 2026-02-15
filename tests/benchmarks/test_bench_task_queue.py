"""Benchmark tests for task queue endpoints using mock transport.

No external broker dependencies required.
"""
# pylint: disable=unused-argument

import time
import warnings

import pytest

from commlib.msg import TaskMessage
from commlib.task_queue import TaskQueueConfig, TaskStatus
from commlib.transports.mock import (
    ConnectionParameters,
    TaskProducer,
    TaskWorker,
    clear_mock_bus,
)


class BenchTaskMessage(TaskMessage):
    """Bench Task Message."""
    class Task(TaskMessage.Task):
        """Task."""
        payload: str = ""

    class Result(TaskMessage.Result):
        """Result payload."""
        ack: bool = False


@pytest.mark.unit
@pytest.mark.benchmark
class TestTaskQueueBenchmarks:
    """Test Task Queue Benchmarks."""
    def setup_method(self):
        """Setup method."""
        clear_mock_bus()

    def teardown_method(self):
        """Teardown method."""
        clear_mock_bus()

    @pytest.mark.smoke
    def test_task_queue_import(self):
        """Test task queue import."""
        from commlib.task_queue import BaseTaskProducer, BaseTaskWorker

        assert callable(BaseTaskProducer)
        assert callable(BaseTaskWorker)

    @pytest.mark.smoke
    def test_single_task_roundtrip(self):
        """Test single task roundtrip."""
        conn_params = ConnectionParameters()

        def on_task(ctx):
            return {"ack": True}

        worker = TaskWorker(
            queue_name="bench.single",
            on_task=on_task,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.single",
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        handle = producer.submit({"payload": "test"})
        result = handle.wait_result(timeout=5.0)
        elapsed = time.monotonic() - start

        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert elapsed < 2.0, f"Single task roundtrip too slow: {elapsed:.3f}s"

        producer.stop()
        worker.stop()

    @pytest.mark.smoke
    def test_batch_task_throughput(self):
        """Test batch task throughput."""
        conn_params = ConnectionParameters()
        num_tasks = 50
        completed = []

        def on_task(ctx):
            return {"ack": True}

        def on_result(task_id, result_data):
            completed.append(task_id)

        worker = TaskWorker(
            queue_name="bench.batch",
            on_task=on_task,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.batch",
            on_result=on_result,
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        handles = []
        for i in range(num_tasks):
            h = producer.submit({"payload": f"task-{i}"})
            handles.append(h)

        for h in handles:
            h.wait_result(timeout=10.0)

        elapsed = time.monotonic() - start
        throughput = num_tasks / elapsed if elapsed > 0 else 0

        assert len(completed) == num_tasks
        assert throughput > 5, f"Task throughput too low: {throughput:.1f} tasks/sec"

        if throughput < 20:
            warnings.warn(
                f"Task queue throughput below expected: {throughput:.1f} tasks/sec"
            )

        producer.stop()
        worker.stop()

    def test_typed_task_throughput(self):
        """Test typed task throughput."""
        conn_params = ConnectionParameters()
        num_tasks = 30
        completed = []

        def on_task(ctx):
            return BenchTaskMessage.Result(ack=True)

        def on_result(task_id, result_data):
            completed.append(task_id)

        worker = TaskWorker(
            queue_name="bench.typed",
            msg_type=BenchTaskMessage,
            on_task=on_task,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.typed",
            msg_type=BenchTaskMessage,
            on_result=on_result,
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        handles = []
        for i in range(num_tasks):
            task = BenchTaskMessage.Task(payload=f"typed-{i}")
            h = producer.submit(task)
            handles.append(h)

        for h in handles:
            h.wait_result(timeout=10.0)

        elapsed = time.monotonic() - start
        throughput = num_tasks / elapsed if elapsed > 0 else 0

        assert len(completed) == num_tasks
        assert throughput > 5, (
            f"Typed task throughput too low: {throughput:.1f} tasks/sec"
        )

        producer.stop()
        worker.stop()

    def test_fire_and_forget_throughput(self):
        """Test fire and forget throughput."""
        conn_params = ConnectionParameters()
        num_tasks = 100
        processed = []

        def on_task(ctx):
            processed.append(ctx.task_id)
            return None

        worker = TaskWorker(
            queue_name="bench.fandf",
            on_task=on_task,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.fandf",
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        for i in range(num_tasks):
            producer.submit({"payload": f"ff-{i}"}, fire_and_forget=True)

        timeout = 15.0
        deadline = time.monotonic() + timeout
        while len(processed) < num_tasks and time.monotonic() < deadline:
            time.sleep(0.05)

        elapsed = time.monotonic() - start
        throughput = len(processed) / elapsed if elapsed > 0 else 0

        assert len(processed) == num_tasks, (
            f"Only {len(processed)}/{num_tasks} fire-and-forget tasks processed"
        )
        assert throughput > 5, f"F&F throughput too low: {throughput:.1f} tasks/sec"

        producer.stop()
        worker.stop()

    @pytest.mark.smoke
    def test_progress_reporting_overhead(self):
        """Test progress reporting overhead."""
        conn_params = ConnectionParameters()
        progress_reports = []

        def on_task(ctx):
            for i in range(10):
                ctx.send_progress({"step": i}, percent=(i + 1) * 10.0)
            return {"done": True}

        def on_progress(task_id, progress_data, percent):
            progress_reports.append(percent)

        worker = TaskWorker(
            queue_name="bench.progress",
            on_task=on_task,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.progress",
            on_progress=on_progress,
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        handle = producer.submit({"work": True})
        result = handle.wait_result(timeout=5.0)
        elapsed = time.monotonic() - start

        time.sleep(0.2)

        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert len(progress_reports) == 10
        assert elapsed < 3.0, f"Progress-enabled task too slow: {elapsed:.3f}s"

        producer.stop()
        worker.stop()

    def test_concurrent_workers(self):
        """Test concurrent workers."""
        conn_params = ConnectionParameters()
        num_tasks = 20
        completed = []

        def on_task(ctx):
            time.sleep(0.01)
            return {"task_id": ctx.task_id}

        def on_result(task_id, result_data):
            completed.append(task_id)

        config = TaskQueueConfig(
            queue_name="bench.concurrent",
            max_concurrent=4,
        )

        worker = TaskWorker(
            queue_name="bench.concurrent",
            on_task=on_task,
            config=config,
            conn_params=conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="bench.concurrent",
            on_result=on_result,
            conn_params=conn_params,
        )
        producer.run()

        start = time.monotonic()
        handles = []
        for i in range(num_tasks):
            h = producer.submit({"idx": i})
            handles.append(h)

        for h in handles:
            h.wait_result(timeout=15.0)

        elapsed = time.monotonic() - start

        assert len(completed) == num_tasks

        if elapsed > 5.0:
            warnings.warn(
                f"Concurrent worker tasks slower than expected: {elapsed:.1f}s"
            )

        producer.stop()
        worker.stop()
