# commlib/ — Core Library

## OVERVIEW

Protocol-agnostic communication library core. Defines base classes for endpoints (Pub/Sub, RPC, Action), message types, Node abstraction, serialization, and bridge patterns.

## STRUCTURE

```
commlib/
├── __init__.py         # Version only (0.13.1), no re-exports
├── msg.py              # Message hierarchy: Message → RPCMessage, PubSubMessage, ActionMessage
├── node.py             # Node: component-port-connector model, creates endpoints via factories
├── endpoints.py        # BaseEndpoint + endpoint_factory(etype, etransport)
├── pubsub.py           # BasePublisher, BaseSubscriber, BaseMPublisher, BasePSubscriber
├── rpc.py              # BaseRPCService, BaseRPCClient, BaseRPCServer
├── action.py           # BaseActionService, BaseActionClient, GoalHandler, GoalStatus
├── bridges.py          # TopicBridge, RPCBridge, PTopicBridge — cross-broker forwarding
├── connection.py       # BaseConnectionParameters(BaseModel), AuthBase, AuthPlain
├── serializer.py       # JSONSerializer (orjson > ujson > json), ContentType, Serializer
├── compression.py      # CompressionType enum + compress/decompress utils
├── exceptions.py       # Custom exceptions: RPCClientError, PublisherError, etc.
├── utils.py            # gen_random_id, get_timestamp_ns, topic_to_*/topic_from_* conversions
├── async_utils.py      # safe_wrapper, safe_gather, safe_ensure_future
├── timer.py            # Timer utility
├── aggregation.py      # Message aggregation patterns
├── tcp_proxy.py        # TCP bridge (separate from transport layer)
└── transports/         # Transport backends (see transports/AGENTS.md)
```

## WHERE TO LOOK

| Task | File | Key Classes/Functions |
|------|------|----------------------|
| New message type | `msg.py` | Inherit `Message`, `RPCMessage`, `PubSubMessage`, or `ActionMessage` |
| New endpoint type | `endpoints.py` | Add to `EndpointType` enum + `endpoint_factory` |
| Node factory method | `node.py` | Add `create_*` method to `Node` class |
| New exception | `exceptions.py` | Inherit `BaseException(Exception)` with `(message, errors=None)` |
| Serialization format | `serializer.py` | Add backend alongside `JSONSerializer` |
| Topic conversion | `utils.py` | Add `topic_to_X`/`topic_from_X` + update `convert_topic_notation` |
| Cross-broker bridge | `bridges.py` | Inherit from `Bridge` base class |

## CONVENTIONS

- **Logging**: Every module uses lazy singleton pattern:
  ```python
  module_logger = None
  class MyClass:
      @classmethod
      def logger(cls): ...  # global module_logger init
      @property
      def log(self): return self.logger()
  ```
- **Threading**: `BaseTransport` uses `threading.Event` for connection state (no busy-wait)
- **BaseEndpoint.run(wait=True)**: Uses event-driven `wait_connected()` with timeout fallback
- **Message pattern**: Nested inner classes for RPC (`Request`/`Response`) and Action (`Goal`/`Result`/`Feedback`)
- **`__init__.py`**: Minimal — only `__version__`, `__author__`, `__email__`. No re-exports.

## ANTI-PATTERNS

- **Never** import transport modules at top-level — they have optional deps
- **Never** use `json` stdlib directly — always go through `commlib.serializer.JSONSerializer`
- **Never** create raw threads for heartbeats — use `HeartbeatThread` in `node.py`
- **Action GoalHandler**: Must check `cancel_event.is_set()` in loops for preemption support
