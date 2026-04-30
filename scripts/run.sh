#!/usr/bin/env bash
# Docker Compose service manager for this repository.
# Works on Linux/macOS and inside any shell where `docker compose` is available.
#
# Usage:
#   bash scripts/run.sh up           # build + start all services in background
#   bash scripts/run.sh down         # stop and remove services
#   bash scripts/run.sh restart      # down then up
#   bash scripts/run.sh build        # build images only
#   bash scripts/run.sh logs [svc]   # follow logs (all or one service)
#   bash scripts/run.sh ps           # show running services
#   bash scripts/run.sh config       # validate/print compose config
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"

cd "$REPO_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not in PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose plugin is required (Docker Compose v2)." >&2
  exit 1
fi

dc() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

print_endpoints() {
  echo ""
  echo "Services are up:"
  echo "  UI      -> http://localhost:8080"
  echo "  BFF API -> http://localhost:8010/api/health"
}

case "${1:-up}" in
  up)
    echo "==> Building and starting all services..."
    dc up --build -d
    print_endpoints
    ;;
  start)
    echo "==> Starting existing containers..."
    dc start
    print_endpoints
    ;;
  stop)
    echo "==> Stopping services..."
    dc stop
    ;;
  down)
    echo "==> Stopping and removing services..."
    dc down
    ;;
  restart)
    echo "==> Restarting services..."
    dc down
    dc up --build -d
    print_endpoints
    ;;
  build)
    echo "==> Building images..."
    dc build
    ;;
  pull)
    echo "==> Pulling images..."
    dc pull
    ;;
  logs)
    shift || true
    if [[ $# -gt 0 ]]; then
      dc logs -f "$1"
    else
      dc logs -f
    fi
    ;;
  ps|status)
    dc ps
    ;;
  config)
    dc config
    ;;
  *)
    cat <<'EOF'
Usage: bash scripts/run.sh [command]

Commands:
  up        Build and start all services (default)
  start     Start existing containers
  stop      Stop running services
  down      Stop and remove services
  restart   Recreate services (down + up --build)
  build     Build images only
  pull      Pull images only
  logs      Follow all logs (or pass a service name)
  ps        Show service status
  config    Validate and print compose config
EOF
    exit 1
    ;;
esac
