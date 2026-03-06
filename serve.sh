#!/bin/bash
# Start local development server for testing index.html
# Usage: ./serve.sh [port]

PORT=${1:-8000}

cd "$(dirname "$0")"
echo "Starting server at http://localhost:$PORT"
echo "Press Ctrl+C to stop"
python3 -m http.server "$PORT"