#!/bin/bash

# Check if at least one argument is provided
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <dev|prod> [build]"
    echo "  dev  - Run development environment"
    echo "  prod - Run production environment"
    echo "  build - Optional: Rebuild Docker images before starting"
    exit 1
fi

# Check if the first argument is valid
if [ "$1" != "dev" ] && [ "$1" != "prod" ]; then
    echo "Error: Invalid argument '$1'"
    echo "Usage: $0 <dev|prod> [build]"
    echo "  dev  - Run development environment"
    echo "  prod - Run production environment"
    echo "  build - Optional: Rebuild Docker images before starting"
    exit 1
fi

# Check if second argument is "build" (if provided)
if [ $# -eq 2 ] && [ "$2" != "build" ]; then
    echo "Error: Invalid second argument '$2'"
    echo "Usage: $0 <dev|prod> [build]"
    echo "  dev  - Run development environment"
    echo "  prod - Run production environment"
    echo "  build - Optional: Rebuild Docker images before starting"
    exit 1
fi

# Check if sandbox image exists, build if it doesn't
if [ -z "$(docker images -q sandbox:latest)" ]; then
    echo "Sandbox image not found, building it..."
    docker build -f sandbox/Dockerfile -t sandbox:latest ..
    if [ $? -ne 0 ]; then
        echo "Error: Failed to build sandbox image"
        exit 1
    fi
    echo "Sandbox image built successfully."
fi

# Run the appropriate docker-compose command
if [ "$1" = "dev" ]; then
    if [ "$2" = "build" ]; then
        echo "Building and starting development environment..."
        docker compose -f docker/docker-compose-dev.yaml -p project up --build
    else
        echo "Starting development environment..."
        docker compose -f docker/docker-compose-dev.yaml -p project up
    fi
elif [ "$1" = "prod" ]; then
    if [ "$2" = "build" ]; then
        echo "Building and starting production environment..."
        docker compose -f docker/docker-compose.yaml -p project up --build
    else
        echo "Starting production environment..."
        docker compose -f docker/docker-compose.yaml -p project up
    fi
fi
