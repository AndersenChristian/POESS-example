#!/bin/bash

SERVICE="$1"

# Allowed services
VALID_SERVICES=("siddhi" "microservice" "logging")

# Check if argument is provided
if [ -z "$SERVICE" ]; then
    echo "❌ No service specified."
    echo "Usage: ./rebuild.sh <siddhi|microservice|logging>"
    exit 1
fi

# Check if argument is valid
if [[ ! " ${VALID_SERVICES[@]} " =~ " ${SERVICE} " ]]; then
    echo "❌ Invalid service: $SERVICE"
    echo "Valid options: siddhi, microservice, logging"
    exit 1
fi

echo "🔧 Stopping all containers..."
docker-compose down

echo "🔨 Rebuilding $SERVICE..."
docker-compose build "$SERVICE" --no-cache

echo "🚀 Starting all containers..."
docker-compose up
