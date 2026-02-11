#!/usr/bin/env python

"""Smart Building — Firmware Update Service (Action pattern).

Simulates an OTA firmware update for building IoT devices with staged
progress feedback.  Pair with ``firmware_update_client.py``.

Usage::

    python examples/smart_building/firmware_update_service.py --broker redis
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import ActionMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class FirmwareUpdateAction(ActionMessage):
    class Goal(ActionMessage.Goal):
        device_id: str = ""
        firmware_version: str = ""
        firmware_size_mb: float = 0.0

    class Result(ActionMessage.Result):
        success: bool = False
        device_id: str = ""
        new_version: str = ""
        duration_sec: float = 0.0

    class Feedback(ActionMessage.Feedback):
        device_id: str = ""
        stage: str = ""
        percent: float = 0.0


STAGES = [
    ("downloading", 0.0, 40.0, 5),
    ("verifying", 40.0, 60.0, 3),
    ("installing", 60.0, 95.0, 5),
    ("rebooting", 95.0, 100.0, 2),
]


def on_firmware_goal(goal_h) -> FirmwareUpdateAction.Result:
    goal = goal_h.data
    device = goal.device_id
    version = goal.firmware_version
    start = time.time()

    print(f"[firmware] Starting update: {device} -> v{version}")

    for stage_name, pct_start, pct_end, steps in STAGES:
        for i in range(steps):
            if goal_h.cancel_event.is_set():
                print(f"[firmware] Update cancelled for {device}")
                return FirmwareUpdateAction.Result(
                    success=False,
                    device_id=device,
                    new_version=version,
                    duration_sec=time.time() - start,
                )
            pct = pct_start + (pct_end - pct_start) * (i + 1) / steps
            goal_h.send_feedback(
                FirmwareUpdateAction.Feedback(
                    device_id=device,
                    stage=stage_name,
                    percent=round(pct, 1),
                )
            )
            time.sleep(0.3)

    duration = round(time.time() - start, 2)
    print(f"[firmware] Update complete: {device} v{version} ({duration}s)")
    return FirmwareUpdateAction.Result(
        success=True,
        device_id=device,
        new_version=version,
        duration_sec=duration,
    )


if __name__ == "__main__":
    parser = make_broker_parser("OTA firmware update service")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.devices.firmware_service",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_action(
        msg_type=FirmwareUpdateAction,
        action_name="building.devices.firmware_update",
        on_goal=on_firmware_goal,
    )

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
