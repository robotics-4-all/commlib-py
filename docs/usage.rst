=====
Usage
=====

Create a Node with a simple RPC Service port::

    from commlib.node import Node, TransportType
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
        node.run()
