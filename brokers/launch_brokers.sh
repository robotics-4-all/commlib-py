#!/bin/bash

COMPOSE_FILE="docker-compose.yml"

function print_help {
  echo "Usage: ./launch_brokers.sh [broker1 broker2 ...]"
  echo ""
  echo "Available brokers:"
  echo "  emqx        EMQX MQTT Broker"
  echo "  mosquitto   Mosquitto MQTT Broker"
  echo "  redis       Redis Broker"
  echo "  dragonfly   Dragonfly Broker (Redis compatible)"
  echo "  rabbitmq    RabbitMQ (AMQP) Broker"
  echo "  kafka       Kafka Broker (includes Zookeeper)"
  echo "  all         Start all brokers (except conflicting ones)"
  echo ""
  echo "Note: emqx and mosquitto conflict on port 1883."
  echo "Note: redis and dragonfly conflict on port 6379."
}

if [ $# -eq 0 ] || [ "$1" == "help" ] || [ "$1" == "--help" ]; then
  print_help
  exit 0
fi

SERVICES=""

for arg in "$@"; do
  case $arg in
  emqx)
    SERVICES="$SERVICES emqx"
    ;;
  mosquitto)
    SERVICES="$SERVICES mosquitto"
    ;;
  redis)
    SERVICES="$SERVICES redis"
    ;;
  dragonfly)
    SERVICES="$SERVICES dragonfly"
    ;;
  rabbitmq)
    SERVICES="$SERVICES rabbitmq"
    ;;
  kafka)
    SERVICES="$SERVICES zookeeper kafka"
    ;;
  all)
    SERVICES="emqx redis rabbitmq zookeeper kafka"
    ;;
  *)
    echo "Unknown broker: $arg"
    print_help
    exit 1
    ;;
  esac
done

echo "Starting services: $SERVICES"
docker-compose -f $COMPOSE_FILE up -d $SERVICES
