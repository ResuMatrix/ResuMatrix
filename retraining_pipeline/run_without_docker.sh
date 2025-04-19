#!/bin/bash
# Script to run the retraining pipeline without Docker

# Set default values for environment variables
export GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-resumatrix-embeddings}
export GCP_PROJECT_ID=${GCP_PROJECT_ID:-awesome-nimbus-452221-v2}
export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://localhost:5001}
export ARTIFACT_REGISTRY_REPO=${ARTIFACT_REGISTRY_REPO:-us-east1-docker.pkg.dev/${GCP_PROJECT_ID}/resume-fit-supervised/xgboost_and_cosine_similarity}

# Check if GCP credentials are set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "ERROR: GOOGLE_APPLICATION_CREDENTIALS not set."
    echo "Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable."
    exit 1
fi

echo "Using GCP credentials from GOOGLE_APPLICATION_CREDENTIALS"

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
