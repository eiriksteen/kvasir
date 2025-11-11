#!/bin/bash

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <dev|prod> [build] [-d]"
    echo "  dev    - Run development environment"
    echo "  prod   - Run production environment"
    echo "  build  - Optional: Rebuild Docker images before starting"
    echo "  -d     - Optional: Run in detached mode"
    exit 1
fi

# Parse arguments
ENV=""
BUILD_FLAG=""
DETACHED_FLAG=""

for arg in "$@"; do
    case "$arg" in
        dev|prod)
            if [ -n "$ENV" ]; then
                echo "Error: Multiple environment arguments provided"
                exit 1
            fi
            ENV="$arg"
            ;;
        build)
            BUILD_FLAG="--build"
            ;;
        -d)
            DETACHED_FLAG="-d"
            ;;
        *)
            echo "Error: Invalid argument '$arg'"
            echo "Usage: $0 <dev|prod> [build] [-d]"
            echo "  dev    - Run development environment"
            echo "  prod   - Run production environment"
            echo "  build  - Optional: Rebuild Docker images before starting"
            echo "  -d     - Optional: Run in detached mode"
            exit 1
            ;;
    esac
done

# Check if environment is specified
if [ -z "$ENV" ]; then
    echo "Error: Environment (dev or prod) must be specified"
    echo "Usage: $0 <dev|prod> [build] [-d]"
    exit 1
fi

# Run the appropriate docker-compose command
if [ "$ENV" = "dev" ]; then
    if [ -n "$BUILD_FLAG" ]; then
        echo "Building and starting development environment..."
    else
        echo "Starting development environment..."
    fi
    docker compose -f docker/docker-compose-dev.yaml -p main up $BUILD_FLAG $DETACHED_FLAG
elif [ "$ENV" = "prod" ]; then
    if [ -n "$BUILD_FLAG" ]; then
        echo "Building and starting production environment..."
    else
        echo "Starting production environment..."
    fi
    docker compose -f docker/docker-compose.yaml -p main up $BUILD_FLAG $DETACHED_FLAG
fi
