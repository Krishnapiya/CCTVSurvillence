#!/bin/bash

# Exit on error
set -e

echo "========================================="
echo "Starting AI Surveillance Platform Backend"
echo "========================================="

# Run verification checks first
echo "Running module import verification checks..."
python3 test_verification.py

echo "Building and starting Docker services..."
docker-compose up --build -d

echo "Services started successfully!"
echo "- FastAPI documentation: http://localhost:8000/docs"
echo "- RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "- WebSocket Alert Feed: ws://localhost:8000/api/v1/ws/alerts"
echo "========================================="
