# Simple PubSub

## Implementation of the Subscriber Node

```python
#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass
from commlib.node import Node, TransportType


@DataClass
class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


def on_message(msg):
    print(f'Received front sonar data: {msg}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='obstacle_avoidance_node',
                transport_type=transport,
                transport_connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    node.create_subscriber(msg_type=SonarMessage,
                           topic='sensors.sonar.front',
                           on_message=on_message)

    node.run_forever(sleep_rate=1)
```

## Implementation of the Publisher Node

```python
#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage, MessageHeader, DataClass
from commlib.node import Node, TransportType


@DataClass
class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
        transport = TransportType.REDIS
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
        transport = TransportType.AMQP
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
        transport = TransportType.MQTT
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='sensors.sonar.front',
                transport_type=transport,
                transport_connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)

    pub = node.create_publisher(msg_type=SonarMessage,
                                topic='sensors.sonar.front')

    msg = SonarMessage()
    while True:
        pub.publish(msg)
        msg.range += 1
        time.sleep(1)
```
