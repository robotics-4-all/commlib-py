# commlib-py
Broker-based communication framework written in python 3.
Implements the most common communication patterns (RPC/ReqResp, PubSub) over a message broker.
A message broker is a communication middleware responsible for routing messages to the
proper endpoints. Some examples of message brokers are: AMQP-based brokers (e.g. RabbitMQ),
Apache Kafka, MQTT brokers (e.g. Mosquito) and Redis.

Yes, Redis can also be used as a message broker for RPC and PubSub communication!!


# Installation


```bash
python setup.py install
```

or

```bash
pip install . --user
```

# Features
The purpose of this implementation is to provide an application-level of
communication patterns, such as RPCs, Topic-based PubSub, Preemptable Services
(aka Actions), Events etc.

## Transports
TODO

### AMQP
TODO

### Redis
TODO

## Endpoints
TODO

### RPCService
TODO

### RPCClient
TODO

### Publisher
TODO

### Subscriber
TODO

### ActionServer
TODO

### ActionClient
TODO

### EventEmitter
TODO

## Broker-to-broker (B2B) bridges

![bridges_1](./assets/2020-07-24-025901_713x483_scrot.png)

# Examples

Examples can be found at the `./examples` directory of this repo

# Tests

TODO

# Roadmap

TODO

# Credis

TODO
