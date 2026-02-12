#!/usr/bin/env python

"""Robot Fleet — Multi-Sensor Publisher (MPublisher + WPublisher pattern).

A robot publishes lidar, camera, and IMU data over a shared connection
using ``MPublisher`` and ``WPublisher`` to minimise broker connections.

Usage::

    python examples/robot_fleet/multi_sensor_publisher.py --broker redis
"""

import os
import random
import sys
import time

from pydantic import Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# pylint: disable=wrong-import-position
from _helpers import get_connection_params, make_broker_parser  # noqa: E402

from commlib.msg import PubSubMessage  # noqa: E402
from commlib.node import Node  # noqa: E402


class LidarScan(PubSubMessage):
    ranges: list = Field(default_factory=list)
    angle_min: float = -3.14
    angle_max: float = 3.14


class CameraFrame(PubSubMessage):
    frame_id: int = 0
    width: int = 640
    height: int = 480
    encoding: str = "rgb8"


class ImuReading(PubSubMessage):
    ax: float = 0.0
    ay: float = 0.0
    az: float = 9.81
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0


if __name__ == "__main__":
    parser = make_broker_parser("Publish multi-sensor robot data")
    args = parser.parse_args()
    conn_params = get_connection_params(args.broker, args.host, args.port)

    node = Node(
        node_name="robot.sensors",
        connection_params=conn_params,
        heartbeats=False,
    )

    mpub = node.create_mpublisher()
    lidar_pub = node.create_wpublisher(mpub, "robot.sensors.lidar")
    camera_pub = node.create_wpublisher(mpub, "robot.sensors.camera")
    imu_pub = node.create_wpublisher(mpub, "robot.sensors.imu")

    node.run()

    frame_id = 0
    start = time.time()
    try:
        while True:
            if args.timeout and time.time() - start > args.timeout:
                break

            lidar_msg = LidarScan(
                ranges=[round(random.uniform(0.2, 10.0), 2) for _ in range(36)],
            )
            lidar_pub.publish(lidar_msg)
            print(f"[lidar] {len(lidar_msg.ranges)} ranges")

            camera_msg = CameraFrame(frame_id=frame_id)
            camera_pub.publish(camera_msg)
            print(f"[camera] frame {frame_id}")

            imu_msg = ImuReading(
                ax=round(random.gauss(0, 0.1), 4),
                ay=round(random.gauss(0, 0.1), 4),
                az=round(9.81 + random.gauss(0, 0.05), 4),
                gx=round(random.gauss(0, 0.01), 4),
                gy=round(random.gauss(0, 0.01), 4),
                gz=round(random.gauss(0, 0.01), 4),
            )
            imu_pub.publish(imu_msg)
            print(f"[imu] az={imu_msg.az}")

            frame_id += 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
