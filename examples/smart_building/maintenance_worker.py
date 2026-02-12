#!/usr/bin/env python

"""Smart Building — Maintenance Task Worker (Task Queue pattern).

Processes building maintenance work orders dispatched by
``maintenance_dispatcher.py``.  Demonstrates competing consumers,
progress reporting, and retry semantics.

Usage::

    python examples/smart_building/maintenance_worker.py --broker redis
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
    class Task(TaskMessage.Task):
        work_order_id: str = ""
        task_type: str = ""
        floor: int = 0
        description: str = ""
        priority_level: str = "normal"

    class Result(TaskMessage.Result):
        work_order_id: str = ""
        completed: bool = False
        notes: str = ""

    class Progress(TaskMessage.Progress):
        work_order_id: str = ""
        stage: str = ""
        percent: float = 0.0


def on_task(ctx) -> MaintenanceTask.Result:
    task_data = ctx.data
    wo_id = task_data.work_order_id
    print(f"[worker] Starting: {wo_id} ({task_data.task_type})")

    stages = ["inspecting", "preparing", "executing", "verifying"]
    for i, stage in enumerate(stages):
        ctx.send_progress(
            MaintenanceTask.Progress(
                work_order_id=wo_id,
                stage=stage,
                percent=round((i + 1) / len(stages) * 100, 1),
            ),
            percent=round((i + 1) / len(stages) * 100, 1),
        )
        print(f"  [{wo_id}] {stage} ({(i + 1) * 25}%)")
        time.sleep(0.5)

    print(f"[worker] Completed: {wo_id}")
    return MaintenanceTask.Result(
        work_order_id=wo_id,
        completed=True,
        notes=f"{task_data.task_type} on floor {task_data.floor} done",
    )


if __name__ == "__main__":
    parser = make_broker_parser("Process building maintenance tasks")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    TaskWorker: type
    if args.broker == "redis":
        from commlib.transports.redis import TaskWorker
    elif args.broker == "amqp":
        from commlib.transports.amqp import TaskWorker
    elif args.broker == "mqtt":
        from commlib.transports.mqtt import TaskWorker
    elif args.broker == "kafka":
        from commlib.transports.kafka import TaskWorker
    else:
        from commlib.transports.mock import TaskWorker

    config = TaskQueueConfig(
        queue_name="building.maintenance.jobs",
        max_retries=2,
        max_concurrent=2,
        progress_enabled=True,
    )

    worker = TaskWorker(
        queue_name="building.maintenance.jobs",
        msg_type=MaintenanceTask,
        config=config,
        on_task=on_task,
        conn_params=conn_params,
    )
    worker.run()

    print("[worker] Listening for maintenance tasks...")
    try:
        if args.timeout:
            time.sleep(args.timeout)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
