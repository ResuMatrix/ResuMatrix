# ML Model Retraining Pipeline

This directory contains a Jenkins-based ML retraining pipeline for the ResuMatrix project. The pipeline is triggered when new embeddings and metadata are uploaded to Google Cloud Storage (GCS).

## Pipeline Overview

The pipeline performs the following steps:

1. Downloads train/test embeddings and metadata from GCS
2. Loads and validates the data
3. Trains a new XGBoost model using the existing training function
4. Logs metrics with MLflow (accuracy, classification report, confusion matrix)
5. Compares the new model to the best previous run (based on accuracy)
6. If the new model performs better, saves it to the model registry
7. Pushes the model to Google Artifact Registry if a new model was saved

## Files

- `download_from_gcs.py`: Downloads files from GCS and saves them to local disk
- `run_retraining.py`: Loads the data, trains the model, and compares it to the best previous model
- `Dockerfile`: Defines the Docker image for running the pipeline
- `jenkins_pipeline.groovy`: Jenkins pipeline definition
- `requirements.txt`: Python dependencies for the pipeline

## Environment Variables

The pipeline uses the following environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account credentials (defaults to `GCP_JSON_PATH`)
- `GCP_BUCKET_NAME`: Name of the GCS bucket containing embeddings and metadata
- `GCP_PROJECT_ID`: Google Cloud Project ID
- `MLFLOW_TRACKING_URI`: URI of the MLflow tracking server (defaults to `http://localhost:5000`)
- `ARTIFACT_REGISTRY_REPO`: Google Artifact Registry repository for storing Docker images (defaults to `us-east1-docker.pkg.dev/${GCP_PROJECT_ID}/resume-fit-supervised/xgboost_and_cosine_similarity`)
- `DATA_DIR`: Directory for storing downloaded data (defaults to `data`)
- `MODEL_REGISTRY_DIR`: Directory for storing trained models (defaults to `model_registry`)

These variables are set in the `.env` file at the root of the project.

## Setup

1. Configure Jenkins with the necessary credentials and plugins
2. Create a new Jenkins pipeline job using the `jenkins_pipeline.groovy` file
3. Set up the required environment variables in Jenkins

## Running Locally

To run the pipeline locally:

1. Set up the required environment variables
2. Run `python download_from_gcs.py` to download the data
3. Run `python run_retraining.py` to train and evaluate the model

## Docker

To build and run the Docker image:

```bash
docker build -t resumatrix-retraining -f Dockerfile .
docker run -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json \
           -e GCP_BUCKET_NAME=your-bucket-name \
           -e MLFLOW_TRACKING_URI=http://localhost:5000 \
           resumatrix-retraining
```
