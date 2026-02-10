#!/usr/bin/env python

"""Smart Building — Firmware Update Client (Action pattern).

Requests a firmware update and monitors progress via feedback callbacks.

Usage::

    python examples/smart_building/firmware_update_client.py --broker redis
"""

import os
import sys

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


def on_feedback(feedback: FirmwareUpdateAction.Feedback) -> None:
    print(f"  [{feedback.stage}] {feedback.percent}%  (device: {feedback.device_id})")


def on_result(result: FirmwareUpdateAction.Result) -> None:
    status = "SUCCESS" if result.success else "FAILED"
    print(f"  -> [{status}] v{result.new_version} in {result.duration_sec}s")


def on_goal_reached(result: FirmwareUpdateAction.Result) -> None:
    print(f"[client] Firmware update finished for {result.device_id}")


if __name__ == "__main__":
    parser = make_broker_parser("Request a firmware update")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="building.devices.firmware_client",
        connection_params=conn_params,
        heartbeats=False,
    )
    action_client = node.create_action_client(
        msg_type=FirmwareUpdateAction,
        action_name="building.devices.firmware_update",
        on_goal_reached=on_goal_reached,
        on_feedback=on_feedback,
        on_result=on_result,
    )
    node.run()

    goal = FirmwareUpdateAction.Goal(
        device_id="sensor-node-42",
        firmware_version="2.1.0",
        firmware_size_mb=12.5,
    )
    print(f"[client] Requesting update: {goal.device_id} -> v{goal.firmware_version}")
    action_client.send_goal(goal)
    resp = action_client.get_result(wait=True)
    print(f"[client] Final result: {resp}")
    node.stop()
