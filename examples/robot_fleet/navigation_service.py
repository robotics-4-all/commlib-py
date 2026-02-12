#!/usr/bin/env python

"""Robot Fleet — Navigation Service (Action pattern).

Simulates robot navigation to a target waypoint with continuous position
feedback.  Pair with ``navigation_client.py``.

Usage::

    python examples/robot_fleet/navigation_service.py --broker redis
"""

import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import ActionMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class NavigateAction(ActionMessage):
    class Goal(ActionMessage.Goal):
        x: float = 0.0
        y: float = 0.0
        max_speed: float = 1.0

    class Result(ActionMessage.Result):
        reached: bool = False
        final_x: float = 0.0
        final_y: float = 0.0
        distance_traveled: float = 0.0

    class Feedback(ActionMessage.Feedback):
        current_x: float = 0.0
        current_y: float = 0.0
        distance_remaining: float = 0.0
        eta_seconds: float = 0.0


def on_navigate_goal(goal_h) -> NavigateAction.Result:
    goal = goal_h.data
    target_x, target_y = goal.x, goal.y
    speed = goal.max_speed
    cur_x, cur_y = 0.0, 0.0
    total_dist = 0.0
    dt = 0.3

    print(f"[nav] Navigating to ({target_x}, {target_y}) at {speed} m/s")

    while True:
        if goal_h.cancel_event.is_set():
            print("[nav] Navigation cancelled")
            return NavigateAction.Result(
                reached=False,
                final_x=cur_x,
                final_y=cur_y,
                distance_traveled=round(total_dist, 3),
            )

        dx = target_x - cur_x
        dy = target_y - cur_y
        remaining = math.sqrt(dx * dx + dy * dy)

        if remaining < 0.1:
            break

        step = min(speed * dt, remaining)
        ratio = step / remaining
        cur_x += dx * ratio
        cur_y += dy * ratio
        total_dist += step

        eta = remaining / speed if speed > 0 else 0
        goal_h.send_feedback(
            NavigateAction.Feedback(
                current_x=round(cur_x, 3),
                current_y=round(cur_y, 3),
                distance_remaining=round(remaining, 3),
                eta_seconds=round(eta, 1),
            )
        )
        time.sleep(dt)

    print(f"[nav] Reached ({target_x}, {target_y})")
    return NavigateAction.Result(
        reached=True,
        final_x=round(cur_x, 3),
        final_y=round(cur_y, 3),
        distance_traveled=round(total_dist, 3),
    )


if __name__ == "__main__":
    parser = make_broker_parser("Robot navigation action service")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="fleet.robot_01.navigation",
        connection_params=conn_params,
        heartbeats=False,
    )
    node.create_action(
        msg_type=NavigateAction,
        action_name="fleet.robot_01.navigate",
        on_goal=on_navigate_goal,
    )

    if args.timeout:
        import threading

        threading.Timer(args.timeout, node.stop).start()
    node.run_forever()
