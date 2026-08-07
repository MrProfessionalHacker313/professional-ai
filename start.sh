#!/bin/bash
set -e

echo "========================================"
echo "  PROFESSIONAL AI - ONE COMMAND START"
echo "========================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "WARNING: Please edit .env and set your SECRET_KEY, JWT_SECRET,"
    echo "ENCRYPTION_KEY, OWNER_EMAIL, and OWNER_SETUP_KEY before running again."
    echo ""
    exit 1
fi

# Install dependencies on first run
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd frontend && npm install)
fi

if [ ! -d "backend/.venv" ]; then
    echo "Installing backend dependencies..."
    (cd backend && pip install -r requirements.txt)
fi

echo ""
echo "Starting Professional AI..."
echo "This will start: Frontend (3000) + Backend (8000) + PostgreSQL + Redis"
echo ""
echo "After startup, open: http://localhost:3000"
echo ""

docker compose up --build

echo ""
echo "PROFESSIONAL AI FULLY RUNNING at http://localhost:3000"
