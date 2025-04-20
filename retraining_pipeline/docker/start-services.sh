#!/bin/bash
set -e

# Ensure directories exist with proper permissions
mkdir -p /mlflow/artifacts /mlflow/mlruns /var/log/supervisor
chown -R jenkins:jenkins /mlflow

# Ensure Docker socket has correct permissions
if [ -e /var/run/docker.sock ]; then
  echo "Setting Docker socket permissions..."
  chmod 666 /var/run/docker.sock
  echo "Docker socket permissions updated."
else
  echo "Warning: Docker socket not found at /var/run/docker.sock"
fi

# Start MLflow in the background
echo "Starting MLflow server on port 5001..."
cd /mlflow && /opt/venv/bin/mlflow server \
  --host 0.0.0.0 \
  --port 5001 \
  --backend-store-uri /mlflow/mlruns \
  --default-artifact-root /mlflow/artifacts &

# Start Jenkins in the foreground
echo "Starting Jenkins server..."
exec /usr/local/bin/jenkins.sh
