#!/usr/bin/env python

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
from commlib.bridges import (
    RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType
)
import time


def on_request(msg, meta):
    print('RPC Service Request')
    return msg


def on_message(nsg, meta):
    print('Data received at topic.')


def run_redis_to_redis_topic():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS-to-REDIS Topic Bridge Test...')
    print('-----------------------------------------------------------------')
    topic_name = 'test-topic3'
    sub_params = rcomm.ConnectionParameters(db=1)
    pub_params = rcomm.ConnectionParameters(db=2)
    br = TopicBridge(TopicBridgeType.REDIS_TO_REDIS, topic_name, sub_params,
                     pub_params)
    br.run()

    pub = rcomm.Publisher(conn_params=sub_params,
                          topic=topic_name)

    sub = rcomm.Subscriber(
        conn_params=pub_params,
        topic=topic_name,
        on_message=on_message
    )
    sub.run()

    count = 0
    pub.publish({'a': 1})
    while count < 5:
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


def run_amqp_to_amqp_topic():
    print()
    print('-----------------------------------------------------------------')
    print('Running AMQP-to-AMQP Topic Bridge Test...')
    print('-----------------------------------------------------------------')
    topic_name = 'test-topic4'
    sub_params = acomm.ConnectionParameters()
    pub_params = acomm.ConnectionParameters()
    br = TopicBridge(TopicBridgeType.AMQP_TO_AMQP, topic_name, sub_params,
                     pub_params)
    br.run()

    pub = acomm.Publisher(conn_params=sub_params,
                          topic=topic_name)

    sub = acomm.Subscriber(
        conn_params=pub_params,
        topic=topic_name,
        on_message=on_message
    )
    sub.run()

    count = 0
    pub.publish({'a': 1})
    while count < 5:
        time.sleep(1)
    br.stop()
    sub.stop()


def run_amqp_to_redis_topic():
    print()
    print('-----------------------------------------------------------------')
    print('Running AMQP-to-REDIS Topic Bridge Test...')
    print('-----------------------------------------------------------------')
    topic_name = 'test-topic2'
    sub_params = acomm.ConnectionParameters()
    pub_params = rcomm.ConnectionParameters()
    br = TopicBridge(TopicBridgeType.AMQP_TO_REDIS, topic_name, sub_params,
                     pub_params)
    br.run()

    pub = acomm.Publisher(conn_params=sub_params,
                          topic=topic_name)

    sub = rcomm.Subscriber(
        conn_params=pub_params,
        topic=topic_name,
        on_message=on_message
    )
    sub.run()

    count = 0
    while count < 5:
        pub.publish({'a': 1})
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


def run_redis_to_amqp_topic():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS-to-AMQP Topic Bridge Test...')
    print('-----------------------------------------------------------------')
    topic_name = 'test-topic'
    sub_params = rcomm.ConnectionParameters()
    pub_params = acomm.ConnectionParameters()
    br = TopicBridge(TopicBridgeType.REDIS_TO_AMQP, topic_name,
                     sub_params, pub_params)
    br.run()

    pub = rcomm.Publisher(conn_params=sub_params,
                          topic=topic_name)

    sub = acomm.Subscriber(
        conn_params=pub_params,
        topic=topic_name,
        on_message=on_message
    )
    sub.run()

    count = 0
    while count < 5:
        pub.publish({'a': 1})
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


def run_amqp_to_redis_rpc():
    print()
    print('-----------------------------------------------------------------')
    print('Running AMQP-to-REDIS RPC Bridge Test...')
    print('-----------------------------------------------------------------')
    rpc_name = 'testrpc1'
    client_params = rcomm.ConnectionParameters()
    server_params = acomm.ConnectionParameters()
    br = RPCBridge(RPCBridgeType.AMQP_TO_REDIS, rpc_name, client_params,
                   server_params)
    br.run()

    client = acomm.RPCClient(conn_params=server_params,
                             rpc_name=rpc_name)

    server = rcomm.RPCService(
        conn_params=client_params,
        rpc_name=rpc_name,
        on_request=on_request
    )
    server.run()

    count = 0
    while count < 5:
        resp = client.call({'a': 1})
        print(f'Response from REDIS RPC Service: {resp}')
        time.sleep(1)
        count += 1
    br.stop()
    server.stop()


def run_redis_to_amqp_rpc():
    print()
    print('-----------------------------------------------------------------')
    print('Running REDIS-to-AMQP RPC Bridge Test...')
    print('-----------------------------------------------------------------')
    rpc_name = 'testrpc2'
    client_params = acomm.ConnectionParameters()
    server_params = rcomm.ConnectionParameters()
    br = RPCBridge(RPCBridgeType.REDIS_TO_AMQP, rpc_name, client_params,
                   server_params)
    br.run()

    client = rcomm.RPCClient(conn_params=server_params,
                             rpc_name=rpc_name)

    server = acomm.RPCService(
        conn_params=client_params,
        rpc_name=rpc_name,
        on_request=on_request
    )
    server.run()

    count = 0
    while count < 5:
        resp = client.call({'a': 1})
        print(f'Response from AMQP RPC Service: {resp}')
        time.sleep(1)
        count += 1
    server.stop()
    br.stop()


if __name__ == '__main__':
    # run_amqp_to_amqp_topic()
    # run_redis_to_redis_topic()
    run_redis_to_amqp_topic()
    run_amqp_to_redis_topic()
    run_redis_to_amqp_rpc()
    run_amqp_to_redis_rpc()
    print('==========================================')
    print('================END OF TEST===============')
    print('==========================================')
