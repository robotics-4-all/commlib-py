#!/usr/bin/env python

"""Robot Fleet — Delivery Task Worker (Task Queue pattern).

Processes delivery tasks assigned to a robot.  Demonstrates task queue
workers with progress feedback and retry support.

Usage::

    python examples/robot_fleet/task_worker.py --broker redis
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
    class Task(TaskMessage.Task):
        order_id: str = ""
        pickup_location: str = ""
        delivery_location: str = ""
        payload_kg: float = 0.0

    class Result(TaskMessage.Result):
        order_id: str = ""
        delivered: bool = False
        time_taken_sec: float = 0.0

    class Progress(TaskMessage.Progress):
        order_id: str = ""
        stage: str = ""
        percent: float = 0.0


def on_delivery_task(ctx) -> DeliveryTask.Result:
    task = ctx.data
    oid = task.order_id
    start = time.time()
    print(f"[worker] Order {oid}: {task.pickup_location} -> {task.delivery_location}")

    stages = [
        ("navigating_to_pickup", 25.0),
        ("picking_up", 50.0),
        ("navigating_to_delivery", 75.0),
        ("delivering", 100.0),
    ]
    for stage, pct in stages:
        ctx.send_progress(
            DeliveryTask.Progress(order_id=oid, stage=stage, percent=pct),
            percent=pct,
        )
        print(f"  [{oid}] {stage} ({pct}%)")
        time.sleep(0.5)

    elapsed = round(time.time() - start, 2)
    print(f"[worker] Order {oid} delivered in {elapsed}s")
    return DeliveryTask.Result(
        order_id=oid,
        delivered=True,
        time_taken_sec=elapsed,
    )


if __name__ == "__main__":
    parser = make_broker_parser("Process robot delivery tasks")
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
        queue_name="fleet.robot_01.tasks",
        max_retries=3,
        max_concurrent=1,
    )

    worker = TaskWorker(
        queue_name="fleet.robot_01.tasks",
        msg_type=DeliveryTask,
        config=config,
        on_task=on_delivery_task,
        conn_params=conn_params,
    )
    worker.run()

    print("[worker] Waiting for delivery tasks...")
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
