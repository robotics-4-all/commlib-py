#!/bin/bash
# Start all brokers needed for benchmarks

echo "Starting brokers for benchmarks..."

# Clean up existing containers if they exist
echo "Cleaning up existing containers..."
docker rm -f benchmark-mqtt benchmark-redis benchmark-amqp 2>/dev/null || true
echo ""

# MQTT (Mosquitto)
echo "Starting MQTT broker..."
docker run -d --name benchmark-mqtt \
    -p 1883:1883 \
    eclipse-mosquitto \
    mosquitto -c /mosquitto-no-auth.conf

# Redis
echo "Starting Redis broker..."
docker run -d --name benchmark-redis \
    -p 6379:6379 \
    redis:latest

# AMQP (RabbitMQ)
echo "Starting AMQP broker..."
docker run -d --name benchmark-amqp \
    -p 5672:5672 \
    -p 15672:15672 \
    rabbitmq:3-management

echo ""
echo "Waiting for brokers to be ready..."
sleep 5

echo ""
echo "✓ Brokers started:"
echo "  - MQTT:  localhost:1883"
echo "  - Redis: localhost:6379"
echo "  - AMQP:  localhost:5672"
echo "  - RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo ""
echo "Run benchmarks:"
echo "  python benchmark/bench_mqtt_real.py"
echo "  python benchmark/bench_redis_real.py"
echo "  python benchmark/bench_amqp_real.py"
echo ""
echo "Or run as integration tests:"
echo "  make test-benchmarks-smoke  # Quick (~30s)"
echo "  make test-benchmarks        # Full (~2-5min)"
