# PTopicBridge Example

This is an example of bridging pubsub communication between brokers,
based on topic pattern match.

```
[Publisher A] -------> |          |                |          |
[Publisher B] -------> |          | {PtopicBridge} |          |
[Publisher C] -------> | Broker A | -------------> | Broker B | ------> [Subscriber]
[Publisher D] -------> |          | {PtopicBridge} |          |
[Publisher E] -------> |          |                |          |
```


![ptopicbridge_example](./docs/images/ptopicbridge_example.png)
