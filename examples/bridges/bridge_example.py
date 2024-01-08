#!/usr/bin/env python

import time

import commlib.transports.mqtt as mcomm
import commlib.transports.redis as rcomm
from commlib.bridges import RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType


def on_request(msg):
    print(f"[Broker-B] - RPC Service received request: {msg}")
    c = msg["a"] + msg["b"]
    resp = {"c": c}
    return resp


def on_message(msg):
    print(f"[Broker-B] - Data received at topic - {msg}")


def redis_to_mqtt_rpc_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()
    bA_uri = "ops.start_navigation"
    bB_uri = "thing.robotA.ops.start_navigation"
    br = RPCBridge(
        RPCBridgeType.REDIS_TO_MQTT,
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params,
        debug=False,
    )
    br.run()

    ## For Testing Bridge ------------------>
    ## BrokerA
    client = rcomm.RPCClient(conn_params=bA_params, rpc_name=bA_uri, debug=False)

    ## BrokerB
    server = mcomm.RPCService(
        conn_params=bB_params, rpc_name=bB_uri, on_request=on_request, debug=False
    )
    server.run()
    time.sleep(1)

    count = 0
    req_msg = {"a": 1, "b": 2}
    while count < 5:
        req_msg["a"] = count
        resp = client.call(req_msg)
        print(f"[Broker-A Client] - Response from AMQP RPC Service: {resp}")
        time.sleep(1)
        count += 1
    server.stop()
    ## <-------------------------------------
    br.stop()


def redis_to_mqtt_topic_bridge():
    """
    [Broker A] ------------> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()
    bA_uri = "sonar.front"
    bB_uri = "thing.robotA.sensors.sonar.font"
    br = TopicBridge(
        TopicBridgeType.REDIS_TO_MQTT,
        from_uri=bA_uri,
        to_uri=bB_uri,
        from_broker_params=bA_params,
        to_broker_params=bB_params,
        debug=False,
    )
    br.run()

    pub = rcomm.Publisher(conn_params=bA_params, topic=bA_uri, debug=False)

    sub = mcomm.Subscriber(conn_params=bB_params, topic=bB_uri, on_message=on_message)
    sub.run()

    count = 0
    msg = {"a": 1}
    while count < 5:
        msg["a"] = count
        pub.publish(msg)
        time.sleep(1)
        count += 1
    br.stop()
    sub.stop()


if __name__ == "__main__":
    redis_to_mqtt_rpc_bridge()
    redis_to_mqtt_topic_bridge()
