#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Power BI Answer Evaluator"
echo "=========================================================="

# 1. Start Backend in background
echo "[1/2] Launching FastAPI Backend on http://localhost:8000..."
cd backend
PYTHONPATH=. ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Start Frontend
echo "[2/2] Launching Next.js Frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Power BI Answer Evaluator is now running!"
echo "-> Frontend: http://localhost:3000"
echo "-> Backend API: http://localhost:8000/docs"
echo ""

# Handle graceful shutdown
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
