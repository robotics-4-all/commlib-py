#!/usr/bin/env python3

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


def test_as_dict():
    print('-----------------------------------------------------------------')
    print('Running <Message AS_DICT> Test...')
    print('-----------------------------------------------------------------')

    class TestRPCMessage(RPCMessage):
        @MessageClass
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        @MessageClass
        class Response(RPCMessage.Response):
            c: int = 0
            d: int = 0

    req = TestRPCMessage.Request()
    resp = TestRPCMessage.Response()
    assert req.as_dict() == {
        'header': {
            'seq': 0,
            'timestamp': -1,
            'node_id': '',
            'properties': {}
        },
        'a': 0,
        'b': 0
    }
    assert resp.as_dict() == {
        'header': {
            'seq': 0,
            'timestamp': -1,
            'node_id': '',
            'properties': {}
        },
        'c': 0,
        'd': 0
    }
    print(req)
    print(resp)


def test_from_dict():
    print('-----------------------------------------------------------------')
    print('Running <Message FROM_DICT> Test...')
    print('-----------------------------------------------------------------')

    class TestRPCMessage(RPCMessage):
        @MessageClass
        class Request(RPCMessage.Request):
            a: int = 0
            b: int = 0

        @MessageClass
        class Response(RPCMessage.Response):
            c: int = 0
            d: int = 0

    resp = TestRPCMessage.Response()

    resp_dict = {'c': 1, 'd': 2}
    resp.from_dict(resp_dict)
    print(resp)
    resp = TestRPCMessage.Response(**resp_dict)
    print(resp)

    resp_dict = {'a': 1, 'b': 2}
    try:
        resp.from_dict(resp_dict)
        print(resp)
    except Exception as exc:
        print(exc)
    try:
        resp = TestRPCMessage.Response(**resp_dict)
        print(resp)
    except Exception as exc:
        print(exc)


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
    test_as_dict()
    test_from_dict()
    test_rpc_message()
    test_pubsub_message()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
