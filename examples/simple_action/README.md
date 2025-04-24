## Action Server and Client Example

This example demonstrates the implementation of the Action pattern using `commlib-py`. It comprises two scripts:

* **Action Server:** Defines and runs an Action server that provides an action.
* **Action Client:** Defines and runs an Action client that calls the action provided by the Action server.

###   Action Server

The server script defines the structure of the goal, result, and feedback messages using `ActionMessage` classes: `ExampleAction`. It then defines a handler function (`on_goal`) that implements the action logic.

Key components:

* **Message Definitions:**

    ```python
    class ExampleAction(ActionMessage):
        class Goal(ActionMessage.Goal):
            target_cm: int = 0

        class Result(ActionMessage.Result):
            dest_cm: int = 0

        class Feedback(ActionMessage.Feedback):
            current_cm: int = 0
    ```

    These classes define the structure of the goal, result, and feedback messages for the action. The `Goal` class defines the input parameters (`target_cm`), the `Result` class defines the output (`dest_cm`), and the `Feedback` class defines the intermediate feedback messages (`current_cm`).

* **Handler Function:**

    ```python
    def on_goal(goal_h):
        c = 0
        res = ExampleAction.Result()
        while c < goal_h.data.target_cm:
            if goal_h.cancel_event.is_set():
                break
            goal_h.send_feedback(ExampleAction.Feedback(current_cm=c))
            c += 1
            time.sleep(1)
        res.dest_cm = c
        return res
    ```

    This function implements the core logic of the action. It takes a `goal_handle` as input, which provides access to the goal message and a cancellation event. The function iteratively processes the goal, sends feedback messages, and returns the result.

* **Server Setup:**

    ```python
    if __name__ == "__main__":
        action_name = "action_example"
        if len(sys.argv) > 1:
            broker_type = str(sys.argv[1])
        else:
            broker_type = "redis"
        if broker_type == "redis":
            from commlib.transports.redis import ConnectionParameters
        elif broker_type == "amqp":
            from commlib.transports.amqp import ConnectionParameters
        elif broker_type == "mqtt":
            from commlib.transports.mqtt import ConnectionParameters
        else:
            print("Not a valid broker-type was given!")
            sys.exit(1)
        conn_params = ConnectionParameters()

        node = Node(
            node_name="action_service_example_node",
            connection_params=conn_params,
        )
        node.create_action(msg_type=ExampleAction, action_name=action_name, on_goal=on_goal)

        node.run_forever()
    ```

    This code block:

    1.  Sets up the message broker connection.
    2.  Creates a `Node` instance.
    3.  Creates an action server using `node.create_action()`, specifying the message type, action name, and goal handler function.
    4.  Starts the node's event loop.

###   Action Client

The client script defines the same message classes as the server (`ExampleAction`) and then sets up an Action client to call the action provided by the Action server.

Key components:

* **Message Definitions:**

    ```python
    class ExampleAction(ActionMessage):
        class Goal(ActionMessage.Goal):
            target_cm: int = 0

        class Result(ActionMessage.Result):
            dest_cm: int = 0

        class Feedback(ActionMessage.Feedback):
            current_cm: int = 0
    ```

    These are identical to the definitions in the server script and are necessary for the client to correctly format requests and interpret responses.

* **Client Callbacks:**

    ```python
    def on_feedback(feedback):
        print(f"ActionClient <on-feedback> callback: {feedback}")


    def on_result(result):
        print(f"ActionClient <on-result> callback: {result}")


    def on_goal_reached(result):
        print(f"ActionClient <on-goal-reached> callback: {result}")
    ```

    These functions are callback functions that are called when the client receives feedback, a result, or a goal reached message from the server.

* **Client Setup and Action Call:**

    ```python
    if __name__ == "__main__":
        action_name = "action_example"
        if len(sys.argv) > 1:
            broker_type = str(sys.argv[1])
        else:
            broker_type = "redis"
        if broker_type == "redis":
            from commlib.transports.redis import ConnectionParameters
        elif broker_type == "amqp":
            from commlib.transports.amqp import ConnectionParameters
        elif broker_type == "mqtt":
            from commlib.transports.mqtt import ConnectionParameters
        else:
            print("Not a valid broker-type was given!")
            sys.exit(1)
        conn_params = ConnectionParameters()

        node = Node(
            node_name="action_client_example_node",
            connection_params=conn_params,
        )
        action_client = node.create_action_client(
            msg_type=ExampleAction,
            action_name=action_name,
            on_goal_reached=on_goal_reached,
            on_feedback=on_feedback,
            on_result=on_result,
        )
        node.run()
        goal_msg = ExampleAction.Goal(target_cm=5)
        action_client.send_goal(goal_msg)
        resp = action_client.get_result(wait=True)
        print(f"Action Result: {resp}")
        node.stop()
    ```

    This code block:

    1.  Sets up the message broker connection.
    2.  Creates a `Node` instance.
    3.  Creates an action client using `node.create_action_client()`, specifying the message type, action name, and callback functions.
    4.  Starts the node's event loop.
    5.  Creates an instance of the goal message.
    6.  Sends the goal message to the server using `action_client.send_goal()`.
    7.  Waits for the result using `action_client.get_result()`.
    8.  Prints the result.
