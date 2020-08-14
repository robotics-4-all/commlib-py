#!/usr/bin/env python

from commlib.msg import as_dict, make_msgclass, is_msgclass
from commlib.msg import MessageClass, MessageField
from commlib.msg import HeaderMessage, RPCMessage, PubSubMessage
import time


def test_header_message():
    print('-----------------------------------------------------------------')
    print('Running <Header Message> Test...')
    print('-----------------------------------------------------------------')
    header = HeaderMessage()
    header.seq = 1
    header.timestamp = 12312451231231
    header.node_id = 'test-node'
    header.properties = {'a': 1}


def test_rpc_message():
    print('-----------------------------------------------------------------')
    print('Running <RPC Message> Test...')
    print('-----------------------------------------------------------------')

    class TestRPCMessage(RPCMessage):
        @MessageClass
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        @MessageClass
        class Response(RPCMessage.Response):
            a: int = 0
            b: int = 0

    req = TestRPCMessage.Request()
    resp = TestRPCMessage.Response()
    print(req)
    print(resp)


def test_pubsub_message():
    print('-----------------------------------------------------------------')
    print('Running <PubSub Message> Test...')
    print('-----------------------------------------------------------------')

    @MessageClass
    class TestPubSubMessage(PubSubMessage):
        a: int = 1
        b: str = 'aaa'

    msg = TestPubSubMessage()
    print(msg)


if __name__ == '__main__':
    test_rpc_message()
    test_pubsub_message()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
