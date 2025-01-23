#!/usr/bin/env python3

import time
from commlib.node import Node
from commlib.transports.redis import ConnectionParameters as RedisConnectionParameters

IDS = []


class Test(Node):
    def __init__(self):
        super().__init__(
            connection_params=RedisConnectionParameters(),
            heartbeats=False,
            node_name="TestNode",
        )

        self.order_rpc_server = self.create_rpc(
            rpc_name = "skata.bank.action",
            on_request = self.order_action,
        )

        self.run(wait=True)

    def order_action(self, message):
        """
        Deposit callback
        """

        print(f"TestNode instance ID: {id(self)}")
        IDS.append(id(self))
        return {"id": id(self)}


cnode = Node(
    connection_params=RedisConnectionParameters(),
    heartbeats=False,
)
client = cnode.create_rpc_client(rpc_name = "skata.bank.action")
cnode.run(wait=True)

for i in range(0, 10):
    print(f"Running TestNode instance {i+1}")
    a = Test()

    resp = client.call({"action": "buy", "coin": "usdt", "price": 1, "amount": 10}, timeout=2)
    print(f"Response: {resp}")

    a.stop(wait=True)

print(IDS)
