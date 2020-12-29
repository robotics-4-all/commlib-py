#!/usr/bin/env python

import time

from commlib.transports.redis import MPublisher, ConnectionParameters
from commlib.msg import PubSubMessage, DataClass

@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


if __name__ == '__main__':
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    p1 = 'sensors.sonar.front'
    p2 = 'sensors.ir.rear'

    bA_params = ConnectionParameters()

    pub = MPublisher(conn_params=bA_params,
                     msg_type=SonarMessage,
                     debug=True)

    msg = SonarMessage()
    while True:
        pub.publish(msg, p1)
        pub.publish(msg, p2)
        time.sleep(1)
        msg.distance += 1


