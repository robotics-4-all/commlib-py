#!/usr/bin/env python

"""Smart Building — Maintenance Task Dispatcher (Task Queue pattern).

Dispatches building maintenance work orders to be processed by
``maintenance_worker.py``.  Demonstrates task submission with priorities,
progress callbacks, and result collection.

Usage::

    python examples/smart_building/maintenance_dispatcher.py --broker redis
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import TaskMessage  # noqa: E402
from commlib.task_queue import TaskQueueConfig  # noqa: E402


class MaintenanceTask(TaskMessage):
    """Maintenance Task."""
    class Task(TaskMessage.Task):
        """Task."""
        work_order_id: str = ""
        task_type: str = ""
        floor: int = 0
        description: str = ""
        priority_level: str = "normal"

    class Result(TaskMessage.Result):
        """Result payload."""
        work_order_id: str = ""
        completed: bool = False
        notes: str = ""

    class Progress(TaskMessage.Progress):
        """Progress."""
        work_order_id: str = ""
        stage: str = ""
        percent: float = 0.0


def on_result(task_id: str, task_result: MaintenanceTask.Result) -> None:
    """On result."""
    task_status = "DONE" if task_result.completed else "FAILED"
    print(f"[dispatch] Result {task_id}: [{task_status}] {task_result.notes}")


def on_progress(
    task_id: str, progress: MaintenanceTask.Progress, percent: float
) -> None:
    """On progress."""
    print(f"[dispatch] Progress {task_id}: {progress.stage} ({percent}%)")


if __name__ == "__main__":
    parser = make_broker_parser("Dispatch building maintenance tasks")
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
        queue_name="building.maintenance.jobs",
        max_retries=2,
        progress_enabled=True,
    )

    producer = TaskProducer(
        queue_name="building.maintenance.jobs",
        msg_type=MaintenanceTask,
        config=config,
        on_result=on_result,
        on_progress=on_progress,
        conn_params=conn_params,
    )
    producer.run()

    work_orders = [
        MaintenanceTask.Task(
            work_order_id="WO-001",
            task_type="hvac_filter_replacement",
            floor=3,
            description="Replace HVAC filters in zones A-C",
            priority_level="high",
        ),
        MaintenanceTask.Task(
            work_order_id="WO-002",
            task_type="lighting_inspection",
            floor=1,
            description="Inspect emergency lighting circuits",
            priority_level="normal",
        ),
        MaintenanceTask.Task(
            work_order_id="WO-003",
            task_type="elevator_maintenance",
            floor=0,
            description="Quarterly elevator safety check",
            priority_level="urgent",
        ),
    ]

    priorities = {"urgent": 10, "high": 5, "normal": 1}
    handles = []

    for task in work_orders:
        prio = priorities.get(task.priority_level, 1)
        print(f"[dispatch] Submitting {task.work_order_id} (priority={prio})")
        handle = producer.submit(task, priority=prio)
        handles.append(handle)
        time.sleep(0.2)

    print("[dispatch] Waiting for results...")
    for handle in handles:
        result = handle.wait_result(timeout=30)
        if result is not None:
            status = "COMPLETED" if result.status == 3 else "FAILED"
            print(f"[dispatch] {handle.task_id}: {status}")
        else:
            print(f"[dispatch] {handle.task_id}: TIMEOUT")

    producer.stop()
