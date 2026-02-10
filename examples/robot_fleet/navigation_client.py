#!/usr/bin/env python

"""Robot Fleet — Navigation Client (Action pattern).

Sends a navigation goal and monitors feedback until the robot reaches
the target waypoint.

Usage::

    python examples/robot_fleet/navigation_client.py --broker redis
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
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


def on_feedback(feedback: NavigateAction.Feedback) -> None:
    print(
        f"  pos=({feedback.current_x}, {feedback.current_y}) "
        f"remaining={feedback.distance_remaining}m "
        f"ETA={feedback.eta_seconds}s"
    )


def on_result(result: NavigateAction.Result) -> None:
    status = "REACHED" if result.reached else "ABORTED"
    print(
        f"  -> [{status}] final=({result.final_x}, {result.final_y}) "
        f"traveled={result.distance_traveled}m"
    )


def on_goal_reached(result: NavigateAction.Result) -> None:
    print("[client] Navigation complete")


if __name__ == "__main__":
    parser = make_broker_parser("Send a navigation goal")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="fleet.robot_01.nav_client",
        connection_params=conn_params,
        heartbeats=False,
    )
    action_client = node.create_action_client(
        msg_type=NavigateAction,
        action_name="fleet.robot_01.navigate",
        on_goal_reached=on_goal_reached,
        on_feedback=on_feedback,
        on_result=on_result,
    )
    node.run()

    goal = NavigateAction.Goal(x=10.0, y=5.0, max_speed=2.0)
    print(f"[client] Navigate to ({goal.x}, {goal.y}) at {goal.max_speed} m/s")
    action_client.send_goal(goal)
    resp = action_client.get_result(wait=True)
    print(f"[client] Result: {resp}")
    node.stop()
