# Model Retraining Pipeline

This directory contains the code and configuration for the automated model retraining pipeline.

## Directory Structure

- `docker/`: Contains Docker configuration for the unified Jenkins + MLflow environment
  - `Dockerfile`: Defines the Docker image with Jenkins and MLflow
  - `start-services.sh`: Script to start both Jenkins and MLflow services
  - `init-container.sh`: Script to initialize and run the Docker container
  - `README.md`: Documentation for the Docker setup

- `Jenkinsfile`: Defines the Jenkins pipeline for model retraining
- `download_from_gcs.py`: Script to download embeddings and metadata from Google Cloud Storage
- `run_retraining.py`: Script to run the model retraining process
- `push_to_artifactory.py`: Script to build and push the Docker image to Google Artifact Registry
- `requirements.txt`: Python dependencies for the retraining pipeline

## Getting Started

1. Set up the Docker environment:
   ```bash
   cd docker
   chmod +x init-container.sh
   ./init-container.sh
   ```

2. Access Jenkins at http://localhost:8080 and set up the necessary credentials.

3. Access MLflow at http://localhost:5001 to view experiment results.

4. Create and run the model retraining pipeline in Jenkins.

## Pipeline Stages

1. **Setup Python Environment**: Creates a virtual environment and installs dependencies
2. **Download Data from GCS**: Downloads the latest embeddings and metadata from Google Cloud Storage
3. **Train Model**: Trains an XGBoost model and logs metrics to MLflow
4. **Build and Push Docker Image**: Builds a Docker image with the trained model and pushes it to Google Artifact Registry
