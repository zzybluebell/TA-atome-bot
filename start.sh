#!/bin/bash

# Check for .env
if ! grep -q "sk-" atome-bot/backend/.env; then
    echo "Error: Please set your OPENAI_API_KEY in atome-bot/backend/.env"
    exit 1
fi

# Start Backend
echo "Starting Backend..."
cd atome-bot/backend
source venv/bin/activate
uvicorn main:app --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

wait
