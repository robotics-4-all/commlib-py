#!/usr/bin/env python

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
from commlib.bridges import (
    RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType, MTopicBridge
)
from commlib.msg import PubSubMessage, RPCMessage, DataClass
import time


def on_message(msg, topic):
    print(f'[Broker-B] - Data received at topic - {topic}:{msg}')


def redis_to_amqp_topic_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = acomm.ConnectionParameters()
    bA_uri = 'sensors.*'
    bB_namespace = 'myrobot'
    br = MTopicBridge(TopicBridgeType.REDIS_TO_AMQP,
                      from_uri=bA_uri, to_namespace=bB_namespace,
                      from_broker_params=bA_params,
                      to_broker_params=bB_params,
                      debug=False)
    br.run()

    pub = rcomm.MPublisher(conn_params=bA_params,
                           debug=False)

    sub = acomm.PSubscriber(
        conn_params=bB_params,
        topic=f'{bB_namespace}.{bA_uri}',
        on_message=on_message
    )
    sub.run()

    count = 0
    msg1 = {
        'a': 1
    }
    msg2 = {
        'b': 1
    }
    p1 = 'sensors.sonar.front'
    p2 = 'sensors.ir.rear'
    while count < 5:
        msg1['a'] = count
        msg2['b'] = count
        pub.publish(msg1, p1)
        pub.publish(msg2, p2)
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


def amqp_to_redis_topic_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = acomm.ConnectionParameters()
    bB_params = rcomm.ConnectionParameters()
    bA_uri = 'sensors.*'
    bB_namespace = 'myrobot'
    br = MTopicBridge(TopicBridgeType.AMQP_TO_REDIS,
                      from_uri=bA_uri, to_namespace=bB_namespace,
                      from_broker_params=bA_params,
                      to_broker_params=bB_params,
                      debug=False)
    br.run()

    pub = acomm.MPublisher(conn_params=bA_params,
                           debug=False)

    sub = rcomm.PSubscriber(
        conn_params=bB_params,
        topic=f'{bB_namespace}.{bA_uri}',
        on_message=on_message
    )
    sub.run()

    count = 0
    msg1 = {
        'a': 1
    }
    msg2 = {
        'b': 1
    }
    p1 = 'sensors.sonar.front'
    p2 = 'sensors.ir.rear'
    while count < 5:
        msg1['a'] = count
        msg2['b'] = count
        pub.publish(msg1, p1)
        pub.publish(msg2, p2)
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()

if __name__ == '__main__':
    redis_to_amqp_topic_bridge()
    amqp_to_redis_topic_bridge()
