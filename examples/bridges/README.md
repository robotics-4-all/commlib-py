## Simple Bridge Example

This example demonstrates how to create bridges between different message brokers (Redis and AMQP) using `commlib-py` to forward both topic-based messages and RPC calls.

The example defines two primary functions:

* `redis_to_amqp_topic_bridge()`: Creates a topic bridge that forwards messages from a Redis topic to an AMQP topic.
* `redis_to_amqp_rpc_bridge()`: Creates an RPC bridge that forwards RPC calls from a Redis RPC client to an AMQP RPC service.

###   `redis_to_amqp_topic_bridge()`

This function sets up a topic bridge that forwards messages from a publisher on a Redis broker to a subscriber on an AMQP broker.

```python
def redis_to_amqp_topic_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = acomm.ConnectionParameters()
    bA_uri = "rpc.bridge.testA"
    bB_uri = "rpc.bridge.testB"

    # Create and run the bridge
    br = TopicBridge(TopicMessage, bA_uri, bB_uri, bA_params, bB_params)
    br.run()

    ## For Testing Bridge ------------------>
    pub = rcomm.Publisher(conn_params=bA_params, msg_type=TopicMessage, topic=bA_uri)

    # Create and run the subscriber
    sub = acomm.Subscriber(
        conn_params=bB_params,
        msg_type=TopicMessage,
        topic=bB_uri,
        on_message=on_message,
    )
    sub.run()

    count = 0
    msg = TopicMessage()
    # Publish messages to the topic on Broker A and receive them on Broker B
    # with the subscriber
    while count < 5:
        msg.a = count
        pub.publish(msg)
        time.sleep(1)
        count += 1
    sub.stop()
    ## <-------------------------------------
    br.stop()
```


###   `redis_to_amqp_topic_bridge()`

This function sets up a topic bridge that forwards messages from a publisher on a Redis broker to a subscriber on an AMQP broker.

```python
def redis_to_amqp_rpc_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = acomm.ConnectionParameters()
    bA_uri = "rpc.bridge.testA"
    bB_uri = "rpc.bridge.testB"
    br = RPCBridge(
        btype=RPCBridgeType.REDIS_TO_AMQP,
        msg_type=ExampleRPCMessage,
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params,
        debug=False,
    )
    br.run()

    ## For Testing Bridge ------------------>
    ## BrokerA
    client = rcomm.RPCClient(
        msg_type=ExampleRPCMessage, conn_params=bA_params, rpc_name=bA_uri
    )

    # Create
    server = acomm.RPCService(
        msg_type=ExampleRPCMessage,
        conn_params=bB_params,
        rpc_name=bB_uri,
        on_request=on_request,
    )
    server.run()

    count = 0
    req_msg = ExampleRPCMessage.Request()
    while count < 5:
        req_msg.a = count
        resp = client.call(req_msg)
        print(f"[Broker-A Client] - Response from AMQP RPC Service: {resp}")
        time.sleep(1)
        count += 1
    server.stop()
    ## <-------------------------------------
    br.stop()
```
