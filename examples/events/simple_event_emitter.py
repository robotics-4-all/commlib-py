#!/usr/bin/env python

"""
EventEmitter example. Fire multiple events
"""

import sys
import time

from commlib.events import Event

if __name__ == '__main__':
    # Selecting broker type from arguments
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import ConnectionParameters, EventEmitter
    elif broker == 'amqp':
        from commlib.transports.amqp import ConnectionParameters, EventEmitter
    elif broker == 'mqtt':
        from commlib.transports.mqtt import ConnectionParameters, EventEmitter
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)

    conn_params = ConnectionParameters()
    emitter = EventEmitter(conn_params=conn_params, debug=True)

    # An event is binded to a URI
    eventA = Event(name='TurnOnBedroomLights', uri='bedroom.lights.on')
    eventB = Event(name='TurnOffBedroomLights', uri='bedroom.lights.off')

    while True:
        emitter.send_event(eventA)
        time.sleep(2)
        emitter.send_event(eventB)
        time.sleep(2)
