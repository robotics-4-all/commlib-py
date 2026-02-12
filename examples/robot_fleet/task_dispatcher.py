#!/usr/bin/env python

"""Robot Fleet — Delivery Task Dispatcher (Task Queue pattern).

Dispatches delivery tasks to a robot worker and tracks progress/results.

Usage::

    python examples/robot_fleet/task_dispatcher.py --broker redis
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import TaskMessage  # noqa: E402
from commlib.task_queue import TaskQueueConfig  # noqa: E402


class DeliveryTask(TaskMessage):
    """Delivery Task."""
    class Task(TaskMessage.Task):
        """Task."""
        order_id: str = ""
        pickup_location: str = ""
        delivery_location: str = ""
        payload_kg: float = 0.0

    class Result(TaskMessage.Result):
        """Result payload."""
        order_id: str = ""
        delivered: bool = False
        time_taken_sec: float = 0.0

    class Progress(TaskMessage.Progress):
        """Progress."""
        order_id: str = ""
        stage: str = ""
        percent: float = 0.0


def on_result(_task_id: str, task_result: DeliveryTask.Result) -> None:
    status = "DELIVERED" if task_result.delivered else "FAILED"
    print(
        f"[dispatch] {task_result.order_id}: [{status}] {task_result.time_taken_sec}s"
    )


def on_progress(_task_id: str, progress: DeliveryTask.Progress, percent: float) -> None:
    print(f"[dispatch] {progress.order_id}: {progress.stage} ({percent}%)")


if __name__ == "__main__":
    parser = make_broker_parser("Dispatch robot delivery tasks")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    TaskProducer: type
    if args.broker == "redis":
        from commlib.transports.redis import TaskProducer
    elif args.broker == "amqp":
        from commlib.transports.amqp import TaskProducer
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import TaskProducer
    elif args.broker == "kafka":
        from commlib.transports.kafka import TaskProducer
    else:
        from commlib.transports.mock import TaskProducer

    config = TaskQueueConfig(
        queue_name="fleet.robot_01.tasks",
        max_retries=3,
    )

    producer = TaskProducer(
        queue_name="fleet.robot_01.tasks",
        msg_type=DeliveryTask,
        config=config,
        on_result=on_result,
        on_progress=on_progress,
        conn_params=conn_params,
    )
    producer.run()

    orders = [
        DeliveryTask.Task(
            order_id="ORD-101",
            pickup_location="warehouse_A",
            delivery_location="office_301",
            payload_kg=2.5,
        ),
        DeliveryTask.Task(
            order_id="ORD-102",
            pickup_location="warehouse_B",
            delivery_location="lab_105",
            payload_kg=0.8,
        ),
        DeliveryTask.Task(
            order_id="ORD-103",
            pickup_location="warehouse_A",
            delivery_location="reception",
            payload_kg=5.0,
        ),
    ]

    priorities = [1, 5, 10]
    handles = []

    for task, prio in zip(orders, priorities):
        print(f"[dispatch] Submitting {task.order_id} (priority={prio})")
        handle = producer.submit(task, priority=prio)
        handles.append(handle)
        time.sleep(0.2)

    print("[dispatch] Waiting for results...")
    for handle in handles:
        result = handle.wait_result(timeout=30)
        if result is not None:
            print(f"[dispatch] {handle.task_id}: done (status={result.status})")
        else:
            print(f"[dispatch] {handle.task_id}: TIMEOUT")

    producer.stop()
