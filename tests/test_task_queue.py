#!/usr/bin/env python

import time
import threading
import unittest

from commlib.endpoints import EndpointType
from commlib.exceptions import TaskQueueError, TaskTimeoutError, TaskWorkerError
from commlib.msg import TaskMessage
from commlib.node import Node
from commlib.task_queue import (
    AckPolicy,
    TaskEnvelope,
    TaskHandle,
    TaskQueueConfig,
    TaskResult,
    TaskStatus,
)
from commlib.transports.mock import (
    ConnectionParameters,
    TaskProducer,
    TaskWorker,
    clear_mock_bus,
)


class ComputeTaskMessage(TaskMessage):
    class Task(TaskMessage.Task):
        x: int = 0
        y: int = 0

    class Result(TaskMessage.Result):
        result: int = 0

    class Progress(TaskMessage.Progress):
        percent: float = 0.0


class TestTaskMessage(unittest.TestCase):
    def test_task_message_inner_classes(self):
        t = TaskMessage.Task()
        r = TaskMessage.Result()
        p = TaskMessage.Progress()
        self.assertIsInstance(t, TaskMessage.Task)
        self.assertIsInstance(r, TaskMessage.Result)
        self.assertIsInstance(p, TaskMessage.Progress)

    def test_custom_task_message(self):
        t = ComputeTaskMessage.Task(x=3, y=5)
        self.assertEqual(t.x, 3)
        self.assertEqual(t.y, 5)

    def test_custom_result_message(self):
        r = ComputeTaskMessage.Result(result=42)
        self.assertEqual(r.result, 42)

    def test_custom_progress_message(self):
        p = ComputeTaskMessage.Progress(percent=0.5)
        self.assertEqual(p.percent, 0.5)


class TestTaskStatus(unittest.TestCase):
    def test_status_values(self):
        self.assertEqual(TaskStatus.PENDING, 1)
        self.assertEqual(TaskStatus.PROCESSING, 2)
        self.assertEqual(TaskStatus.COMPLETED, 3)
        self.assertEqual(TaskStatus.FAILED, 4)
        self.assertEqual(TaskStatus.RETRYING, 5)
        self.assertEqual(TaskStatus.DEAD_LETTER, 6)


class TestAckPolicy(unittest.TestCase):
    def test_ack_policy_values(self):
        self.assertEqual(AckPolicy.AUTO, 1)
        self.assertEqual(AckPolicy.MANUAL, 2)


class TestTaskQueueConfig(unittest.TestCase):
    def test_default_config(self):
        config = TaskQueueConfig()
        self.assertEqual(config.queue_name, "default")
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.max_concurrent, 1)
        self.assertEqual(config.ack_policy, AckPolicy.AUTO)

    def test_custom_config(self):
        config = TaskQueueConfig(
            queue_name="my_queue",
            max_retries=5,
            retry_delay=2.0,
            task_ttl=60.0,
            dlq_name="my_queue.dead",
            max_concurrent=4,
        )
        self.assertEqual(config.queue_name, "my_queue")
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.dlq_name, "my_queue.dead")

    def test_default_dlq_name(self):
        config = TaskQueueConfig(queue_name="tasks")
        self.assertEqual(config.get_dlq_name(), "tasks.dlq")

    def test_custom_dlq_name(self):
        config = TaskQueueConfig(queue_name="tasks", dlq_name="dead_letters")
        self.assertEqual(config.get_dlq_name(), "dead_letters")


class TestTaskEnvelope(unittest.TestCase):
    def test_default_envelope(self):
        env = TaskEnvelope()
        self.assertIsNotNone(env.task_id)
        self.assertEqual(env.status, TaskStatus.PENDING)
        self.assertEqual(env.retry_count, 0)

    def test_envelope_with_data(self):
        env = TaskEnvelope(
            queue_name="compute",
            priority=5,
            task_data={"x": 1, "y": 2},
        )
        self.assertEqual(env.queue_name, "compute")
        self.assertEqual(env.priority, 5)
        self.assertEqual(env.task_data, {"x": 1, "y": 2})


class TestTaskHandle(unittest.TestCase):
    def test_initial_state(self):
        handle = TaskHandle("test-id")
        self.assertEqual(handle.task_id, "test-id")
        self.assertEqual(handle.status, TaskStatus.PENDING)
        self.assertFalse(handle.is_done)
        self.assertIsNone(handle.result)

    def test_set_result(self):
        handle = TaskHandle("test-id")
        result = TaskResult(task_id="test-id", status=TaskStatus.COMPLETED)
        handle.set_result(result)
        self.assertTrue(handle.is_done)
        self.assertEqual(handle.status, TaskStatus.COMPLETED)

    def test_wait_result_with_timeout(self):
        handle = TaskHandle("test-id")
        result = handle.wait_result(timeout=0.1)
        self.assertIsNone(result)

    def test_wait_result_resolves(self):
        handle = TaskHandle("test-id")
        expected = TaskResult(task_id="test-id", status=TaskStatus.COMPLETED)

        def setter():
            time.sleep(0.05)
            handle.set_result(expected)

        t = threading.Thread(target=setter)
        t.start()
        result = handle.wait_result(timeout=2.0)
        t.join()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.task_id, "test-id")


class TestEndpointTypeRegistration(unittest.TestCase):
    def test_task_producer_enum(self):
        self.assertEqual(EndpointType.TaskProducer.value, 9)

    def test_task_worker_enum(self):
        self.assertEqual(EndpointType.TaskWorker.value, 10)


class TestExceptions(unittest.TestCase):
    def test_task_queue_error_hierarchy(self):
        self.assertTrue(issubclass(TaskTimeoutError, TaskQueueError))
        self.assertTrue(issubclass(TaskWorkerError, TaskQueueError))

    def test_task_queue_error_message(self):
        err = TaskQueueError("test error")
        self.assertIn("test error", str(err))


class TestMockTaskProducerWorker(unittest.TestCase):
    def setUp(self):
        clear_mock_bus()
        self.conn_params = ConnectionParameters()

    def tearDown(self):
        clear_mock_bus()

    def test_producer_submit_and_worker_process(self):
        results = []

        def on_task(ctx):
            data = ctx.data
            return {"sum": data["x"] + data["y"]}

        def on_result(task_id, result_data):
            results.append((task_id, result_data))

        worker = TaskWorker(
            queue_name="compute",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="compute",
            on_result=on_result,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"x": 3, "y": 7})
        result = handle.wait_result(timeout=5.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["sum"], 10)

        time.sleep(0.1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1]["sum"], 10)

        producer.stop()
        worker.stop()

    def test_typed_task_message(self):
        results = []

        def on_task(ctx):
            data = ctx.data
            self.assertIsInstance(data, ComputeTaskMessage.Task)
            return ComputeTaskMessage.Result(result=data.x * data.y)

        def on_result(_task_id, result_data):
            results.append(result_data)

        worker = TaskWorker(
            queue_name="typed_compute",
            msg_type=ComputeTaskMessage,
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="typed_compute",
            msg_type=ComputeTaskMessage,
            on_result=on_result,
            conn_params=self.conn_params,
        )
        producer.run()

        task = ComputeTaskMessage.Task(x=4, y=5)
        handle = producer.submit(task)
        result = handle.wait_result(timeout=5.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["result"], 20)

        time.sleep(0.1)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ComputeTaskMessage.Result)
        self.assertEqual(results[0].result, 20)

        producer.stop()
        worker.stop()

    def test_fire_and_forget(self):
        processed = []

        def on_task(ctx):
            processed.append(ctx.task_id)
            return None

        worker = TaskWorker(
            queue_name="fire_forget",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="fire_forget",
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1}, fire_and_forget=True)
        time.sleep(0.5)

        self.assertEqual(len(processed), 1)
        self.assertEqual(handle.task_id, processed[0])

        producer.stop()
        worker.stop()

    def test_task_priority(self):
        producer = TaskProducer(
            queue_name="priority_test",
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1}, priority=5)
        self.assertIsNotNone(handle.task_id)

        producer.stop()

    def test_progress_reporting(self):
        progress_reports = []

        def on_task(ctx):
            ctx.send_progress({"step": 1}, percent=50.0)
            ctx.send_progress({"step": 2}, percent=100.0)
            return {"done": True}

        def on_progress(task_id, progress_data, percent):
            progress_reports.append((task_id, progress_data, percent))

        worker = TaskWorker(
            queue_name="progress_test",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="progress_test",
            on_progress=on_progress,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"work": True})
        handle.wait_result(timeout=5.0)

        time.sleep(0.2)
        self.assertEqual(len(progress_reports), 2)
        self.assertEqual(progress_reports[0][2], 50.0)
        self.assertEqual(progress_reports[1][2], 100.0)

        producer.stop()
        worker.stop()

    def test_task_failure_and_retry(self):
        attempts = []

        def on_task(ctx):
            attempts.append(ctx.retry_count)
            if ctx.retry_count < 2:
                raise ValueError("Simulated failure")
            return {"recovered": True}

        config = TaskQueueConfig(
            queue_name="retry_test",
            max_retries=3,
            retry_delay=0.1,
            retry_backoff_multiplier=1.0,
        )

        worker = TaskWorker(
            queue_name="retry_test",
            on_task=on_task,
            config=config,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="retry_test",
            config=config,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1})
        result = handle.wait_result(timeout=10.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["recovered"], True)
        self.assertEqual(len(attempts), 3)

        producer.stop()
        worker.stop()

    def test_task_exhausted_retries(self):
        def on_task(ctx):
            raise RuntimeError("Always fails")

        config = TaskQueueConfig(
            queue_name="exhaust_test",
            max_retries=2,
            retry_delay=0.05,
            retry_backoff_multiplier=1.0,
        )

        worker = TaskWorker(
            queue_name="exhaust_test",
            on_task=on_task,
            config=config,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="exhaust_test",
            config=config,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1})
        result = handle.wait_result(timeout=10.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("Always fails", result.error)

        producer.stop()
        worker.stop()

    def test_manual_ack(self):
        _acked = []

        def on_task(ctx):
            result = {"processed": True}
            ctx.ack()
            return result

        config = TaskQueueConfig(
            queue_name="manual_ack_test",
            ack_policy=AckPolicy.MANUAL,
        )

        worker = TaskWorker(
            queue_name="manual_ack_test",
            on_task=on_task,
            config=config,
            conn_params=self.conn_params,
        )
        worker.run()

        producer = TaskProducer(
            queue_name="manual_ack_test",
            config=config,
            conn_params=self.conn_params,
        )
        producer.run()

        handle = producer.submit({"data": 1})
        result = handle.wait_result(timeout=5.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)

        producer.stop()
        worker.stop()

    def test_worker_requires_on_task(self):
        with self.assertRaises(ValueError):
            TaskWorker(
                queue_name="no_callback",
                on_task=None,
                conn_params=self.conn_params,
            )

    def test_producer_stop_and_cleanup(self):
        producer = TaskProducer(
            queue_name="cleanup_test",
            conn_params=self.conn_params,
        )
        producer.run()
        self.assertTrue(producer.connected)
        producer.stop()
        self.assertFalse(producer.connected)

    def test_worker_stop_and_cleanup(self):
        def on_task(_ctx):
            return None

        worker = TaskWorker(
            queue_name="cleanup_test",
            on_task=on_task,
            conn_params=self.conn_params,
        )
        worker.run()
        self.assertTrue(worker.connected)
        worker.stop()
        self.assertFalse(worker.connected)


class TestNodeTaskQueueIntegration(unittest.TestCase):
    def setUp(self):
        clear_mock_bus()
        self.conn_params = ConnectionParameters()

    def tearDown(self):
        clear_mock_bus()

    def test_node_create_task_producer(self):
        node = Node(
            node_name="task_producer_node",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        producer = node.create_task_producer(queue_name="node_tasks")
        self.assertIsInstance(producer, TaskProducer)
        self.assertEqual(producer.queue_name, "node_tasks")

    def test_node_create_task_worker(self):
        def handler(_ctx):
            return None

        node = Node(
            node_name="task_worker_node",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        worker = node.create_task_worker(
            queue_name="node_tasks",
            on_task=handler,
        )
        self.assertIsInstance(worker, TaskWorker)
        self.assertEqual(worker.queue_name, "node_tasks")

    def test_node_endpoints_include_task_queue(self):
        def handler(_ctx):
            return None

        node = Node(
            node_name="endpoints_test_node",
            connection_params=self.conn_params,
            heartbeats=False,
        )
        producer = node.create_task_producer(queue_name="test_q")
        worker = node.create_task_worker(queue_name="test_q", on_task=handler)

        self.assertIn(producer, node.endpoints)
        self.assertIn(worker, node.endpoints)

    def test_node_full_task_queue_flow(self):
        results = []

        def on_task(ctx):
            data = ctx.data
            return {"doubled": data["value"] * 2}

        def on_result(_task_id, result_data):
            results.append(result_data)

        node = Node(
            node_name="full_flow_node",
            connection_params=self.conn_params,
            heartbeats=False,
        )

        _worker = node.create_task_worker(
            queue_name="full_flow",
            on_task=on_task,
        )

        producer = node.create_task_producer(
            queue_name="full_flow",
            on_result=on_result,
        )

        node.run()

        handle = producer.submit({"value": 21})
        result = handle.wait_result(timeout=5.0)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.result_data["doubled"], 42)

        time.sleep(0.1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["doubled"], 42)

        node.stop()


if __name__ == "__main__":
    unittest.main()
