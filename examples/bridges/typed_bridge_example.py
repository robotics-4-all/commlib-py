#!/usr/bin/env python

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
from commlib.bridges import (
    RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType
)
from commlib.msg import PubSubMessage, RPCMessage
import time


class TopicMessage(PubSubMessage):
    a: int = 0


class ExampleRPCMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


def on_request(msg):
    print(f'[Broker-B] - RPC Service received request: {msg}')
    resp = ExampleRPCMessage.Response(c=msg.a+msg.b)
    return resp


def on_message(msg):
    print(f'[Broker-B] - Data received at topic - {msg}')


def redis_to_amqp_topic_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = acomm.ConnectionParameters()
    bA_uri = 'rpc.bridge.testA'
    bB_uri = 'rpc.bridge.testB'
    br = TopicBridge(TopicBridgeType.REDIS_TO_AMQP,
                     TopicMessage, bA_uri, bB_uri,
                     bA_params, bB_params, debug=False)
    br.run()

    pub = rcomm.Publisher(conn_params=bA_params,
                          msg_type=TopicMessage,
                          topic=bA_uri)

    sub = acomm.Subscriber(
        conn_params=bB_params,
        msg_type=TopicMessage,
        topic=bB_uri,
        on_message=on_message
    )
    sub.run()

    count = 0
    msg = TopicMessage()
    while count < 5:
        msg.a = count
        pub.publish(msg)
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


def redis_to_amqp_rpc_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = acomm.ConnectionParameters()
    bA_uri = 'rpc.bridge.testA'
    bB_uri = 'rpc.bridge.testB'
    br = RPCBridge(btype=RPCBridgeType.REDIS_TO_AMQP,
                   msg_type=ExampleRPCMessage,
                   from_uri=bA_uri,
                   to_uri=bB_uri,
                   from_broker_params=bA_params,
                   to_broker_params=bB_params,
                   debug=False)
    br.run()


    ## For Testing Bridge ------------------>
    ## BrokerA
    client = rcomm.RPCClient(msg_type=ExampleRPCMessage,
                             conn_params=bA_params, rpc_name=bA_uri)

    ## BrokerB
    server = acomm.RPCService(
        msg_type=ExampleRPCMessage,
        conn_params=bB_params,
        rpc_name=bB_uri,
        on_request=on_request
    )
    server.run()

    count = 0
    req_msg = ExampleRPCMessage.Request()
    while count < 5:
        req_msg.a = count
        resp = client.call(req_msg)
        print(f'[Broker-A Client] - Response from AMQP RPC Service: {resp}')
        time.sleep(1)
        count += 1
    server.stop()
    ## <-------------------------------------
    br.stop()


if __name__ == '__main__':
    redis_to_amqp_rpc_bridge()
    redis_to_amqp_topic_bridge()
