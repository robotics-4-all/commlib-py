<div id="top">
<div align="center">

![commlib-py](https://github.com/robotics-4-all/commlib-py/assets/4770702/0dc3db01-eb5e-40a2-9d3a-07d25613fc86)

# commlib-py

**Protocol-agnostic Pub/Sub · RPC · Actions · Task Queue for Python**

*Write your messaging logic once. Switch between MQTT, Redis, AMQP, and Kafka by changing a single import.*

[![PyPI version](https://badge.fury.io/py/commlib-py.svg)](https://badge.fury.io/py/commlib-py)
[![Python](https://img.shields.io/pypi/pyversions/commlib-py.svg)](https://pypi.org/project/commlib-py/)
[![CI](https://github.com/robotics-4-all/commlib-py/actions/workflows/pytest.yml/badge.svg)](https://github.com/robotics-4-all/commlib-py/actions/workflows/pytest.yml)
[![License: MIT](https://img.shields.io/github/license/robotics-4-all/commlib-py)](https://github.com/robotics-4-all/commlib-py/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/commlib-py)](https://pepy.tech/project/commlib-py)
[![Downloads](https://static.pepy.tech/badge/commlib-py/month)](https://pepy.tech/project/commlib-py)

<img src="https://img.shields.io/badge/Redis-FF4438.svg?style=flat&logo=Redis&logoColor=white" alt="Redis">
<img src="https://img.shields.io/badge/MQTT-606?logo=mqtt&logoColor=fff&style=flat" alt="MQTT">
<img src="https://img.shields.io/badge/RabbitMQ-F60?logo=rabbitmq&logoColor=fff&style=flat" alt="RabbitMQ">
<img src="https://img.shields.io/badge/Apache%20Kafka-231F20?logo=apachekafka&logoColor=fff&style=flat" alt="Kafka">
<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat&logo=Pydantic&logoColor=white" alt="Pydantic">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">

</div>

---

## Table of Contents

- [What is commlib-py?](#-what-is-commlib-py)
- [30-Second Quickstart](#-30-second-quickstart)
- [Why commlib-py?](#-why-commlib-py)
- [Communication Patterns](#-communication-patterns)
- [Performance](#-performance)
- [Installation](#-installation)
- [API Reference](#-api-reference)
  - [Node](#node)
  - [RPC (Request/Response)](#reqresp---rpcs)
  - [Pub/Sub](#pubsub)
  - [Wildcard Subscriptions](#wildcard-subscriptions)
  - [Topic Notation Conversion](#topic-notation-conversion)
  - [Actions](#preemptive-services-with-feedback-actions)
- [Advanced](#%EF%B8%8F-advanced)
  - [Low-level Endpoints API](#endpoints-low-level-api)
  - [Broker-to-Broker Bridges](#b2b-bridges)
  - [TCP Bridge](#tcp-bridge)
  - [REST Proxy](#rest-proxy)
  - [Web Gateway](#web-gateway)
- [Examples](#-examples)
- [Testing](#-testing)
- [Roadmap](#%EF%B8%8F-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Star History](#-star-history)

---

## 🚀 What is commlib-py?

**commlib-py** is a communication library for Python implementing the most common messaging patterns — **Pub/Sub, RPC, Actions, and Task Queue** — on top of any message broker, with a single unified API.

It abstracts away MQTT, Redis, AMQP, and Kafka behind a clean, Pydantic-typed interface. Whether you're building IoT pipelines, distributed microservices, or robotic control systems, your application code stays the same regardless of the broker underneath.

<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/ab009804-75aa-4272-a471-b3f966e4011c">
</div>

---

## ⚡ 30-Second Quickstart

```python
from commlib.msg import PubSubMessage
from commlib.node import Node
# Change this one line to switch to Redis, AMQP, or Kafka — nothing else changes
from commlib.transports.mqtt import ConnectionParameters

class SensorData(PubSubMessage):
    temperature: float = 0.0
    humidity: float = 0.0

node = Node(node_name='weather_station', connection_params=ConnectionParameters())
pub = node.create_publisher(msg_type=SensorData, topic='sensors.weather')
node.run()
pub.publish(SensorData(temperature=23.5, humidity=65.0))
```

**Subscriber — swap `mqtt` for `redis`, `amqp`, or `kafka`, nothing else changes:**

```python
from commlib.transports.redis import ConnectionParameters  # swapped to Redis

node = Node(node_name='dashboard', connection_params=ConnectionParameters())
node.create_subscriber(
    msg_type=SensorData,
    topic='sensors.weather',
    on_message=lambda msg: print(f'Temp: {msg.temperature}C  Humidity: {msg.humidity}%')
)
node.run_forever()
```

---

## 🤔 Why commlib-py?

Building distributed systems in Python usually means picking a broker and writing boilerplate — `paho-mqtt`, `redis-py`, `pika`, `confluent-kafka` all have different APIs, different patterns for RPC, and no built-in support for higher-level primitives like Actions or Task Queues.

commlib-py solves this with **one consistent API** across all brokers:

|  | `paho-mqtt` | `redis-py` | `pika` (AMQP) | **commlib-py** |
|---|:---:|:---:|:---:|:---:|
| **Pub/Sub** | ✅ | ✅ | ✅ | ✅ |
| **RPC (Request/Response)** | ❌ DIY | ❌ DIY | ❌ DIY | ✅ built-in |
| **Actions w/ feedback** | ❌ | ❌ | ❌ | ✅ built-in |
| **Task Queue** | ❌ | ❌ | ❌ | ✅ built-in |
| **Typed messages (Pydantic v2)** | ❌ | ❌ | ❌ | ✅ |
| **Swap broker in 1 line** | ❌ | ❌ | ❌ | ✅ |
| **Cross-broker bridges** | ❌ | ❌ | ❌ | ✅ built-in |
| **Automatic connection pooling** | ❌ | manual | ❌ | ✅ |
| **Wildcard subscriptions** | ✅ | ✅ | ✅ | ✅ unified API |

---

## 📡 Communication Patterns

commlib-py implements four production-grade patterns on top of any supported broker:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Pub/Sub** | Fire-and-forget event publishing | Sensor streams, telemetry, events |
| **RPC** | Typed request/response with timeout | Service calls, queries, commands |
| **Actions** | Long-running tasks with cancellation & feedback | Robot motion, ML inference, batch jobs |
| **Task Queue** | Competing-consumer job distribution | Background workers, parallel processing |

All patterns work identically across MQTT, Redis, AMQP, and Kafka.

---

## 📊 Performance

- ✅ **6–10× fewer broker connections** via connection pooling
- ✅ **35% faster AMQP throughput** with optimized serialization
- ✅ **390+ tests** with continuous benchmarking via GitHub Actions CI/CD
- ✅ **Scaling tests** for 1–100 concurrent publishers

Serialization priority (auto-detected at runtime): `orjson` → `ujson` → `json`

See [Performance Documentation](docs/performance/) for detailed benchmarks and analysis.

---

## 🛠️ Installation

**Core (no broker dependencies):**

```sh
pip install commlib-py
```

**With specific broker support:**

```sh
pip install "commlib-py[mqtt]"     # MQTT via paho-mqtt
pip install "commlib-py[redis]"    # Redis via redis-py + hiredis
pip install "commlib-py[amqp]"     # AMQP via pika (RabbitMQ)
pip install "commlib-py[kafka]"    # Kafka via confluent-kafka
pip install "commlib-py[all]"      # All brokers
```

**For maximum performance:**

```sh
pip install "commlib-py[all,performance]"   # Adds orjson, msgpack, lz4 compression
```

**From source:**

```sh
git clone https://github.com/robotics-4-all/commlib-py.git
cd commlib-py
pip install -e ".[dev]"
```

> **Requires Python 3.9+**

---

## 📖 API Reference

### Node

A **Node** is the central building block of commlib-py. It follows the **Component-Port-Connector** model — each node binds to a single broker and exposes typed input/output ports for communication.

<div align="center">

| Port Type | Endpoint | Description |
|-----------|----------|-------------|
| **Input** | `Subscriber` | Listens for messages on a topic |
| **Input** | `RPCServer` | Handles RPC requests |
| **Input** | `ActionService` | Executes long-running tasks with feedback |
| **Output** | `Publisher` | Publishes messages to a topic |
| **Output** | `RPCClient` | Sends RPC requests and waits for responses |
| **Output** | `ActionClient` | Sends goals to an action service |
| **InOut** | `TopicBridge` | Bridges Pub/Sub between two brokers |
| **InOut** | `RPCBridge` | Bridges RPC between two brokers |
| **InOut** | `PTopicBridge` | Wildcard-based cross-broker topic bridge |

</div>

**Supported endpoint types across all transports:**

| Interface Type | MQTT | Redis | AMQP | Kafka |
|----------------|:----:|:-----:|:----:|:-----:|
| RPCClient / RPCServer | ✅ | ✅ | ✅ | ✅ |
| Publisher / Subscriber | ✅ | ✅ | ✅ | ✅ |
| MPublisher (multi-topic) | ✅ | ✅ | ✅ | ✅ |
| PSubscriber (wildcard) | ✅ | ✅ | ✅ | ✅ |
| ActionService / ActionClient | ✅ | ✅ | ✅ | ✅ |
| TaskProducer / TaskWorker | ✅ | ✅ | ✅ | ✅ |

```python
from commlib.node import Node
from commlib.msg import RPCMessage
from commlib.transports.redis import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

def add_two_int_handler(msg):
    return AddTwoIntMessage.Response(c=msg.a + msg.b)

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(
        node_name='add_two_ints_node',
        connection_params=conn_params,
        heartbeats=True,
        heartbeat_uri='nodes.add_two_ints.heartbeat',
        heartbeat_interval=10,
        ctrl_services=True,
    )
    rpc = node.create_rpc(
        msg_type=AddTwoIntMessage,
        rpc_name='add_two_ints_node.add_two_ints',
        on_request=add_two_int_handler
    )
    node.run_forever(sleep_rate=1)
```

**Node constructor:**

```python
class Node:
    def __init__(self,
                 node_name: Optional[str] = "",
                 connection_params: Optional[Any] = None,
                 debug: Optional[bool] = False,
                 heartbeats: Optional[bool] = True,
                 heartbeat_interval: Optional[float] = 10.0,
                 heartbeat_uri: Optional[str] = None,
                 compression: CompressionType = CompressionType.NO_COMPRESSION,
                 ctrl_services: Optional[bool] = False,
                 workers_rpc: Optional[int] = 4):
```

**Node methods:**

```python
node.create_subscriber(...)       # Pub/Sub subscriber
node.create_publisher(...)        # Pub/Sub publisher
node.create_rpc(...)              # RPC server
node.create_rpc_client(...)       # RPC client
node.create_action(...)           # Action service
node.create_action_client(...)    # Action client
node.create_mpublisher(...)       # Multi-topic publisher
node.create_psubscriber(...)      # Wildcard subscriber
node.create_task_producer(...)    # Task queue producer
node.create_task_worker(...)      # Task queue worker
node.run_forever(sleep_rate=1)    # Block and run
node.run(wait=True)               # Start (optionally blocking)
node.stop()                       # Graceful shutdown
```

---

### Req/Resp - RPCs

RPCs enable typed synchronous request/response between distributed components. Define your message schema once — the same class is used by both client and server.

#### Server Side Example

```python
from commlib.msg import RPCMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

# Callback function of the add_two_ints RPC
def add_two_int_handler(msg) -> AddTwoIntMessage.Response:
    print(f'Request Message: {msg.__dict__}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='add_two_ints_node',
                connection_params=conn_params)
    rpc = node.create_rpc(
        msg_type=AddTwoIntMessage,
        rpc_name='add_two_ints_node.add_two_ints',
        on_request=add_two_int_handler
    )
    node.run_forever(sleep_rate=1)
```

#### Client Side Example

```python
import time

from commlib.msg import RPCMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='myclient', connection_params=conn_params)
    rpc = node.create_rpc_client(
        msg_type=AddTwoIntMessage,
        rpc_name='add_two_ints_node.add_two_ints'
    )
    node.run()

    msg = AddTwoIntMessage.Request()
    while True:
        resp = rpc.call(msg)   # returns AddTwoIntMessage.Response
        print(resp)
        msg.a += 1
        msg.b += 1
        time.sleep(1)
```

---

### Pub/Sub

Event-driven messaging with typed, Pydantic-validated messages. Publishers and subscribers are completely decoupled — they don't need to know about each other.

#### Write a Simple Publisher

```python
from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

if __name__ == "__main__":
    conn_params = ConnectionParameters(host='localhost', port=1883)
    node = Node(node_name='sensors.sonar.front', connection_params=conn_params)
    pub = node.create_publisher(msg_type=SonarMessage, topic='sensors.sonar.front')
    node.run()
    msg = SonarMessage()
    while True:
        pub.publish(msg)
        msg.distance += 0.1
        time.sleep(1)
```

#### Write a Simple Subscriber

```python
import time
from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2

def on_message(msg):
    print(f'Received front sonar data: {msg}')

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='node.obstacle_avoidance', connection_params=conn_params)
    node.create_subscriber(msg_type=SonarMessage,
                           topic='sensors.sonar.front',
                           on_message=on_message)
    node.run_forever(sleep_rate=1)
```

---

### Wildcard Subscriptions

Subscribe to multiple topics using a single pattern. Use `PSubscriber` for pattern-based subscriptions and `MPublisher` for multi-topic publishing:

```python
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

def on_msg_callback(msg, topic):
    print(f'Message at topic <{topic}>: {msg}')

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='wildcard_subscription_example',
                connection_params=conn_params)

    # Subscribe to all topic.* messages
    node.create_psubscriber(topic='topic.*', on_message=on_msg_callback)
    # Publish to multiple topics from a single instance
    pub = node.create_mpublisher()
    node.run(wait=True)

    while True:
        pub.publish({'a': 1}, 'topic.a')
        pub.publish({'b': 1}, 'topic.b')
        time.sleep(1)
```

---

### Topic Notation Conversion

commlib-py uses a **unified dot-notation** (`a.b.c`) internally, converting automatically to/from each broker's native format.

| Protocol | Separator | Wildcard | Example |
|----------|-----------|----------|---------|
| **commlib** (unified) | `.` | `*` | `sensors.*.temperature` |
| **MQTT** | `/` | `+` (single) / `#` (multi) | `sensors/+/temperature` |
| **Redis** | `.` | `*` | `sensors.*.temperature` |
| **AMQP** | `.` | `*` / `#` | `sensors.*.temperature` |
| **Kafka** | `-` | `*` | `sensors-*-temperature` |

**Conversion utilities:**

```python
from commlib.utils import (
    convert_topic_notation,
    topic_to_mqtt, topic_from_mqtt,
    topic_to_redis, topic_from_redis,
    topic_to_kafka, topic_from_kafka,
    topic_to_amqp, topic_from_amqp,
)

# MQTT -> commlib
commlib_topic = topic_from_mqtt("sensors/+/temperature")
# Result: "sensors.*.temperature"

# commlib -> MQTT
mqtt_topic = topic_to_mqtt("sensors.*.temperature")
# Result: "sensors/+/temperature"

# Cross-protocol: Kafka -> MQTT
mqtt_topic = convert_topic_notation("sensors-temperature", "kafka", "mqtt")
# Result: "sensors/temperature"

# IoT hierarchy
commlib_topic = convert_topic_notation("home/+/sensors/+/temperature", "mqtt", "commlib")
# Result: "home.*.sensors.*.temperature"
```

Supported protocol names: `"commlib"`, `"mqtt"`, `"redis"`, `"amqp"`, `"kafka"`

---

### Preemptive Services with Feedback (Actions)

Actions are [pre-emptive services](https://en.wikipedia.org/wiki/Preemption_(computing)) with asynchronous feedback publishing. Built for long-running tasks that can be cancelled mid-execution — robot motion, ML inference, batch processing.

Each Action message defines three sub-messages: `Goal`, `Result`, and `Feedback`.

#### Write an Action Service

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage
from commlib.node import Node
from commlib.transports.redis import ConnectionParameters

class MoveByDistanceMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0

def on_goal_request(goal_h):
    c = 0
    res = MoveByDistanceMsg.Result()
    while c < goal_h.data.target_cm:
        if goal_h.cancel_event.is_set():   # Supports mid-execution cancellation
            break
        goal_h.send_feedback(MoveByDistanceMsg.Feedback(current_cm=c))
        c += 1
        time.sleep(1)
    res.dest_cm = c
    return res

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='myrobot.node.motion', connection_params=conn_params)
    node.create_action(
        msg_type=MoveByDistanceMsg,
        action_name='myrobot.move.distance',
        on_goal=on_goal_request
    )
    node.run_forever()
```

#### Write an Action Client

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage
from commlib.node import Node
from commlib.transports.redis import ConnectionParameters

class MoveByDistanceMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0

def on_feedback(feedback):
    print(f'ActionClient <on-feedback> callback: {feedback}')

def on_result(result):
    print(f'ActionClient <on-result> callback: {result}')

def on_goal_reached(result):
    print(f'ActionClient <on-goal-reached> callback: {result}')

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='action_client_example_node',
                connection_params=conn_params)
    action_client = node.create_action_client(
        msg_type=MoveByDistanceMsg,
        action_name='myrobot.move.distance',
        on_goal_reached=on_goal_reached,
        on_feedback=on_feedback,
        on_result=on_result
    )
    node.run()
    action_client.send_goal(MoveByDistanceMsg.Goal(target_cm=5))
    resp = action_client.get_result(wait=True)
    print(f'Action Result: {resp}')
    node.stop()
```

---

## 🏗️ Advanced

### Endpoints (Low-level API)

For applications that don't fit the `Node` model, endpoints can be constructed directly without binding to a node:

```python
from commlib.transports.redis import RPCService
from commlib.transports.amqp import Subscriber
from commlib.transports.mqtt import Publisher, RPCClient
```

Or use `endpoint_factory` for dynamic construction:

```python
import time
from commlib.endpoints import endpoint_factory, EndpointType, TransportType

def callback(data):
    print(data)

if __name__ == '__main__':
    topic = 'endpoints_factory_example'

    mqtt_sub = endpoint_factory(
        EndpointType.Subscriber,
        TransportType.MQTT)(topic=topic, on_message=callback)
    mqtt_sub.run()

    mqtt_pub = endpoint_factory(
        EndpointType.Publisher,
        TransportType.MQTT)(topic=topic, debug=True)
    mqtt_pub.run()

    data = {'a': 1, 'b': 2}
    while True:
        mqtt_pub.publish(data)
        time.sleep(1)
```

**All endpoint types:**

| Endpoint | Description | Supported Protocols |
|----------|-------------|---------------------|
| `RPCClient` / `RPCServer` | Typed request/response | MQTT, Redis, AMQP, Kafka |
| `Publisher` / `Subscriber` | Fire-and-forget messaging | MQTT, Redis, AMQP, Kafka |
| `MPublisher` | Publish to multiple topics | MQTT, Redis, AMQP, Kafka |
| `PSubscriber` | Wildcard topic subscription | MQTT, Redis, AMQP, Kafka |
| `WPublisher` / `WSubscriber` | Wrapped endpoints | MQTT, Redis |
| `ActionService` / `ActionClient` | Long-running tasks w/ feedback | MQTT, Redis, AMQP, Kafka |
| `TaskProducer` / `TaskWorker` | Competing-consumer job queue | MQTT, Redis, AMQP, Kafka |

---

### B2B Bridges

Bridge messages between brokers — including across different protocols. Ideal for Edge-to-Cloud pipelines, multi-broker architectures, and protocol translation.

<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/98993090-abfd-4e9f-b16e-ad9b7f436987">
</div>

```python
import commlib.transports.redis as rcomm
import commlib.transports.mqtt as mcomm
from commlib.bridges import RPCBridge, TopicBridge

def redis_to_mqtt_rpc_bridge():
    """[RPC Client] -> [Redis Broker] -> [MQTT Broker] -> [RPC Service]"""
    br = RPCBridge(
        from_uri='ops.start_navigation',
        to_uri='thing.robotA.ops.start_navigation',
        from_broker_params=rcomm.ConnectionParameters(),
        to_broker_params=mcomm.ConnectionParameters(),
    )
    br.run()

def redis_to_mqtt_topic_bridge():
    """[Producer] -> [Redis Broker] -> [MQTT Broker] -> [Consumer]"""
    br = TopicBridge(
        from_uri='sonar.front',
        to_uri='thing.robotA.sensors.sonar.front',
        from_broker_params=rcomm.ConnectionParameters(),
        to_broker_params=mcomm.ConnectionParameters(),
    )
    br.run()
```

**Pattern-based bridge (PTopicBridge)** — bridge all topics matching a wildcard:

```python
from commlib.msg import PubSubMessage
from commlib.bridges import PTopicBridge
import commlib.transports.redis as rcomm
import commlib.transports.mqtt as mcomm

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

if __name__ == '__main__':
    br = PTopicBridge(
        'sensors.*',          # From: all sensor topics on Redis
        'myrobot',            # To: namespace on MQTT
        rcomm.ConnectionParameters(),
        mcomm.ConnectionParameters(),
        msg_type=SonarMessage,
    )
    br.run()
```

**Bridge class signatures:**

```python
class Bridge:
    def __init__(self,
                 from_uri: str,
                 to_uri: str,
                 from_broker_params: BaseConnectionParameters,
                 to_broker_params: BaseConnectionParameters,
                 auto_transform_uris: bool = True,
                 debug: bool = False): ...

class RPCBridge(Bridge):
    def __init__(self, msg_type: RPCMessage = None, *args, **kwargs): ...

class TopicBridge(Bridge):
    def __init__(self, msg_type: PubSubMessage = None, *args, **kwargs): ...

class PTopicBridge(Bridge):
    def __init__(self,
                 msg_type: PubSubMessage = None,
                 uri_transform: List = [],
                 *args, **kwargs): ...
```

---

### TCP Bridge

Forwards raw TCP packets between two endpoints:

```
[Client] ------> [TCPBridge, port=xxxx] ---------> [TCP endpoint, port=xxxx]
```

A one-to-one connection is established between the bridge and the endpoint.

---

### REST Proxy

Enables **invocation of REST services via message brokers**. An RPC call is translated into a proper HTTP request — useful for exposing REST APIs into broker-based architectures.

<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/1507cb10-00ec-49ce-8159-967c23d1ba72">
</div>

```python
class RESTProxyMessage(RPCMessage):
    class Request(RPCMessage.Request):
        base_url: str
        path: str = '/'
        verb: str = 'GET'
        query_params: Dict[str, Any] = {}
        path_params: Dict[str, Any] = {}
        body_params: Dict[str, Any] = {}
        headers: Dict[str, Any] = {}

    class Response(RPCMessage.Response):
        data: Union[str, Dict, int]
        headers: Dict[str, Any]
        status_code: int = 200
```

See [commlib-rest-proxy](https://github.com/robotics-4-all/commlib-rest-proxy) for a ready-to-deploy Docker image.

---

### Web Gateway

A WebSocket/HTTP gateway that exposes your broker topics and RPCs to web clients.

See [commlib-web-gw](https://github.com/robotics-4-all/commlib-web-gw) for a ready-to-deploy Docker image.

---

## 🤖 Examples

The [`examples/`](./examples) directory contains runnable examples for every pattern:

| Example | Pattern | Description |
|---------|---------|-------------|
| `simple_pubsub/` | Pub/Sub | Basic publisher and subscriber |
| `simple_rpc/` | RPC | Request/response service |
| `simple_action/` | Action | Preemptive service with feedback |
| `node/` | Node | Node with multiple endpoints |
| `node_decorators/` | Node | Decorator-based node definition |
| `node_inherit/` | Node | Inheritance-based node pattern |
| `bridges/` | Bridge | Topic and RPC cross-broker bridges |
| `ptopic_bridge/` | Bridge | Wildcard pattern bridge |
| `multitopic_publisher/` | Pub/Sub | Multi-topic publishing |
| `minimize_conns/` | Pub/Sub | Connection pooling example |
| `topic_aggregator/` | Pub/Sub | Topic merge/aggregation |
| `endpoint_factory/` | Low-level | Direct endpoint construction |

---

## 🧪 Testing

commlib-py uses `pytest`. Broker integration tests require Docker.

**Quick test (unit only, no broker needed, ~15s):**
```sh
make ci
```

**With linting:**
```sh
make ci-strict
```

**Full suite including broker integration tests (~2min, requires Docker):**
```sh
make ci-full
```

**Individual steps:**
```sh
pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/benchmarks -v  # Unit only
pytest tests/benchmarks/ -v -m smoke                                           # Benchmarks
make coverage                                                                   # Coverage report
```

**Standalone benchmarks (no broker needed):**
```sh
python benchmark/bench_scaling.py --transport mock --test all
```

See [benchmark/README.md](benchmark/README.md) for full benchmark documentation.

---

## 🎞️ Roadmap

- [x] Protocol-agnostic architecture
- [x] MQTT, Redis, AMQP support
- [x] Kafka support (full endpoint parity)
- [x] RPCServer for AMQP and Kafka
- [x] Task Queue pattern across all transports
- [x] Connection pooling (6-10x fewer connections)
- [x] Optimized serialization (35% throughput improvement)
- [ ] Comprehensive integration testing
- [ ] AsyncIO transport backend

---

## 🤝 Contributing

- **💬 [Join the Discussions](https://github.com/robotics-4-all/commlib-py/discussions)** — questions, ideas, feedback
- **🐛 [Report Issues](https://github.com/robotics-4-all/commlib-py/issues)** — bugs and feature requests
- **💡 [Submit Pull Requests](https://github.com/robotics-4-all/commlib-py/blob/main/CONTRIBUTING.md)** — contributions welcome

<details>
<summary>Contributing Guidelines</summary>

1. Fork the repository
2. Clone your fork: `git clone https://github.com/{YOUR_ACCOUNT}/commlib-py.git`
3. Create a branch: `git checkout -b my-feature`
4. Make your changes and run `make ci-strict` to verify
5. Commit: `git commit -m 'Add my feature'`
6. Push: `git push origin my-feature`
7. Open a Pull Request

</details>

<details>
<summary>Contributors</summary>
<br>
<a href="https://github.com/robotics-4-all/commlib-py/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=robotics-4-all/commlib-py">
</a>
</details>

---

## 📜 License

commlib-py is released under the [MIT License](https://github.com/robotics-4-all/commlib-py/blob/main/LICENSE).

---

## 🌟 Star History

If commlib-py is useful to you, a ⭐ helps the project grow and reach more developers!

[![Star History Chart](https://api.star-history.com/svg?repos=robotics-4-all/commlib-py&type=Date)](https://www.star-history.com/#robotics-4-all/commlib-py&Date)

<div align="right">

[![Back to top][back-to-top]](#top)

</div>

[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square
