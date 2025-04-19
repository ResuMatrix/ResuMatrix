#!/bin/bash
# Script to run the retraining pipeline in Docker

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default values for environment variables
GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-resumatrix-embeddings}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-awesome-nimbus-452221-v2}
MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://localhost:5001}
ARTIFACT_REGISTRY_REPO=${ARTIFACT_REGISTRY_REPO:-us-east1-docker.pkg.dev/${GCP_PROJECT_ID}/resume-fit-supervised/xgboost_and_cosine_similarity}
GCP_JSON_PATH=${GCP_JSON_PATH:-gcp-credentials.json}

# Check if GCP credentials file exists
if [ ! -f "$GCP_JSON_PATH" ]; then
    echo "Error: GCP credentials file not found at $GCP_JSON_PATH"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t resumatrix-retraining -f retraining_pipeline/Dockerfile .

# Run the Docker container
echo "Running retraining pipeline in Docker..."
docker run --rm \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/model_registry:/app/model_registry \
    -v $(pwd)/$GCP_JSON_PATH:/app/gcp-credentials.json \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json \
    -e GCP_BUCKET_NAME=$GCP_BUCKET_NAME \
    -e GCP_PROJECT_ID=$GCP_PROJECT_ID \
    -e MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI \
    -e ARTIFACT_REGISTRY_REPO=$ARTIFACT_REGISTRY_REPO \
    resumatrix-retraining

echo "Retraining pipeline completed."
