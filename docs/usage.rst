=====
Usage
=====

#############################################
Create a Node with a simple RPC Service port.
#############################################

In this example we will create a node with a simple RPC endpoint that
takes as input two integer numbers and returns their sum.

.. code-block:: python

    from commlib.node import Node, TransportType
    from commlib.msg import RPCMessage, DataClass
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


    if __name__ == "__main__":
        node = Node(transport_type=TransportType.REDIS,
                    connection_params=ConnectionParameters())
        node.create_rpc(msg_type=AddTwoIntMessage,
                        rpc_name='testrpc',
                        on_request=on_request)
        node.init_heartbeat_thread()
        node.run()

The first thing is to import required components and instantiate a `Node` that
will connect to a specific broker.

.. code-block:: python

    import time
    from commlib.node import Node, TransportType
    from commlib.transports.redis import ConnectionParameters

    if __name__ == "__main__":
        node = Node(transport_type=TransportType.REDIS,
                    connection_params=ConnectionParameters())
        node.init_heartbeat_thread()
        node.run()
        while True:
            time.sleep(1)

As evident above, a `Node` provides the `run(self)` method to start running.
This is required to start all created Endpoints (Subscribers, RPC Services etc),
initiate the heartbeat thread and start logging. Althoug, a `run_forever(self)`
function also provides a blocking way of starting the `Node`.

.. code-block:: python

    from commlib.node import Node, TransportType
    from commlib.transports.redis import ConnectionParameters

    if __name__ == "__main__":
        node = Node(transport_type=TransportType.REDIS,
                    connection_params=ConnectionParameters())
        node.init_heartbeat_thread()
        node.run_forever()


If you want to use a transport different than Redis, simply import
`ConnectionParameters` from the relevant `transports` module.


.. code-block:: python

    from commlib.transports.redis import ConnectionParameters
    from commlib.transports.mqtt import ConnectionParameters
    from commlib.transports.amqp import ConnectionParameters


Commlib is a message-based communication middleware, so communication messages
are typed and  categorized into, PubSubMessages, RPCMessages, ActionMessages
and Events. So we need to define an RPC Message for our Service.


.. code-block:: python

    from commlib.msg import RPCMessage, DataClass

    class AddTwoIntMessage(RPCMessage):
        @DataClass
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        @DataClass
        class Response(RPCMessage.Response):
            c: int = 0


In the context of the current work an IDL has been developed for definition
and generation of Messages (https://github.com/robotics-4-all/comm-idl).
The relevant message definition using comm-idl would like like the below:

.. code-block:: javascript

    RPCMessage AddTwoIntMessage {
      a: int
      b: int
      ---
      c: int
    }

Now lets create our RPC Service. Simply use the `create_rpc` method of the
`Node` instance and define a callback function to be called `on_request`.

.. code-block:: python

    def on_request(msg):
        print(f'AddTwoInts Request: {msg}')
        resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
        return resp


    if __name__ == "__main__":
        node = Node(transport_type=TransportType.REDIS,
                    connection_params=ConnectionParameters())
        node.create_rpc(msg_type=AddTwoIntMessage,
                        rpc_name='add_two_ints',
                        on_request=on_request)
        node.init_heartbeat_thread()
        node.run_forever()

No need to manually start the RPCService instance, as this is handled by the
`run()` and `run_forever()` methods of the `Node`.