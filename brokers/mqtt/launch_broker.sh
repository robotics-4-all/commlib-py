#!/usr/bin/env bash

BROKER=${1:-"emqx"}

if [ "$BROKER" == "emqx" ]; then
    echo "Starting EMQX broker..."
    docker-compose up emqx
elif [ "$BROKER" == "mosquitto" ]; then
    echo "Starting Mosquitto broker..."
    docker-compose up mosquitto
else
    echo "Unknown broker: $BROKER"
    echo "Usage: ./launch_broker.sh [emqx|mosquitto]"
    exit 1
fi
