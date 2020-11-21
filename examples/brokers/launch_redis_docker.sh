#!/usr/bin/env bash

docker run --rm -it --hostname redis -v redis.conf:/usr/local/etc/redis/redis.conf -p 6379:6379 redis
