#!/usr/bin/env bash
# Run this ONCE inside WSL2 (Ubuntu 24.04) to install Docker Engine without Docker Desktop.
# Usage (from Windows PowerShell):
#   wsl bash /path/to/scripts/wsl2_docker_setup.sh
set -euo pipefail

echo "==> Removing any conflicting legacy Docker packages..."
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  sudo apt-get remove -y "$pkg" 2>/dev/null || true
done

echo "==> Installing prerequisites..."
sudo apt-get update -q
sudo apt-get install -y ca-certificates curl gnupg lsb-release

echo "==> Adding Docker's official GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "==> Setting up the Docker apt repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "==> Installing Docker Engine and Compose plugin..."
sudo apt-get update -q
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Adding current user to docker group (no sudo needed for docker commands)..."
sudo usermod -aG docker "$USER"

echo "==> Starting Docker daemon (WSL2 does not run systemd by default)..."
sudo service docker start || sudo dockerd &>/tmp/dockerd.log &
sleep 3

echo "==> Verifying installation..."
docker version
docker compose version

echo ""
echo "Done. Docker Engine is ready inside WSL2."
echo "NOTE: Run 'sudo service docker start' at the start of each WSL2 session, or add it to ~/.bashrc."
