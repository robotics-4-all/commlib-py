# commlib-py Examples

Real-world examples demonstrating every communication pattern in commlib-py.

## Quick Start

Every example supports `--broker`, `--host`, `--port`, and `--timeout` flags:

```bash
python examples/smart_building/sensor_publisher.py --broker redis
python examples/smart_building/sensor_publisher.py --broker mqtt --host 10.0.0.5
python examples/smart_building/sensor_publisher.py --broker redis --timeout 10
```

## Scenarios

### Smart Building IoT (`smart_building/`)

A building management system with floor sensors, HVAC control, firmware updates, and maintenance task processing.

| File | Pattern | What It Shows |
|------|---------|---------------|
| `sensor_publisher.py` | **Pub/Sub** | Publish temperature/humidity readings |
| `sensor_subscriber.py` | **Pub/Sub** | Subscribe to sensor telemetry |
| `hvac_service.py` | **RPC** | HVAC set-temperature service with validation |
| `hvac_client.py` | **RPC** | Call HVAC service (valid + invalid requests) |
| `firmware_update_service.py` | **Action** | OTA firmware update with staged progress |
| `firmware_update_client.py` | **Action** | Request firmware update, monitor feedback |
| `maintenance_worker.py` | **Task Queue** | Process maintenance work orders |
| `maintenance_dispatcher.py` | **Task Queue** | Dispatch tasks with priorities |

### Robot Fleet Management (`robot_fleet/`)

A multi-robot fleet with telemetry, navigation, multi-sensor data, and delivery task dispatch.

| File | Pattern | What It Shows |
|------|---------|---------------|
| `robot_node.py` | **Node Inheritance** | Custom `RobotNode` class with auto-telemetry |
| `fleet_monitor.py` | **PSubscriber** | Wildcard `fleet.*.telemetry` monitoring |
| `multi_sensor_publisher.py` | **MPublisher/WPublisher** | Lidar + camera + IMU over shared connection |
| `navigation_service.py` | **Action** | Navigate-to-waypoint with position feedback |
| `navigation_client.py` | **Action** | Send navigation goal, track progress |
| `task_worker.py` | **Task Queue** | Robot delivery task worker |
| `task_dispatcher.py` | **Task Queue** | Dispatch delivery tasks with priorities |

### Edge-to-Cloud Bridging (`edge_to_cloud/`)

Cross-broker message forwarding for edge-to-cloud architectures.

| File | Pattern | What It Shows |
|------|---------|---------------|
| `topic_bridge.py` | **TopicBridge** | Forward sensor data between brokers |
| `rpc_bridge.py` | **RPCBridge** | Bridge RPC calls across brokers |
| `pattern_bridge.py` | **PTopicBridge** | Wildcard topic bridging |

### Advanced Patterns (`advanced/`)

| File | Pattern | What It Shows |
|------|---------|---------------|
| `endpoint_factory_demo.py` | **EndpointFactory** | Programmatic endpoint creation without Node |
| `decorator_node.py` | **Decorators** | `@node.subscribe` and `@node.rpc` syntax |
| `sensor_aggregator.py` | **TopicAggregator** | Merge multiple sensor streams |

## Feature Coverage

| commlib Feature | Example |
|----------------|---------|
| Publisher / Subscriber | `smart_building/sensor_*` |
| RPCService / RPCClient | `smart_building/hvac_*` |
| ActionService / ActionClient | `smart_building/firmware_*`, `robot_fleet/navigation_*` |
| TaskProducer / TaskWorker | `smart_building/maintenance_*`, `robot_fleet/task_*` |
| Node Inheritance | `robot_fleet/robot_node.py` |
| MPublisher / WPublisher | `robot_fleet/multi_sensor_publisher.py` |
| PSubscriber (wildcards) | `robot_fleet/fleet_monitor.py` |
| TopicBridge / RPCBridge | `edge_to_cloud/topic_bridge.py`, `rpc_bridge.py` |
| PTopicBridge | `edge_to_cloud/pattern_bridge.py` |
| EndpointFactory | `advanced/endpoint_factory_demo.py` |
| Node Decorators | `advanced/decorator_node.py` |
| TopicAggregator | `advanced/sensor_aggregator.py` |
