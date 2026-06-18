#!/bin/bash
# Local development start script

echo "========================================="
echo "Starting FastAPI backend locally..."
echo "========================================="
# Start the FastAPI backend server using uvicorn
./venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8005
