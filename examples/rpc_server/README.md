## RPC Server and Client Example

This example demonstrates the implementation of Remote Procedure Call (RPC) functionality using `commlib-py`. It comprises two scripts:

* **RPC Server (`RPC Server Example`):** Defines and runs an RPC server that provides two services:
    * `add_two_ints`: Adds two integers.
    * `multiply_ints`: Multiplies two integers.
* **RPC Client (`RPC Client Example`):** Defines and runs an RPC client that calls the services provided by the RPC server.

### RPC Server (`RPC Server Example`)

The server script defines the structure of the request and response messages using `RPCMessage` classes: `AddTwoIntMessage` and `MultiplyIntMessage`.  It then defines handler functions (`add_two_int_handler` and `multiply_int_handler`) that implement the service logic.



* **Message Definitions:**
    ```python
    class AddTwoIntMessage(RPCMessage):
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        class Response(RPCMessage.Response):
            c: int = 0

    class MultiplyIntMessage(RPCMessage):
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        class Response(RPCMessage.Response):
            c: int = 0
    ```
    These classes define the structure of the request and response messages for each RPC service.  The `Request` class defines the input parameters (`a`, `b`), and the `Response` class defines the output (`c`).

* **Handler Functions:**
    ```python
    def multiply_int_handler(msg):
        print(f"Request Message: {msg}")
        resp = MultiplyIntMessage.Response(c=msg.a * msg.b)
        return resp

    def add_two_int_handler(msg):
        print(f"Request Message: {msg}")
        resp = AddTwoIntMessage.Response(c=msg.a + msg.b)
        return resp
    ```
    These functions implement the core logic of the RPC services.  They take the request message as input and return the corresponding response message.

* **Server Setup:**
  ```python
  if __name__ == "__main__":
      # ... (Broker selection)

      node = Node(
          node_name="myRpcServer",
          connection_params=conn_params,
          heartbeats=False,
          debug=True,
      )

      base_uri = "rpcserver.example.com"
      svc_map = {
          "add_two_ints": (add_two_int_handler, AddTwoIntMessage),
          "multiply_ints": (multiply_int_handler, MultiplyIntMessage),
      }

      # Create the RPC server. Preregister the RPC endpoints via the svc_map.
      # The svc_map is a dictionary where the key is the RPC name and the value is a tuple
      # containing the handler function and the message type.
      # The base_uri is the base URI for the RPC server.
      # The workers parameter specifies the number of worker threads to use for handling requests.
      server = node.create_rpc_server(base_uri=base_uri, svc_map=svc_map, workers=4)
      # Register the RPC endpoints with the server.
      # server.register_endpoint("multiply_ints", multiply_int_handler, MultiplyIntMessage)
      server.run_forever()
  ```
  This code block:
  1.  Sets up the message broker connection.
  2.  Creates a `Node` instance.
  3.  Defines a service map (`svc_map`) that maps RPC service names to their handler functions and message types.
  4.  Creates an `rpc_server` using `node.create_rpc_server()`, specifying the base URI, service map, and number of worker threads.
  5.  Registers an additional endpoint.
  6.  Starts the server's event loop.

### RPC Client (`RPC Client Example`)

The client script defines the same message classes as the server (`AddTwoIntMessage` and `MultiplyIntMessage`) and then sets up RPC clients to call the corresponding services.

Key components:

* **Message Definitions:**
    ```python
    class AddTwoIntMessage(RPCMessage):
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        class Response(RPCMessage.Response):
            c: int = 0

    class MultiplyIntMessage(RPCMessage):
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        class Response(RPCMessage.Response):
            c: int = 0
    ```
    These are identical to the definitions in the server script and are necessary for the client to correctly format requests and interpret responses.

* **Client Setup and Calls:**
    ```python
    if __name__ == "__main__":
        # ... (Broker selection)

        node = Node(
            node_name="myclient",
            connection_params=conn_params,
            debug=True,
        )

        rpc_a = node.create_rpc_client(
            msg_type=AddTwoIntMessage, rpc_name="rpcserver.test.add_two_ints"
        )
        rpc_b = node.create_rpc_client(
            msg_type=MultiplyIntMessage, rpc_name="rpcserver.test.multiply_ints"
        )

        node.run()

        msg_a = AddTwoIntMessage.Request()
        msg_b = MultiplyIntMessage.Request()

        while True:
            resp_a = rpc_a.call(msg_a)
            print(f'SUM: {msg_a.a} + {msg_a.b} = {resp_a}')
            msg_a.a += 1
            msg_a.b += 1
            resp_b = rpc_b.call(msg_b)
            print(f'MULTIPLY: {msg_b.a} * {msg_b.b} = {resp_b}')
            msg_b.a += 1
            msg_b.b += 1
            time.sleep(1)
    ```
    This code block:
    1.  Sets up the message broker connection.
    2.  Creates a `Node` instance.
    3.  Creates RPC clients (`rpc_a`, `rpc_b`) using `node.create_rpc_client()`, specifying the message type and RPC service name.
    4.  Starts the node's event loop.
    5.  Creates instances of the request messages.
    6.  Enters an infinite loop to continuously call the RPC services using `rpc_a.call()` and `rpc_b.call()`.
    7.  Prints the results and increments the request parameters.
