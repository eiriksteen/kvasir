#!/bin/bash

# Check if exactly one argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <dev|prod>"
    echo "  dev  - Run development environment"
    echo "  prod - Run production environment"
    exit 1
fi

# Check if the argument is valid
if [ "$1" != "dev" ] && [ "$1" != "prod" ]; then
    echo "Error: Invalid argument '$1'"
    echo "Usage: $0 <dev|prod>"
    echo "  dev  - Run development environment"
    echo "  prod - Run production environment"
    exit 1
fi

# Run the appropriate docker command
if [ "$1" = "dev" ]; then
    echo "Starting development environment..."
    docker build -f docker/Dockerfile.dev -t project-server:dev .
    docker run -it --rm -p 8001:8001 project-server:dev
elif [ "$1" = "prod" ]; then
    echo "Starting production environment..."
    docker build -f docker/Dockerfile.prod -t project-server:prod .
    docker run -d -p 8001:8001 project-server:prod
fi
