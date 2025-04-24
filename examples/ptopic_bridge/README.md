## Topic Bridge Example

This example demonstrates how to create a topic bridge using `commlib-py` to forward messages between different message brokers (Redis and MQTT in this case). It involves three scripts:

* **`bridge.py`**: Creates the topic bridge.
* **`mqtt_sub.py`**: Creates a subscriber on the MQTT broker to receive forwarded messages.
* **`redis_pu.py`**: Creates a publisher on the Redis broker to send messages that will be forwarded.


### `bridge.py`

This script sets up a `PTopicBridge` to forward messages from a Redis broker to an MQTT broker.

```python
#!/usr/bin/env python

import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.bridges import PTopicBridge, TopicBridgeType
from commlib.msg import PubSubMessage

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

if __name__ == "__main__":
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "sensors.*"
    bB_namespace = "myrobot"

    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()

    br = PTopicBridge(
        bA_uri,
        bB_namespace,
        bA_params,
        bB_params,
        msg_type=SonarMessage,
    )
    br.run_forever()
```

**Message Definition:**
- Defines a SonarMessage class, which inherits from PubSubMessage, to represent the structure of the messages being transmitted.

**Bridge Setup:**
- Specifies the topic URI (bA_uri) on the Redis broker (Broker A) to subscribe to (using a wildcard)
- Specifies a namespace (bB_namespace) on the MQTT broker (Broker B) where the messages will be forwarded.
- Creates ConnectionParameters for both Redis and MQTT.
- Creates a PTopicBridge instance, specifying the bridge type (REDIS_TO_MQTT), URI, namespace, connection parameters, and message type.
- Starts the bridge's event loop using br.run_forever().

### `mqtt_sub.py`

This script sets up a subscriber on the MQTT broker to receive the messages forwarded by the bridge.

```python
#!/usr/bin/env python

from commlib.msg import PubSubMessage
from commlib.transports.mqtt import ConnectionParameters, PSubscriber

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

def on_message(msg: SonarMessage, topic: str):
    print(f"[Broker-B] - Data received at topic - {topic}:{msg}")

if __name__ == "__main__":
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_uri = "sensors.*"
    bB_namespace = "myrobot"

    bB_params = ConnectionParameters()

    sub = PSubscriber(
        conn_params=bB_params,
        topic=f"{bB_namespace}.{bA_uri}",
        msg_type=SonarMessage,
        on_message=on_message,
    )
    sub.run_forever()
```

**Message Definition:**
- Defines the same SonarMessage class as bridge.py to ensure message compatibility.

**Subscriber Setup:**
- Specifies the topic to subscribe to on the MQTT broker.
- The topic includes the namespace defined in bridge.py.
- Creates ConnectionParameters for MQTT.
- Creates a PSubscriber instance, specifying the connection parameters, topic, message type, and a callback function (on_message) to handle received messages.
- Starts the subscriber's event loop.

**Message Handling:**
- The on_message function prints the received message and the topic to the console.

### `redis_pub.py`

This script sets up a publisher on the Redis broker to send messages that will be forwarded by the bridge.

```python
#!/usr/bin/env python
import time

from commlib.msg import PubSubMessage
from commlib.transports.redis import ConnectionParameters, MPublisher

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

if __name__ == "__main__":
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    p1 = "sensors.sonar.front"
    p2 = "sensors.ir.rear"

    bA_params = ConnectionParameters()

    pub = MPublisher(conn_params=bA_params, msg_type=SonarMessage)

    msg = SonarMessage()
    while True:
        pub.publish(msg, p1)
        pub.publish(msg, p2)
        time.sleep(1)
        msg.distance += 1
```

**Message Definition:**
- Defines the SonarMessage class, consistent with the other scripts.

**Publisher Setup:**
- Specifies the topics (p1, p2) on the Redis broker to publish to.
- Creates ConnectionParameters for Redis.
- Creates an MPublisher instance, specifying the connection parameters, message type, and enabling debug logging.

**Message Publishing:**
- Enters an infinite loop to continuously publish SonarMessage instances to the specified topics.
- Increments the distance value in the message.

Ensure that `bridge.py` is running before `mqtt_sub.py` and `redis_pub.py`. You should see the messages published by `redis_pub.py` being forwarded by `bridge.py` and received by `mqtt_sub.py`.
