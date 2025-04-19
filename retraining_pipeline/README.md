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
- `jenkins_pipeline.groovy`: Original Jenkins pipeline definition
- `Jenkinsfile`: Standard Jenkins pipeline definition (alternative to jenkins_pipeline.groovy)
- `docker-compose.yml`: Docker Compose file for running Jenkins and MLflow
- `JENKINS_SETUP.md`: Detailed instructions for setting up Jenkins
- `run_in_docker.sh`: Script to run the retraining pipeline in Docker without Jenkins
- `run_local.sh`: Script to run the retraining pipeline in a new Python virtual environment
- `clean_env.sh`: Script to clean up the Python virtual environment
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

### Jenkins Setup

For detailed instructions on setting up Jenkins, see `JENKINS_SETUP.md`.

Quick start:

1. Start Jenkins and MLflow using Docker Compose:
   ```bash
   cd retraining_pipeline
   docker-compose up -d
   ```

2. Configure Jenkins with the necessary credentials and plugins
3. Create a new Jenkins pipeline job using either the `jenkins_pipeline.groovy` file or the `Jenkinsfile`
4. Set up the required environment variables in Jenkins

## Running Locally

### Using a new Python virtual environment (recommended)

The easiest way to run the pipeline locally is to use the provided script:

```bash
./run_local.sh
```

This script will:
1. Create a new Python virtual environment called `retraining_env`
2. Install all required dependencies
3. Set up the necessary environment variables
4. Run the pipeline in the virtual environment

To clean up the virtual environment:

```bash
./clean_env.sh
```

### Manual execution

To run the pipeline manually:

1. Set up the required environment variables
2. Run `python download_from_gcs.py` to download the data
3. Run `python run_retraining.py` to train and evaluate the model

## Docker

### Using the run_in_docker.sh script

The easiest way to run the pipeline in Docker is to use the provided script:

```bash
./run_in_docker.sh
```

This script will build the Docker image and run the container with the appropriate environment variables.

### Manual Docker setup

To build and run the Docker image manually:

```bash
docker build -t resumatrix-retraining -f Dockerfile .
docker run -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json \
           -e GCP_BUCKET_NAME=your-bucket-name \
           -e MLFLOW_TRACKING_URI=http://localhost:5000 \
           resumatrix-retraining
```
