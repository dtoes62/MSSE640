#!/usr/bin/env bash
# Start the Triangle GraphQL API over HTTPS with HTTP/2 (Week3Project)
# Usage: bash start.sh [port]
#   Default port: 8443

set -e

PORT="${1:-8443}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
CERT_FILE="$SCRIPT_DIR/certs/cert.pem"
KEY_FILE="$SCRIPT_DIR/certs/key.pem"

if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
    echo "ERROR: TLS certificates not found in $SCRIPT_DIR/certs/"
    echo "Run the following to generate them:"
    echo "  cd certs && MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj \"/CN=localhost\""
    exit 1
fi

echo "=== Triangle GraphQL API (HTTPS + HTTP/2) ==="
echo "Starting on port $PORT..."
echo ""
echo "  Swagger UI : https://localhost:$PORT/docs"
echo "  GraphiQL   : https://localhost:$PORT/graphql"
echo ""
echo "NOTE: Browser will warn about the self-signed certificate."
echo "      Click 'Advanced' -> 'Proceed to localhost' to continue."
echo ""
echo "Default credentials: username=admin  password=secret"
echo ""

cd "$BACKEND_DIR"
uvicorn main:app \
    --port "$PORT" \
    --ssl-certfile "$CERT_FILE" \
    --ssl-keyfile  "$KEY_FILE"
