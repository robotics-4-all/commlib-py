#!/usr/bin/env python

"""Robot Fleet — Custom Robot Node (Node inheritance pattern).

Demonstrates extending the ``Node`` class to create a reusable
``RobotNode`` that auto-publishes telemetry at a configurable rate.

Usage::

    python examples/robot_fleet/robot_node.py --broker redis
"""

import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import PubSubMessage  # noqa: E402
from commlib.node import Node  # noqa: E402
from commlib.utils import Rate  # noqa: E402


class RobotTelemetry(PubSubMessage):
    robot_id: str = ""
    battery_pct: float = 100.0
    x: float = 0.0
    y: float = 0.0
    velocity: float = 0.0
    status: str = "idle"


class RobotNode(Node):
    def __init__(self, robot_id: str, pub_freq: float = 5.0, **kwargs):
        self.robot_id = robot_id
        self.pub_freq = pub_freq
        self._telemetry_topic = f"fleet.{robot_id}.telemetry"
        kwargs.pop("node_name", None)
        super().__init__(
            node_name=f"fleet.{robot_id}",
            **kwargs,
        )
        self._telem_pub = self.create_publisher(
            msg_type=RobotTelemetry,
            topic=self._telemetry_topic,
        )

    def start_telemetry(self, timeout: float = 0) -> None:
        self.run()
        rate = Rate(self.pub_freq)
        x, y = 0.0, 0.0
        battery = 100.0
        heading = random.uniform(0, 2 * math.pi)
        start = time.time()

        try:
            while True:
                if timeout and time.time() - start > timeout:
                    break
                speed = random.uniform(0.3, 1.5)
                x += speed * math.cos(heading) * (1.0 / self.pub_freq)
                y += speed * math.sin(heading) * (1.0 / self.pub_freq)
                heading += random.uniform(-0.1, 0.1)
                battery = max(0, battery - 0.01)

                msg = RobotTelemetry(
                    robot_id=self.robot_id,
                    battery_pct=round(battery, 2),
                    x=round(x, 3),
                    y=round(y, 3),
                    velocity=round(speed, 3),
                    status="moving" if speed > 0.5 else "idle",
                )
                self._telem_pub.publish(msg)
                print(
                    f"[{self.robot_id}] pos=({msg.x}, {msg.y}) bat={msg.battery_pct}%"
                )
                rate.sleep()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


if __name__ == "__main__":
    parser = make_broker_parser("Run a robot node with telemetry")
    parser.add_argument(
        "--robot-id",
        type=str,
        default="robot_01",
        help="Robot identifier",
    )
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    robot = RobotNode(
        robot_id=args.robot_id,
        pub_freq=2.0,
        connection_params=conn_params,
        heartbeats=False,
    )
    robot.start_telemetry(timeout=args.timeout)
