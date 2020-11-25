# commlib-py
Broker-based communication framework written in python 3.
Implements the most common communication patterns (RPC/ReqResp, PubSub) over a message broker.
A message broker is a communication middleware responsible for routing messages to the
proper endpoints. Some examples of message brokers are: AMQP-based brokers (e.g. RabbitMQ),
Apache Kafka, MQTT brokers (e.g. Mosquito) and Redis.

Yes, Redis can also be used as a message broker for RPC and PubSub communication!!

Currently, AMQP, Redis and MQTT brokers are supported.

The goal of this project is to implement a standard communication middleware
based on message brokers, for building systems. A system can be a device, 
an IoT environment or a software platformm. Performance is also considered
as it is often used on low-cost devices, so messaging has to be fast and with
low footprint.


# Installation


```bash
python setup.py install
```

or

```bash
pip install . --user
```

# Features
The purpose of this implementation is to provide an application-level communication layer, 
by providing implementations for Remote-Procedure-Calls (RPCs), Topic-based PubSub, Preemptable Services
(aka Actions), Events etc.

## Node

The concept **Node** is a software component that follows the Component-Port-Connector model.
A Node has input and output ports for communicating with the world. Each
port defines an endpoint and can be of type:

- Input Port:
  - Subscriber
  - RPC Service
  - Action Service
- Output Port:
  - Publisher
  - RPC Client
  - Action Client


Furthermore, it implements several features:
- Publish Heartbeat messages in the background for as long as the node is active
- Provide control interfaces, to `start` and `stop` the execution of the Node
- Provides methods to create ports.

```python
from commlib.node import Node, TransportType
from commlib.msg import RPCMessage, DataClass
## Import the Redis transports
## Imports are lazy handled internally
from commlib.transports.redis import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


def on_request(msg):
    print(f'On-Request: {msg}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp


if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='example-node',
                transport_type=transport,
                transport_connection_params=conn_params,
                debug=True)

    # Create  an RPCService endpoint
    rpc = node.create_rpc(msg_type=AddTwoIntMessage,
                          rpc_name='testrpc',
                          on_request=on_request)
    # Starts the RPCService and wait until an exit signal is catched.
    node.run_forever()
```

A Node always binds to a specific broker for implementing the input and
output ports. Of course you can instantiate and run several Nodes in a single-process 
application.

## Req/Resp (RPC) Communication

```
                             +---------------+
                   +-------->+   RPC Topic   +------+
+--------------+   |         |               |      |        +---------------+
|              +---+         +---------------+      +------->+               |
|  RPC Client  |                                             |  RPC Service  |
|              +<--+         +---------------+      +--------+               |
+--------------+   |         |Temporaty Topic|      |        +---------------+
                   +---------+               +<-----+
                             +---------------+
```


### Server Side

```python
from commlib.transports.redis import (
    RPCService, ConnectionParameters
)
from commlib.msg import RPCMessage, DataClass


# The RPC Communication Object
class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


def add_two_int_handler(msg):
    # This is the implementation of the RPC callback.
    print(f'Request Message: {msg}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp


if __name__ == '__main__':
    conn_params = ConnectionParameters()
    rpc_name = 'example_rpc_service'

    rpc = RPCService(rpc_name=rpc_name,
                     msg_type=AddTwoIntMessage,
                     conn_params=conn_params,
                     on_request=add_two_int_handler)
    rpc.run_forever()
```

### Client Side

```python
from commlib.transports.redis import (
    RPCClient, ConnectionParameters
)
from commlib.msg import RPCMessage, DataClass


# The RPC Communication Object
class AddTwoIntMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    @DataClass
    class Response(RPCMessage.Response):
        c: int = 0


if __name__ == '__main__':
    conn_params = ConnectionParameters()
    rpc_name = 'example_rpc_service'

    client = RPCClient(rpc_name=rpc_name,
                    msg_type=AddTwoIntMessage,
                    conn_params=conn_params)
    msg = AddTwoIntMessage.Request(a=1, b=2)
    resp = client.call(msg)
    print(resp)
```


## PubSub Communicaton

```
                                                    +------------+
                                                    |            |
                                            +------>+ Subscriber |
                                            |       |            |
                                            |       +------------+
                                            |
+-----------+             +------------+    |       +------------+
|           |             |            |    |       |            |
| Publisher +------------>+   Topic    +----------->+ Subscriber |
|           |             |            |    |       |            |
+-----------+             +------------+    |       +------------+
                                            |
                                            |       +------------+
                                            |       |            |
                                            +------>+ Subscriber |
                                                    |            |
                                                    +------------+
```

### Write a Simple Topic Publisher

```python
import time

from commlib.msg import PubSubMessage, DataClass
from commlib.transports.mqtt import (
    Publisher, ConnectionParameters
)


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


if __name__ == "__main__":
    conn_params = ConnectionParameters(host='localhost', port=1883)
    pub = Publisher(topic=topic, msg_type=SonarMessage, conn_params=conn_params)
    msg = SonarMessage(distance=2.0)
    while True:
        time.sleep(0.5)
        pub.publish(msg)
        msg.distance += 1

```

### Write a Simple Topic Subscriber

```python
import time

from commlib.msg import PubSubMessage, DataClass
from commlib.transports.mqtt import (
    Subscriber, ConnectionParameters
)


@DataClass
class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0


def sonar_data_callback(msg):
    print(f'Message: {msg}')


if __name__ == "__main__":
    conn_params = ConnectionParameters(host='localhost', port=1883)
    sub = Subscriber(topic=topic,
                     on_message=sonar_data_callback,
                     conn_params=conn_params)
    sub.run()
    while True:
        time.sleep(0.001)
```

## Preemptable Services with Feedback (Actions)

Actions are [pre-emptable services](https://en.wikipedia.org/wiki/Preemption_(computing)) 
with support for asynchronous feedback publishing. This communication pattern
is used to implement services which can be stopped and can provide feedback data, such 
as the move command service of a robot.


### Write an Action Service

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage, DataClass
from commlib.transports.redis import (
    ActionServer, ConnectionParameters
)


class ExampleAction(ActionMessage):
    @DataClass
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    @DataClass
    class Result(ActionMessage.Result):
        dest_cm: int = 0

    @DataClass
    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_goal(goal_h):
    c = 0
    res = ExampleAction.Result()
    while c < goal_h.data.target_cm:
        if goal_h.cancel_event.is_set():
            break
        goal_h.send_feedback(ExampleAction.Feedback(current_cm=c))
        c += 1
        time.sleep(1)
    res.dest_cm = c
    return res


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    action = ActionServer(msg_type=ExampleAction,
                          conn_params=conn_params,
                          action_name=action_name,
                          on_goal=on_goal)
    action.run()
    while True:
      time.sleep(0.001)
```

### Write an Action Client

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage, DataClass
from commlib.transports.redis import (
    ActionClient, ConnectionParameters
)


class ExampleAction(ActionMessage):
    @DataClass
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    @DataClass
    class Result(ActionMessage.Result):
        dest_cm: int = 0

    @DataClass
    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_feedback(feedback):
    print(f'ActionClient <on-feedback> callback: {feedback}')


def on_goal_reached(result):
    print(f'ActionClient <on-goal-reached> callback: {result}')


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    action_c = ActionClient(msg_type=ExampleAction,
                            conn_params=conn_params,
                            action_name=action_name,
                            on_feedback=on_feedback,
                            on_goal_reached=on_goal_reached)
    goal_msg = ExampleAction.Goal(target_cm=5)
    action_c.send_goal(goal_msg)
    resp = action_c.get_result(wait=True)
    print(resp)
```

## Transports

### AMQP / RabbitMQ

AMQP RPC (request/reply) and PubSub Endpoints are supported by the protocol itself, using
deticated exchanges.

For RPC enpoints a `Direct Exchange` is used to route requests and responses,
optionally using the [Direct Reply-to](https://www.rabbitmq.com/direct-reply-to.html).
If the `Direct Reply-to` feature is used, then RPC endpoints must publish
to the default exchange `""`.

To use `Direct Reply-to`, an RPC client should:
- Consume from the pseudo-queue `amq.rabbitmq.reply-to` in no-ack mode.
- Set the `reply-to` property in their request message to `amq.rabbitmq.reply-to`.

Meta-information such as the serialization method used, is passed through the
[message properties](https://www.rabbitmq.com/consumers.html#message-properties)
metadata, as specified my AMQP.


### Redis

PubSub endpoints uses the out-of-the-box [Redis pubsub channel](https://redis.io/topics/pubsub) to exchange messages. PubSub message payload in Redis includes the
data of the message and meta-information regarding serialization method used, 
timestamp, etc. Below is an example of the payload for pubsub communication.

```
{
  'data': {},
  'meta': {
    'timestamp': <int>,
    'reply_to': <str>,
    'properties': {
      'content_type': 'application/json',
      'content_encoding': 'utf8'
    }
  }
}
```

This is useful for transparency between brokers. Default values are evident
in the previous example.

Req/Resp communication (RPC) is not supported out-of-the-box. To support
RPC communication over Redis, a custom layer implements the pattern for both endpoints 
using Redis Lists to represent queues. RPC server listens for requests from
a list, while an RPC client sends request messages to that list. In order for
the client to be able to receive responses, he must listen to a temporary queue.
To achieve this, the request message must include a `reply_to` property that is 
used by the RPCServer implementation to send the response message. Below is the 
data model of the request message.

```
{
  'data': {},
  'meta': {
    'timestamp': <int>,
    'reply_to': <str>,
    'properties': {
      'content_type': 'application/json',
      'content_encoding': 'utf8'
    }
  }
}
```

**Note**: The **RPC Client** implementation is responsible to remove any created 
temporary queues!


### MQTT


PubSub message payload in MQTTT includes the
data of the message and meta-information regarding serialization method used, 
timestamp, etc. Below is an example of the payload for pubsub communication.

```
{
  'data': {},
  'meta': {
    'timestamp': <int>,
    'reply_to': <str>,
    'properties': {
      'content_type': 'application/json',
      'content_encoding': 'utf8'
    }
  }
}
```

This is useful for transparency between brokers. Default values are evident
in the previous example.

Though, Req/Resp communication (RPC) is not supported out-of-the-box. To support
RPC communication over MQTT, a custom layer implements the pattern for both endpoints 
using MQTT Lists to represent queues. RPC server listens for requests from
a list, while an RPC client sends request messages to that list. In order for
the client to be able to receive responses, he must listen to a temporary queue.
To achieve this, the request message must include a `reply_to` property that is 
used by the RPCServer implementation to send the response message. Below is the 
data model of the request message.

```
{
  'data': {},
  'meta': {
    'timestamp': <int>,
    'reply_to': <str>,
    'properties': {
      'content_type': 'application/json',
      'content_encoding': 'utf8'
    }
  }
}
```

## Broker-to-broker (B2B) bridges

In the context of IoT and CPS, it is a common requirement to bridge messages
between message brokers, based on application-specific rules. An example is to 
bridge analytics (preprocessed) data from the Edge to the Cloud. And what happens
if the brokers use different communication protocols?

In the context of the current work, communication bridges are implemented for
PubSub and RPC communication between various message brokers. Currently, MQTT, 
AMQP and Redis are supported.

![bridges_1](./assets/BrokerMessaging-Bridges.png)


**TODO**: Action bridges

# Examples

Examples can be found at the `./examples` directory of this repo

# Tests

TODO

# Roadmap

TODO

# Credis

TODO
