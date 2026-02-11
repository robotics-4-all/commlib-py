# commlib/transports/ — Transport Backends

## OVERVIEW

Each transport module implements the same endpoint API (Publisher, Subscriber, RPCService, RPCClient, ActionService, ActionClient, etc.) on top of a specific broker protocol. All transports extend `BaseTransport`.

## STRUCTURE

```
transports/
├── __init__.py         # TransportType enum (AMQP=1, REDIS=2, MQTT=3, KAFKA=4)
│                       # connection_params_for_transport() — lazy import factory
├── base_transport.py   # BaseTransport: conn_params, connected state, Event-driven wait
├── mqtt.py             # paho-mqtt: ConnectionParameters, Publisher, Subscriber, RPCService, etc.
├── redis.py            # redis-py: ConnectionParameters, connection pooling (_connection_pools)
├── amqp.py             # pika: ConnectionParameters, threaded channel management
├── kafka.py            # confluent-kafka: ConnectionParameters, partial implementation
└── mock.py             # In-memory transport for unit testing — no external deps
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| New transport backend | Create `{protocol}.py` | Must define: `ConnectionParameters`, `Publisher`, `Subscriber`, `RPCService`, `RPCClient`, `MPublisher`, `PSubscriber` |
| Connection pooling | `redis.py` | Class-level `_connection_pools` dict, `_get_or_create_pool()` |
| Connection state mgmt | `base_transport.py` | `_set_connected()`, `wait_connected()`, `wait_disconnected()` |
| Mock transport (tests) | `mock.py` | `ConnectionParameters()` with defaults, no real broker needed |
| Endpoint registration | `__init__.py` | Add `TransportType` enum member + `connection_params_for_transport()` case |
| Endpoint factory hook | `../endpoints.py` | Add import + mapping in `endpoint_factory()` |

## CONVENTIONS

- **Every transport module exports**: `ConnectionParameters`, `Publisher`, `Subscriber`, `RPCService`, `RPCClient`, `MPublisher`, `PSubscriber`, `ActionService`, `ActionClient` (where supported)
- **ConnectionParameters**: Extends `BaseConnectionParameters(BaseModel)` — adds protocol-specific fields (auth, db, vhost, etc.)
- **Lazy imports**: Transport deps (`paho.mqtt`, `redis`, `pika`, `confluent_kafka`) imported inside module only
- **Thread model**: Each transport manages its own threading (e.g., MQTT uses `loop_start()`, Redis uses polling threads, AMQP uses threaded channels)
- **run(wait=True)**: All transports must support the `wait` parameter in `run()`

## TRANSPORT SUPPORT MATRIX

| Feature | MQTT | Redis | AMQP | Kafka | Mock |
|---------|------|-------|------|-------|------|
| Publisher | Y | Y | Y | Y | Y |
| Subscriber | Y | Y | Y | Y | Y |
| MPublisher | Y | Y | Y | Y | Y |
| PSubscriber | Y | Y | Y | Y | Y |
| RPCService | Y | Y | Y | Y | Y |
| RPCClient | Y | Y | Y | Y | Y |
| RPCServer | Y | Y | Y | Y | Y |
| ActionService | Y | Y | Y | Y | Y |
| ActionClient | Y | Y | Y | Y | Y |
| WPublisher | Y | Y | N | N | N |
| WSubscriber | Y | Y | N | N | N |
| Connection Pool | N | Y | N | N | N |

## ANTI-PATTERNS

- **Never** import broker client libraries at package level — install is optional
- **Never** skip `wait` parameter in `run()` — was a bug fixed in commit `148b825`
- **Kafka**: Full endpoint parity achieved — all endpoint types now supported
- **Redis pool cleanup**: Must reset class variables — was a bug fixed in commit `5291b9c`
