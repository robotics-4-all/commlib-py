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
## Lazy imports are lazy internally
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
                transport_type=TransportType.REDIS,
                transport_connection_params=conn_params,
                debug=True)

    # Start the heartbeat thread. Heartbeat thread runs in the background
    # and sends heartbeat messages with a rate of 10hz.
    node.init_heartbeat_thread()

    # Create  an RPCService endpoint
    rpc = node.create_rpc(msg_type=AddTwoIntMessage,
                          rpc_name='testrpc',
                          on_request=on_request)
    # Start the RPC Service.
    rpc.run()
    # Create the RPC Client.
    rpc_c = node.create_rpc_client(msg_type=AddTwoIntMessage, rpc_name=rpc_name)

    # Wait until an exit signal is catched.
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

## Preemptable Services with Feedback (Actions)

Actions are [pre-emptable services](https://en.wikipedia.org/wiki/Preemption_(computing)) 
with support for asynchronous feedback publishing. This communication pattern
is used to implement services which can be stopped and can provide feedback data, such 
as the move command service of a robot.


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

![bridges_1](./assets/2020-07-24-025901_713x483_scrot.png)


**TODO**: Action bridges

# Examples

Examples can be found at the `./examples` directory of this repo

# Tests

TODO

# Roadmap

TODO

# Credis

TODO
