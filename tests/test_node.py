#!/usr/bin/env python

"""Tests for `commlib` package."""

import time
import unittest
from typing import Optional
from commlib.msg import PubSubMessage, MessageHeader, RPCMessage
from commlib.node import Node, TransportType


class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2


class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0


class TestNode(unittest.TestCase):
    """Tests for `commlib` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_node_run_stop_mqtt_pubsub(self, iterations=2):
        from commlib.transports.mqtt import ConnectionParameters
        msg = SonarMessage()
        conn_params = ConnectionParameters()
        def on_message(msg):
            print(f'Received front sonar data: {msg}')
        count = 0
        while count < iterations:
            node = Node(node_name='sensors.sonar.front',
                        connection_params=conn_params,
                        debug=True)
            node.create_subscriber(msg_type=SonarMessage,
                                   topic='sensors.sonar.front',
                                   on_message=on_message)
            pub = node.create_publisher(msg_type=SonarMessage,
                                        topic='sensors.sonar.front')
            node.run()
            pub.publish(msg)
            time.sleep(1)
            node.stop()
            time.sleep(1)
            msg.range += 1
            count += 1

    def test_node_run_stop_mqtt_rpc(self, iterations=1):
        from commlib.transports.redis import ConnectionParameters
        msg = AddTwoIntMessage.Request()
        conn_params = ConnectionParameters()
        def add_two_int_handler(msg):
            print(f'Request Message: {msg.__dict__}')
            resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
            return resp

        count = 0
        while count < iterations:
            node = Node(node_name='sensors.sonar.front',
                        connection_params=conn_params,
                        debug=True)
            node.create_rpc(msg_type=AddTwoIntMessage,
                            rpc_name='add_two_ints_node.add_two_ints',
                            on_request=add_two_int_handler)
            rpc = node.create_rpc_client(
                msg_type=AddTwoIntMessage,
                rpc_name='add_two_ints_node.add_two_ints'
            )
            node.run()
            rpc.call(msg)
            time.sleep(1)
            node.stop()
            time.sleep(1)
            count += 1
            msg.a += 1
            msg.b += 1
        self.assertEqual(count, iterations)

    def test_node_run_stop_redis_pubsub(self, iterations=1):
        from commlib.transports.redis import ConnectionParameters
        msg = SonarMessage()
        conn_params = ConnectionParameters()
        def on_message(msg):
            print(f'Received front sonar data: {msg}')
        count = 0
        while count < iterations:
            node = Node(node_name='sensors.sonar.front',
                        connection_params=conn_params,
                        debug=True)
            node.create_subscriber(msg_type=SonarMessage,
                                   topic='sensors.sonar.front',
                                   on_message=on_message)
            pub = node.create_publisher(msg_type=SonarMessage,
                                        topic='sensors.sonar.front')
            node.run()
            pub.publish(msg)
            msg.range += 1
            time.sleep(1)
            node.stop()
            time.sleep(1)
            count += 1
        self.assertEqual(count, iterations)

    def test_node_run_stop_redis_rpc(self, iterations=1):
        from commlib.transports.redis import ConnectionParameters
        msg = AddTwoIntMessage.Request()
        conn_params = ConnectionParameters()
        def add_two_int_handler(msg):
            print(f'Request Message: {msg.__dict__}')
            resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
            return resp

        count = 0
        while count < iterations:
            node = Node(node_name='sensors.sonar.front',
                        connection_params=conn_params,
                        debug=True)
            node.create_rpc(msg_type=AddTwoIntMessage,
                            rpc_name='add_two_ints_node.add_two_ints',
                            on_request=add_two_int_handler)
            rpc = node.create_rpc_client(
                msg_type=AddTwoIntMessage,
                rpc_name='add_two_ints_node.add_two_ints'
            )
            node.run()
            rpc.call(msg)
            time.sleep(1)
            node.stop()
            time.sleep(1)
            count += 1
            msg.a += 1
            msg.b += 1
        self.assertEqual(count, iterations)
