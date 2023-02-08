#!/usr/bin/env python

from commlib.msg import PubSubMessage
from commlib.transports.mqtt import ConnectionParameters, PSubscriber


class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def on_message(msg: SonarMessage, topic: str):
    print(f'[Broker-B] - Data received at topic - {topic}:{msg}')


if __name__ == '__main__':
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = 'sensors.*'
    bB_namespace = 'myrobot'

    bB_params = ConnectionParameters()

    sub = PSubscriber(
        conn_params=bB_params,
        topic=f'{bB_namespace}.{bA_uri}',
        msg_type=SonarMessage,
        on_message=on_message
    )
    sub.run_forever()
