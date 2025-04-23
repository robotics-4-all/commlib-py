## Functionality

This example illustrates the multi-topic publish/subscribe capabilities of `commlib-py`. It comprises two scripts:

* **`Publisher (example5_publisher.py):`** This script establishes a publisher that transmits messages to two distinct topics, designated as `topic.a` and `topic.b`.

* **`Subscriber (example5_listener.py):`** This script establishes a subscriber that subscribes to a wildcard topic, specified as `topic.*`, thereby enabling it to receive messages from both `topic.a` and `topic.b`.

Both scripts are designed to be broker-agnostic, with support for Redis, AMQP (RabbitMQ), and MQTT.

## Example Breakdown

### Common Elements

* **Broker Selection:**

    * The scripts accept an optional command-line argument to specify the message broker. Permissible values are `redis`, `amqp`, or `mqtt`. If no argument is provided, the scripts default to `redis`.

    * The scripts then import the appropriate connection parameters class (`ConnectionParameters`) from the corresponding `commlib.transports` subpackage.

    ```python
    import sys
    from commlib.node import Node

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            broker = "redis"
        else:
            broker = str(sys.argv[1])
        if broker == "redis":
            from commlib.transports.redis import ConnectionParameters
        elif broker == "amqp":
            from commlib.transports.amqp import ConnectionParameters
        elif broker == "mqtt":
            from commlib.transports.mqtt import ConnectionParameters
        else:
            print("Not a valid broker-type was given!")
            sys.exit(1)
        conn_params = ConnectionParameters()
    ```

* **Node Creation:**

    * Both scripts create a `commlib.node.Node` object, which represents a communication node within the system.

    * The `ConnectionParameters` object is passed to the `Node` constructor to configure the connection to the message broker.

    * The `debug=True` argument enables debug logging.

    ```python
    node = Node(
        node_name="example5_publisher", connection_params=conn_params, debug=True
    )
    ```

### Publisher (`example5_publisher.py`)

* **Multi-Publisher Creation:**

    * A multi-publisher is created using `node.create_mpublisher()`. A standard publisher can only transmit to one topic. A multi-publisher allows the same publisher instance to transmit to multiple topics.

    ```python
    pub = node.create_mpublisher()
    ```

* **Message Publishing:**

    * The script enters an infinite loop, during which it performs the following actions:

        * Increments a counter.

        * Publishes a message containing the counter value to `topic.a`.

        * Publishes a message containing the counter value to `topic.b`.

        * Pauses execution for one second.

    ```python
    node.run()

    topicA = "topic.a"
    topicB = "topic.b"
    count = 0
    while True:
        count += 1
        pub.publish({"a": count}, topicA)
        pub.publish({"b": count}, topicB)
        time.sleep(1)
    ```

### Subscriber (`example5_listener.py`)

* **Pattern Subscriber Creation:**

    * A pattern subscriber is created using `node.create_psubscriber(topic="topic.*", on_message=on_message)`.

    * The argument `topic="topic.*"` specifies a wildcard topic pattern, which matches both `topic.a` and `topic.b`.

    * The `on_message` argument provides a callback function (`on_message`), which is invoked whenever a message is received on a matching topic.

    ```python
    def on_message(msg, topic):
        print(f"Message at topic <{topic}>: {msg}")

    # ... inside if __name__ == "__main__":
    sub = node.create_psubscriber(topic="topic.*", on_message=on_message)
    ```

* **Message Handling:**

    * The `on_message` function prints the received message and the topic on which it was received to the console.

    ```python
    def on_message(msg, topic):
        print(f"Message at topic <{topic}>: {msg}")
    ```

* **Running the Node:**

    * The `node.run_forever()` method initiates the node's event loop, which listens for incoming messages and dispatches them to the `on_message` callback function.

    ```python
    node.run_forever()
    ```
