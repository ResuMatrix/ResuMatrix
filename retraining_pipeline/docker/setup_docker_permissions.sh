#!/bin/bash
set -e

echo "Setting up Docker permissions for Jenkins..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)"
  exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed. Please install Docker first."
  exit 1
fi

# Check if Jenkins user exists
if ! id jenkins &> /dev/null; then
  echo "Jenkins user not found. Please make sure Jenkins is installed."
  exit 1
fi

echo "Setting Docker socket permissions..."
chmod 666 /var/run/docker.sock
echo "Docker socket permissions updated."

echo "Adding Jenkins user to Docker group..."
usermod -aG docker jenkins
echo "Jenkins user added to Docker group."

echo "Restarting Jenkins service..."
if systemctl is-active --quiet jenkins; then
  systemctl restart jenkins
  echo "Jenkins service restarted."
else
  echo "Jenkins service not found or not running via systemctl."
  echo "Please restart Jenkins manually."
fi

echo "Docker permissions setup complete."
echo "Note: You may need to restart your Docker container or service for changes to take effect."
echo "You can verify the setup by running a Docker command as the Jenkins user."
