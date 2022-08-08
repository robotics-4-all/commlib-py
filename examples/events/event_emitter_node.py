#!/usr/bin/env python

"""
EventEmitter example. Fire multiple events
"""

import sys
import time

from commlib.events import Event
from commlib.node import Node


if __name__ == '__main__':
    # Selecting broker type from arguments
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(node_name='simple_event_emitter',
                connection_params=conn_params,
                # heartbeat_uri='nodes.add_two_ints.heartbeat',
                debug=True)
    node.run()

    emitter = node.create_event_emitter()

    # An event is binded to a URI
    eventA = Event(name='TurnOnBedroomLights', uri='bedroom.lights.on')
    eventB = Event(name='TurnOffBedroomLights', uri='bedroom.lights.off')

    while True:
        emitter.send_event(eventA)
        time.sleep(2)
        emitter.send_event(eventB)
        time.sleep(2)
