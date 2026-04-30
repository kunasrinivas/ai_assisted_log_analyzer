#!/usr/bin/env bash
# Run from inside WSL2. Starts Docker daemon if not running, then brings up all services.
# Usage:
#   wsl bash scripts/run.sh          # start everything
#   wsl bash scripts/run.sh down     # stop and remove containers
#   wsl bash scripts/run.sh logs     # tail all service logs
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure Docker daemon is running
if ! docker info &>/dev/null; then
  echo "==> Starting Docker daemon..."
  sudo service docker start
  sleep 3
fi

case "${1:-up}" in
  up)
    echo "==> Building and starting all services..."
    docker compose up --build -d
    echo ""
    echo "Services are up:"
    echo "  UI          -> http://localhost:8080"
    echo "  BFF API     -> http://localhost:8010/api/health"
    echo "  Internal services are reachable only inside the Docker network."
    ;;
  down)
    echo "==> Stopping all services..."
    docker compose down
    ;;
  logs)
    docker compose logs -f
    ;;
  *)
    echo "Usage: run.sh [up|down|logs]"
    exit 1
    ;;
esac
