#!/usr/bin/env bash
# Start the Triangle Analyzer (FastAPI backend + Vite frontend)
# Run from the Week1Project directory: bash start.sh

PROJECT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting FastAPI backend on http://localhost:8000 ..."
cd "$PROJECT/backend"
python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Vite frontend on http://localhost:5173 ..."
cd "$PROJECT/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "Both servers running."
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo "  API docs → http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Shut down both servers cleanly on Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'" EXIT
wait
