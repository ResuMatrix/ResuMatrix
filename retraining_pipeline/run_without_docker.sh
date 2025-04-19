#!/bin/bash
# Script to run the retraining pipeline without Docker

# Load environment variables from .env file
if [ -f ../.env ]; then
    export $(grep -v '^#' ../.env | xargs)
elif [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default values for environment variables
export GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-resumatrix-embeddings}
export GCP_PROJECT_ID=${GCP_PROJECT_ID:-awesome-nimbus-452221-v2}
export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://localhost:5001}
export ARTIFACT_REGISTRY_REPO=${ARTIFACT_REGISTRY_REPO:-us-east1-docker.pkg.dev/${GCP_PROJECT_ID}/resume-fit-supervised/xgboost_and_cosine_similarity}
export GCP_JSON_PATH=${GCP_JSON_PATH:-gcp-credentials.json}

# Check if GCP credentials file exists
if [ ! -f "$GCP_JSON_PATH" ] && [ ! -f "../$GCP_JSON_PATH" ]; then
    echo "Error: GCP credentials file not found at $GCP_JSON_PATH or ../$GCP_JSON_PATH"
    exit 1
fi

if [ -f "$GCP_JSON_PATH" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/$GCP_JSON_PATH
elif [ -f "../$GCP_JSON_PATH" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/../$GCP_JSON_PATH
fi

# Create directories if they don't exist
mkdir -p ../data ../model_registry

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/..

# Run the pipeline
echo "Running download_from_gcs.py..."
python download_from_gcs.py

if [ $? -eq 0 ]; then
    echo "Running run_retraining.py..."
    python run_retraining.py
else
    echo "Error: download_from_gcs.py failed. Aborting."
    exit 1
fi

echo "Retraining pipeline completed."
