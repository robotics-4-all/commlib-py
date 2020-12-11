#!/usr/bin/env python

import sys
import time

from commlib.events import Event


if __name__ == '__main__':
    if len(sys.argv) < 2:
        broker = 'redis'
    else:
        broker = str(sys.argv[1])
    if broker == 'redis':
        from commlib.transports.redis import (
            EventEmitter, ConnectionParameters
        )
    elif broker == 'amqp':
        from commlib.transports.amqp import (
            EventEmitter, ConnectionParameters
        )
    elif broker == 'mqtt':
        from commlib.transports.mqtt import (
            EventEmitter, ConnectionParameters
        )
    else:
        print('Not a valid broker-type was given!')
        sys.exit(1)

    conn_params = ConnectionParameters()
    emitter = EventEmitter(conn_params=conn_params, debug=True)

    eventA = Event(name='TurnOnBedroomLights', uri='bedroom.lights.on')
    eventB = Event(name='TurnOffBedroomLights', uri='bedroom.lights.off')

    emitter.send_event(eventA)
    time.sleep(2)
    emitter.send_event(eventB)
