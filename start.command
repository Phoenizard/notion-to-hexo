#!/bin/bash
cd "$(dirname "$0")"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop first."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check config.json exists
if [ ! -f config.json ]; then
    echo "Error: config.json not found. Copy config.example.json and fill in your credentials."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Starting notion-to-hexo..."
docker compose up --build -d

echo "Waiting for service to start..."
sleep 3
open http://localhost:8501

echo "notion-to-hexo is running at http://localhost:8501"
echo "To stop: docker compose down"
