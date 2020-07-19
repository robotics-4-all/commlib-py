#!/usr/bin/env python

from commlib.transports.amqp import (
    Publisher, Subscriber, ConnectionParameters, AMQPConnection)
import time
from threading import Thread


HB_TIMEOUT = 2
SLEEP_MULTIPLIER = 5
ITERATIONS = 3
TOPIC_NAME = 'testtopic'
num_clients = 10
conn_params = ConnectionParameters()
conn_params.credentials.username = 'testuser'
conn_params.credentials.password = 'testuser'
conn_params.host = 'localhost'
conn_params.port = 8076
conn_params.heartbeat_timeout = HB_TIMEOUT  ## Seconds


def thread_runner(p):
    data = {'msg': 'Sent from Child Thread.'}
    counter = 0
    while counter < ITERATIONS:
        p.publish(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1


def sub_callback(msg, meta):
    print(msg)
    return msg


def create_publishers(n, topic, connection):
    l = [Publisher(connection=connection, topic=topic) for i in range(n)]
    return l


def test_multiple_publishers():
    print('[*] - Running <PubSub Multiple Publishers> test')
    print('[*] - Configuration:')
    print(f'[*] - Number of Clients: {num_clients}')
    print('=================================================================')
    s1 = Subscriber(conn_params=conn_params,
                    topic=TOPIC_NAME,
                    on_message=sub_callback)
    s1.run()
    time.sleep(1)
    p1 = Publisher(conn_params=conn_params,
                   topic=TOPIC_NAME)
    p1.run()
    t = Thread(target=thread_runner, args=(p1,))
    t.daemon = True
    t.start()

    p_list = [Publisher(conn_params=conn_params, topic=TOPIC_NAME) \
              for i in range(num_clients)]
    data = {'msg': 'Send from main Thread'}
    counter = 0
    while counter < ITERATIONS:
        for p in p_list:
            p.publish(data)
        time.sleep(1)
        counter += 1
    print('[*] - Finished Test!')
    print('=================================================================')


def test_multiple_publishers_shared_connection():
    print('[*] - Running <PubSub Shared Connection> test')
    print('[*] - Configuration:')
    print(f'[*] - Number of Clients: {num_clients}')
    print('=================================================================')
    s1 = Subscriber(conn_params=conn_params,
                    topic=TOPIC_NAME,
                    on_message=sub_callback)
    s1.run()
    time.sleep(1)
    conn = AMQPConnection(conn_params)
    p1 = Publisher(connection=conn,
                   topic=TOPIC_NAME)
    t = Thread(target=thread_runner, args=(p1,))
    t.daemon = True
    t.start()

    p_list = create_publishers(num_clients, TOPIC_NAME, conn)

    conn.detach_amqp_events_thread()

    data = {'msg': 'Send from main Thread'}
    counter = 0
    while counter < ITERATIONS:
        for p in p_list:
            p.publish(data)
        time.sleep(1)
        counter += 1
    print('[*] - Finished Test!')
    print('=================================================================')


def test_simple_publishers():
    print('[*] - Running <Heartbeat Timeout> test with simple connection Publisher')
    print('[*] - Configuration:')
    print(f'[*] - Heartbeat Timeout: {HB_TIMEOUT}')
    print(f'[*] - Sleep Multiplier: {SLEEP_MULTIPLIER}')
    print(f'[*] - Iterations: {ITERATIONS}')
    print('=================================================================')
    s = Subscriber(conn_params=conn_params,
                   topic=TOPIC_NAME,
                   on_message=sub_callback)
    s.run()
    time.sleep(1)
    p = Publisher(conn_params=conn_params,
                  topic=TOPIC_NAME)
    t = Thread(target=thread_runner, args=(p,))
    t.daemon = True
    t.start()
    data = {'msg': 'Sent from Main Thread.'}
    counter = 0
    while counter < ITERATIONS:
        p.publish(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1
    s.stop()
    print('[*] - Finished Heartbeat Timeout Test!')
    print('=================================================================')


def test_shared_connection_publishers():
    print('[*] - Running <Heartbeat Timeout> test with Shared Connection Publisher')
    print('[*] - Configuration:')
    print(f'[*] - Heartbeat Timeout: {HB_TIMEOUT}')
    print(f'[*] - Sleep Multiplier: {SLEEP_MULTIPLIER}')
    print(f'[*] - Iterations: {ITERATIONS}')
    print('=================================================================')
    s = Subscriber(conn_params=conn_params,
                   topic=TOPIC_NAME,
                   on_message=sub_callback)
    s.run()
    time.sleep(1)
    conn = AMQPConnection(conn_params)
    p = Publisher(connection=conn,
                  topic=TOPIC_NAME)
    t = Thread(target=thread_runner, args=(p,))
    t.daemon = True
    t.start()
    conn.detach_amqp_events_thread()
    data = {'msg': 'Sent from Main Thread.'}
    counter = 0
    while counter < ITERATIONS:
        p.publish(data)
        time.sleep(HB_TIMEOUT * SLEEP_MULTIPLIER)
        counter += 1
    s.stop()
    print('[*] - Finished Heartbeat Timeout Test!')
    print('=================================================================')


def test_stop_subscriber():
    print('[*] - Running <Heartbeat Timeout> test with Shared Connection client')
    print('[*] - Configuration:')
    print(f'[*] - Heartbeat Timeout: {HB_TIMEOUT}')
    print(f'[*] - Sleep Multiplier: {SLEEP_MULTIPLIER}')
    print(f'[*] - Iterations: {ITERATIONS}')
    print('=================================================================')
    counter = 0
    while counter < ITERATIONS:
        s = Subscriber(conn_params=conn_params,
                      topic=TOPIC_NAME,
                      on_message=sub_callback)
        s.run()
        time.sleep(1)
        s.stop()
        time.sleep(1)
        counter += 1


if __name__ == '__main__':
    test_stop_subscriber()
    test_multiple_publishers()
    test_multiple_publishers_shared_connection()
    test_simple_publishers()
    test_shared_connection_publishers()
