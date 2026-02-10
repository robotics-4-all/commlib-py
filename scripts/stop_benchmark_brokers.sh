#!/bin/bash
# Stop and remove benchmark brokers

echo "Stopping benchmark brokers..."

docker stop benchmark-mqtt benchmark-redis benchmark-amqp 2>/dev/null || true
docker rm benchmark-mqtt benchmark-redis benchmark-amqp 2>/dev/null || true

echo "✓ Brokers stopped and removed"
