#!/usr/bin/env bash
# Start the Triangle GraphQL API (Week3Project)
# Usage: bash start.sh [port]
#   Default port: 8001

set -e

PORT="${1:-8001}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "=== Triangle GraphQL API ==="
echo "Starting on port $PORT..."
echo ""
echo "  Swagger UI : http://localhost:$PORT/docs"
echo "  GraphiQL   : http://localhost:$PORT/graphql"
echo ""
echo "Default credentials: username=admin  password=secret"
echo ""

cd "$BACKEND_DIR"
uvicorn main:app --reload --port "$PORT"
