#!/usr/bin/env bash
# Start music-practice-forge locally.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-5017}"
echo "music-practice-forge -> http://127.0.0.1:${PORT}"
exec python3 app.py
