# Commlib-py API Documentation

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Node API](#node-api)
- [Publisher/Subscriber API](#publishersubscriber-api)
- [RPC API](#rpc-api)
- [Action API](#action-api)
- [Transport API](#transport-api)
- [Utilities API](#utilities-api)
- [Message Types](#message-types)
- [Error Handling](#error-handling)
- [Advanced Features](#advanced-features)

---

## Overview

Commlib-py is a protocol-agnostic messaging library for Cyber-Physical Systems. It provides a unified API for communication patterns across multiple message brokers:

- **MQTT** - Lightweight pub/sub over TCP
- **Redis** - In-memory pub/sub and data store
- **AMQP** (RabbitMQ) - Enterprise messaging with guaranteed delivery
- **Kafka** - High-throughput distributed streaming
- **Mock** - Testing and local development

### Key Features

- Protocol-agnostic communication patterns (Pub/Sub, RPC, Actions)
- Automatic reconnection and error recovery
- Message compression and serialization options
- Comprehensive logging and debugging support
- Type-safe message handling with Pydantic models

---

## Installation

### From PyPI

```bash
pip install commlib-py
```

This installs the core library with only essential dependencies (pydantic, ujson, rich).

### With Protocol Support

Install support for specific message brokers:

```bash
# Install with specific protocol support
pip install commlib-py[mqtt]      # MQTT support (Paho MQTT)
pip install commlib-py[redis]     # Redis support (Hiredis)
pip install commlib-py[amqp]      # RabbitMQ/AMQP support (Pika)
pip install commlib-py[kafka]     # Kafka support

# Install with all protocol support
pip install commlib-py[all]       # All protocols

# Development installation with all protocols
pip install -e ".[dev]"
```

### From Source

```bash
git clone https://github.com/robotics-4-all/commlib-py.git
cd commlib-py
pip install -e .

# Or with specific protocols
pip install -e ".[mqtt,redis]"
```

---

## Core Concepts

### Communication Patterns

**1. Pub/Sub (Publish/Subscribe)**
- One-to-many asynchronous messaging
- Publishers send messages to topics
- Subscribers receive all messages on subscribed topics
- Decoupled producer and consumer

**2. RPC (Remote Procedure Call)**
- Request/response synchronous communication
- Client sends request, waits for response
- Server processes and replies
- Built-in timeout handling

**3. Actions (Preemptive Services)**
- Long-running operations with feedback
- Supports goal, feedback, result, and cancellation
- Ideal for robot control, streaming operations
- Comparable to ROS 2 Actions

### Transport Independence

```python
from commlib.transports.mqtt import ConnectionParameters as MQTTParams
from commlib.transports.redis import ConnectionParameters as RedisParams

# Use same API with different brokers
mqtt_params = MQTTParams(host="mqtt.example.com", port=1883)
redis_params = RedisParams(host="redis.example.com", port=6379)
```

---

## Node API

A **Node** is the primary entry point for creating communication endpoints. It abstracts transport selection and endpoint management.

### Creating a Node

```python
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

# Create a node with MQTT transport
conn_params = ConnectionParameters(
    host="localhost",
    port=1883,
    username="user",
    password="password"
)

node = Node(
    node_name="my_robot",
    connection_params=conn_params,
    debug=True  # Enable debug logging
)
```

### Connection Parameters

Each transport has its own `ConnectionParameters` class:

```python
# MQTT
from commlib.transports.mqtt import ConnectionParameters
params = ConnectionParameters(
    host="localhost",
    port=1883,
    username="",
    password="",
    protocol=MQTTProtocolType.MQTTv311,
    ssl=False,
    keepalive=60
)

# Redis
from commlib.transports.redis import ConnectionParameters
params = ConnectionParameters(
    host="localhost",
    port=6379,
    db=0,
    username="",
    password="",
    ssl=False
)

# AMQP (RabbitMQ)
from commlib.transports.amqp import ConnectionParameters
params = ConnectionParameters(
    host="localhost",
    port=5672,
    username="guest",
    password="guest",
    vhost="/",
    ssl=False
)

# Kafka
from commlib.transports.kafka import ConnectionParameters
params = ConnectionParameters(
    host="localhost",
    port=29092,
    group="my_group",
    auto_create_topics=True
)
```

### Node Methods

#### Publisher Creation

```python
# Simple publisher
pub = node.create_publisher(
    topic="sensors/temperature",
    msg_type=TemperatureMsg  # Optional: for type safety
)

# Multi-topic publisher (publish to any topic)
mpub = node.create_mpublisher(msg_type=SensorDataMsg)

# Pattern publisher (for wildcard subscriptions)
ppub = node.create_ppublisher(topic="sensors/#")
```

#### Subscriber Creation

```python
# Simple subscriber
def on_temperature(msg):
    print(f"Temperature: {msg.value}°C")

sub = node.create_subscriber(
    topic="sensors/temperature",
    on_message=on_temperature,
    msg_type=TemperatureMsg  # Optional: auto-parse to type
)

# Pattern subscriber (receives on matching topics)
def on_sensor_data(msg, topic):
    print(f"Received on {topic}: {msg}")

psub = node.create_psubscriber(
    topic="sensors/*",
    on_message=on_sensor_data,
    msg_type=SensorDataMsg
)
```

#### RPC Creation

```python
# RPC Service (server-side)
def add_numbers(request):
    result = request.a + request.b
    return AddMsg.Result(sum=result)

service = node.create_rpc_service(
    rpc_name="math/add",
    on_request=add_numbers,
    msg_type=AddMsg
)

# RPC Client (client-side)
client = node.create_rpc_client(
    rpc_name="math/add",
    msg_type=AddMsg
)

response = client.call(AddMsg.Request(a=5, b=3), timeout=5.0)
print(f"Result: {response.sum}")
```

#### Action Creation

```python
# Action Service
def on_goal_request(goal_h):
    # Process goal with feedback
    for progress in range(0, 101, 10):
        if goal_h.cancel_event.is_set():
            break
        # Publish feedback
        goal_h.publish_feedback(
            MoveMsg.Feedback(progress=progress)
        )
        time.sleep(0.1)
    
    return MoveMsg.Result(completed=True)

action_service = node.create_action_service(
    action_name="robot/move",
    on_goal_request=on_goal_request,
    msg_type=MoveMsg
)

# Action Client
action_client = node.create_action_client(
    action_name="robot/move",
    msg_type=MoveMsg
)

goal_h = action_client.send_goal(MoveMsg.Goal(distance=100))
for feedback in goal_h.get_feedback_iter(timeout=30):
    print(f"Progress: {feedback.progress}%")

result = goal_h.get_result()
print(f"Completed: {result.completed}")
```

### Node Lifecycle

```python
# Start the node (non-blocking)
node.run(wait=False)

# Run the node (blocking, runs forever)
node.run_forever(sleep_rate=10)  # Hz

# Gracefully shutdown
node.stop()
```

---

## Publisher/Subscriber API

### Publisher

```python
from commlib.msg import PubSubMessage

class TemperatureMsg(PubSubMessage):
    temperature: float
    unit: str = "celsius"

# Create publisher
pub = node.create_publisher(
    topic="sensors/temperature",
    msg_type=TemperatureMsg
)

# Publish messages
msg = TemperatureMsg(temperature=25.5)
pub.publish(msg)

# Or with dict (if msg_type not specified)
pub.publish({"temperature": 25.5, "unit": "celsius"})
```

### Multi-Topic Publisher

```python
# Publish to different topics dynamically
mpub = node.create_mpublisher(msg_type=SensorMsg)

mpub.publish(SensorMsg(value=42), "sensors/temperature")
mpub.publish(SensorMsg(value=60), "sensors/humidity")
```

### Subscriber

```python
# Callback-based
def on_message(msg):
    print(f"Received: {msg}")

sub = node.create_subscriber(
    topic="sensors/temperature",
    on_message=on_message,
    msg_type=TemperatureMsg
)

# With type safety
def on_typed_message(msg: TemperatureMsg):
    print(f"Temperature: {msg.temperature}°{msg.unit[0].upper()}")

sub = node.create_subscriber(
    topic="sensors/temperature",
    on_message=on_typed_message,
    msg_type=TemperatureMsg
)
```

### Pattern Subscriber (Wildcards)

```python
# Subscribe to multiple topics with pattern
def on_sensor_data(msg, topic):
    print(f"Topic: {topic}, Data: {msg}")

# Pattern notation: * matches any segment
psub = node.create_psubscriber(
    topic="sensors/*",           # Match: sensors/temperature, sensors/humidity
    on_message=on_sensor_data,
    msg_type=SensorMsg
)

psub = node.create_psubscriber(
    topic="robot.*.position",    # Match: robot.arm.position, robot.base.position
    on_message=on_sensor_data
)

psub = node.create_psubscriber(
    topic="events.*",            # Match everything under events/
    on_message=on_sensor_data
)
```

---

## RPC API

### Request/Response Message Types

```python
from commlib.msg import RPCMessage
from pydantic import Field

class CalculatorMsg(RPCMessage):
    class Request(RPCMessage.Request):
        operation: str = Field(..., description="add, subtract, multiply, divide")
        a: float
        b: float

    class Result(RPCMessage.Result):
        result: float
```

### RPC Service

```python
def on_calculator_request(request: CalculatorMsg.Request) -> CalculatorMsg.Result:
    """Process calculator RPC request."""
    if request.operation == "add":
        result = request.a + request.b
    elif request.operation == "subtract":
        result = request.a - request.b
    elif request.operation == "multiply":
        result = request.a * request.b
    elif request.operation == "divide":
        if request.b == 0:
            raise ValueError("Division by zero")
        result = request.a / request.b
    else:
        raise ValueError(f"Unknown operation: {request.operation}")
    
    return CalculatorMsg.Result(result=result)

# Create service
service = node.create_rpc_service(
    rpc_name="calculator",
    on_request=on_calculator_request,
    msg_type=CalculatorMsg
)

# Run service
node.run_forever()
```

### RPC Client

```python
# Create client
client = node.create_rpc_client(
    rpc_name="calculator",
    msg_type=CalculatorMsg
)

# Make RPC calls
try:
    response = client.call(
        CalculatorMsg.Request(
            operation="add",
            a=10,
            b=5
        ),
        timeout=5.0  # 5 second timeout
    )
    print(f"10 + 5 = {response.result}")
except Exception as e:
    print(f"RPC call failed: {e}")

# Multiple calls
operations = [
    ("add", 10, 5),
    ("multiply", 3, 4),
    ("divide", 20, 4),
]

for op, a, b in operations:
    try:
        result = client.call(
            CalculatorMsg.Request(operation=op, a=a, b=b),
            timeout=5.0
        )
        print(f"{a} {op} {b} = {result.result}")
    except Exception as e:
        print(f"Error: {e}")
```

### Error Handling

```python
from commlib.exceptions import (
    RPCClientTimeoutError,
    RPCRequestError,
    SubscriberError
)

try:
    response = client.call(request, timeout=2.0)
except RPCClientTimeoutError:
    print("RPC call timed out")
except RPCRequestError as e:
    print(f"RPC request failed: {e}")
```

---

## Action API

### Action Message Types

```python
from commlib.msg import ActionMessage

class RobotMoveMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_x: float
        target_y: float
        max_speed: float = 1.0

    class Result(ActionMessage.Result):
        success: bool
        final_x: float
        final_y: float

    class Feedback(ActionMessage.Feedback):
        current_x: float
        current_y: float
        progress: float  # 0-100%
```

### Action Service

```python
from commlib.action import GoalStatus
import time

def on_move_goal(goal_handle):
    """Handle robot movement goal."""
    goal = goal_handle.data
    current_x, current_y = 0.0, 0.0
    
    # Calculate movement direction
    distance = ((goal.target_x ** 2) + (goal.target_y ** 2)) ** 0.5
    if distance == 0:
        return RobotMoveMsg.Result(
            success=True,
            final_x=current_x,
            final_y=current_y
        )
    
    # Move in steps, publishing feedback
    steps = 20
    for step in range(steps):
        # Check if goal was cancelled
        if goal_handle.cancel_event.is_set():
            goal_handle.set_cancelled()
            break
        
        # Calculate progress
        progress = ((step + 1) / steps) * 100
        move_ratio = (step + 1) / steps
        
        current_x = goal.target_x * move_ratio
        current_y = goal.target_y * move_ratio
        
        # Publish feedback
        goal_handle.publish_feedback(
            RobotMoveMsg.Feedback(
                current_x=current_x,
                current_y=current_y,
                progress=progress
            )
        )
        
        # Simulate movement time
        time.sleep(0.1)
    
    # Return result
    return RobotMoveMsg.Result(
        success=True,
        final_x=current_x,
        final_y=current_y
    )

# Create action service
action_service = node.create_action_service(
    action_name="robot/move",
    on_goal_request=on_move_goal,
    msg_type=RobotMoveMsg
)
```

### Action Client

```python
# Create action client
action_client = node.create_action_client(
    action_name="robot/move",
    msg_type=RobotMoveMsg
)

# Send goal
goal_handle = action_client.send_goal(
    RobotMoveMsg.Goal(
        target_x=10.0,
        target_y=10.0,
        max_speed=1.0
    )
)

# Monitor feedback
try:
    for feedback in goal_handle.get_feedback_iter(timeout=30):
        print(f"Position: ({feedback.current_x:.2f}, {feedback.current_y:.2f})")
        print(f"Progress: {feedback.progress:.1f}%")
except TimeoutError:
    print("Action execution timed out")
    goal_handle.cancel()

# Get final result
result = goal_handle.get_result()
if result.success:
    print(f"Goal reached: ({result.final_x}, {result.final_y})")
else:
    print("Goal failed")

# Cancel goal
goal_handle.cancel()
```

---

## Transport API

### Direct Transport Usage

```python
from commlib.transports.mqtt import MQTTTransport, ConnectionParameters
from commlib.serializer import JSONSerializer
from commlib.compression import CompressionType

# Create transport directly
conn_params = ConnectionParameters(host="localhost", port=1883)

transport = MQTTTransport(
    conn_params=conn_params,
    serializer=JSONSerializer(),
    compression=CompressionType.NO_COMPRESSION
)

# Publish
transport.publish("topic/name", {"key": "value"})

# Subscribe
def callback(client, userdata, msg):
    print(f"Received: {msg.payload}")

transport.subscribe("topic/name", callback)

# Start transport
transport.start()
```

### Supported Transports

```python
# MQTT
from commlib.transports.mqtt import MQTTTransport

# Redis
from commlib.transports.redis import RedisTransport

# AMQP (RabbitMQ)
from commlib.transports.amqp import AMQPTransport

# Kafka
from commlib.transports.kafka import KafkaTransport

# Mock (for testing)
from commlib.transports.mock import MockTransport
```

---

## Utilities API

### Topic Conversion

Convert topic notation between different protocols:

```python
from commlib.utils import convert_topic_notation

# MQTT to Commlib unified notation
mqtt_topic = "sensors/+/temperature"
commlib_topic = convert_topic_notation(mqtt_topic, "mqtt", "commlib")
# Result: "sensors.*.temperature"

# Commlib to Kafka
commlib_topic = "sensors.temperature"
kafka_topic = convert_topic_notation(commlib_topic, "commlib", "kafka")
# Result: "sensors-temperature"

# Redis to MQTT
redis_topic = "events.system.*.logs"
mqtt_topic = convert_topic_notation(redis_topic, "redis", "mqtt")
# Result: "events/system/+/logs"

# Protocol-specific conversions
from commlib.utils import (
    topic_to_mqtt, topic_from_mqtt,
    topic_to_redis, topic_from_redis,
    topic_to_kafka, topic_from_kafka,
    topic_to_amqp, topic_from_amqp,
)

mqtt = topic_to_mqtt("sensors.*.temperature")  # "sensors/+/temperature"
redis = topic_to_redis("sensors.*.temperature")  # "sensors.*.temperature"
kafka = topic_to_kafka("sensors.temperature")  # "sensors-temperature"
amqp = topic_to_amqp("sensors.*.temperature")  # "sensors.*.temperature"
```

### Utility Functions

```python
from commlib.utils import (
    gen_timestamp,           # Generate current timestamp (ns)
    get_timestamp_ns,        # Get timestamp in nanoseconds
    get_timestamp_us,        # Get timestamp in microseconds
    get_timestamp_ms,        # Get timestamp in milliseconds
    camelcase_to_snakecase,  # Convert camelCase to snake_case
)

# Timestamps
ts_ns = gen_timestamp()
ts_us = get_timestamp_us()
ts_ms = get_timestamp_ms()

# String conversion
camel = "myVariableName"
snake = camelcase_to_snakecase(camel)  # "my_variable_name"
```

---

## Message Types

### PubSub Messages

```python
from commlib.msg import PubSubMessage
from pydantic import Field
from typing import Optional

class SensorReadingMsg(PubSubMessage):
    """Sensor reading message."""
    
    sensor_id: str = Field(..., description="Unique sensor identifier")
    value: float = Field(..., description="Measured value")
    unit: str = Field(default="", description="Measurement unit")
    timestamp: int = Field(default_factory=gen_timestamp, description="Timestamp (ns)")
    quality: Optional[float] = Field(None, description="Data quality 0-1")

# Create message
msg = SensorReadingMsg(
    sensor_id="temp_001",
    value=25.5,
    unit="celsius"
)

# Access fields
print(f"{msg.sensor_id}: {msg.value}{msg.unit}")

# Convert to dict
data = msg.model_dump()

# Convert from dict
msg2 = SensorReadingMsg(**data)
```

### RPC Messages

```python
from commlib.msg import RPCMessage

class EchoMsg(RPCMessage):
    """Echo RPC message."""
    
    class Request(RPCMessage.Request):
        text: str = Field(..., description="Text to echo")
        
    class Result(RPCMessage.Result):
        echoed_text: str = Field(..., description="Echoed text")

# RPC response
def echo_handler(request: EchoMsg.Request) -> EchoMsg.Result:
    return EchoMsg.Result(echoed_text=request.text)
```

### Action Messages

```python
from commlib.msg import ActionMessage

class TaskMsg(ActionMessage):
    """Long-running task message."""
    
    class Goal(ActionMessage.Goal):
        task_id: str
        parameters: dict = Field(default_factory=dict)
        
    class Result(ActionMessage.Result):
        success: bool
        duration_seconds: float
        
    class Feedback(ActionMessage.Feedback):
        step: int
        total_steps: int
        current_status: str
```

---

## Error Handling

### Exception Types

```python
from commlib.exceptions import (
    RPCClientTimeoutError,      # RPC call timed out
    RPCRequestError,            # RPC request validation failed
    SubscriberError,            # Subscriber initialization failed
)

try:
    response = client.call(request, timeout=5.0)
except RPCClientTimeoutError as e:
    print(f"Timeout: {e}")
except RPCRequestError as e:
    print(f"Invalid request: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Connection Error Handling

```python
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters
import time

conn_params = ConnectionParameters(host="localhost", port=1883)

# Automatic reconnection is built-in
node = Node(
    node_name="resilient_node",
    connection_params=conn_params
)

# Create endpoints
pub = node.create_publisher(topic="status")

# Publish with error handling
try:
    node.run(wait=False)
    
    for i in range(100):
        try:
            pub.publish({"counter": i})
        except Exception as e:
            print(f"Publish failed: {e}")
        time.sleep(1)
        
finally:
    node.stop()
```

---

## Advanced Features

### Message Serialization

```python
from commlib.serializer import JSONSerializer, TextSerializer, BinarySerializer

# JSON serialization (default)
json_serializer = JSONSerializer()

# Text/string serialization
text_serializer = TextSerializer()

# Binary serialization
binary_serializer = BinarySerializer()

# Use with node
node = Node(
    node_name="my_node",
    connection_params=conn_params,
    serializer=json_serializer
)
```

### Message Compression

```python
from commlib.compression import CompressionType

# No compression
node = Node(
    node_name="my_node",
    connection_params=conn_params,
    compression=CompressionType.NO_COMPRESSION
)

# Default compression
node = Node(
    node_name="my_node",
    connection_params=conn_params,
    compression=CompressionType.DEFAULT_COMPRESSION
)
```

### Custom Logging

```python
import logging
from commlib.node import Node

# Configure logging
logging.basicConfig(level=logging.DEBUG)

node = Node(
    node_name="my_node",
    connection_params=conn_params,
    debug=True
)

logger = logging.getLogger("my_app")
logger.info("Node created")
```

### Bridge Communication

```python
from commlib.bridges import Bridge
from commlib.transports.mqtt import ConnectionParameters as MQTTParams
from commlib.transports.redis import ConnectionParameters as RedisParams

# Bridge MQTT to Redis
mqtt_params = MQTTParams(host="mqtt.example.com")
redis_params = RedisParams(host="redis.example.com")

bridge = Bridge(
    name="mqtt_redis_bridge",
    left_conn_params=mqtt_params,
    right_conn_params=redis_params,
    topic_mapping={
        "sensors/temperature": "sensors.temperature",
        "sensors/humidity": "sensors.humidity"
    }
)

bridge.run_forever()
```

### Type Hints and Validation

```python
from pydantic import Field, validator
from commlib.msg import PubSubMessage
from typing import List

class RobotStateMsg(PubSubMessage):
    """Robot state message with validation."""
    
    robot_id: str = Field(..., description="Robot identifier")
    position: tuple = Field(..., description="Position (x, y)")
    velocity: float = Field(..., ge=0.0, description="Velocity >= 0")
    joint_angles: List[float] = Field(default_factory=list)
    
    @validator('position')
    def validate_position(cls, v):
        if len(v) != 2:
            raise ValueError('Position must be (x, y)')
        return v
    
    @validator('robot_id')
    def validate_robot_id(cls, v):
        if not v.startswith('robot_'):
            raise ValueError('Robot ID must start with robot_')
        return v
```

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete commlib-py example with multiple communication patterns."""

import time
import logging
from commlib.node import Node
from commlib.msg import PubSubMessage, RPCMessage, ActionMessage
from commlib.transports.mqtt import ConnectionParameters
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define message types
class TemperatureMsg(PubSubMessage):
    temperature: float
    unit: str = "celsius"

class GreetingMsg(RPCMessage):
    class Request(RPCMessage.Request):
        name: str
    
    class Result(RPCMessage.Result):
        greeting: str

class WorkMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        task_id: str
        duration: float
    
    class Result(ActionMessage.Result):
        success: bool
    
    class Feedback(ActionMessage.Feedback):
        progress: float

# Initialize node
conn_params = ConnectionParameters(host="localhost", port=1883)
node = Node(node_name="example_node", connection_params=conn_params)

# Publisher
temp_pub = node.create_publisher(topic="sensors/temperature", msg_type=TemperatureMsg)

# Subscriber
def on_temperature(msg: TemperatureMsg):
    logger.info(f"Temperature: {msg.temperature}°{msg.unit[0]}")

temp_sub = node.create_subscriber(
    topic="sensors/temperature",
    on_message=on_temperature,
    msg_type=TemperatureMsg
)

# RPC Service
def greet_handler(request: GreetingMsg.Request) -> GreetingMsg.Result:
    return GreetingMsg.Result(greeting=f"Hello, {request.name}!")

greet_service = node.create_rpc_service(
    rpc_name="greet",
    on_request=greet_handler,
    msg_type=GreetingMsg
)

# RPC Client
greet_client = node.create_rpc_client(rpc_name="greet", msg_type=GreetingMsg)

# Action Service
def work_handler(goal_handle):
    goal = goal_handle.data
    steps = 10
    for step in range(steps):
        if goal_handle.cancel_event.is_set():
            break
        progress = ((step + 1) / steps) * 100
        goal_handle.publish_feedback(WorkMsg.Feedback(progress=progress))
        time.sleep(goal.duration / steps)
    return WorkMsg.Result(success=True)

work_service = node.create_action_service(
    action_name="work",
    on_goal_request=work_handler,
    msg_type=WorkMsg
)

# Main loop
if __name__ == "__main__":
    try:
        node.run(wait=False)
        
        # Publish temperature
        temp_pub.publish(TemperatureMsg(temperature=22.5))
        
        # Call RPC
        response = greet_client.call(GreetingMsg.Request(name="World"), timeout=5.0)
        logger.info(f"RPC response: {response.greeting}")
        
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        node.stop()
```

---

## API Reference Quick Links

- **Node**: `commlib.node.Node`
- **Messages**: `commlib.msg` (PubSubMessage, RPCMessage, ActionMessage)
- **Transports**: `commlib.transports.*` (mqtt, redis, amqp, kafka, mock)
- **Serializers**: `commlib.serializer` (JSONSerializer, TextSerializer, BinarySerializer)
- **Utilities**: `commlib.utils` (topic conversion, timestamp generation)
- **Exceptions**: `commlib.exceptions` (RPCClientTimeoutError, RPCRequestError, SubscriberError)

---

## Documentation and Support

- **GitHub**: https://github.com/robotics-4-all/commlib-py
- **Issue Tracker**: https://github.com/robotics-4-all/commlib-py/issues
- **Examples**: https://github.com/robotics-4-all/commlib-py/tree/devel/examples
- **README**: https://github.com/robotics-4-all/commlib-py/blob/devel/README.md

---

## License

Commlib-py is licensed under the Apache License 2.0. See LICENSE file for details.
