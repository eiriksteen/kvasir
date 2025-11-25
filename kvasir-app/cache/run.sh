#!/bin/bash

# Build and run Redis Docker container
echo "Building Redis container..."
docker build -t synesis-redis-cache .

echo "Starting Redis container on port 6379..."
docker run -d \
    --name synesis-redis-cache \
    -p 6379:6379 \
    --restart unless-stopped \
    synesis-redis-cache

echo "Redis container started successfully, available at localhost:6379"
