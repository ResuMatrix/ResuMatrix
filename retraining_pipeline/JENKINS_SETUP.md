# Jenkins Setup for ResuMatrix Retraining Pipeline

This document contains instructions for running the ResuMatrix retraining pipeline on Jenkins inside a Docker container.

## Prerequisites

- Docker and Docker Compose installed
- Google Cloud Platform (GCP) credentials
- Access to the ResuMatrix GCP bucket

## Setup

1. **Start Jenkins and MLflow**

   ```bash
   cd retraining_pipeline
   docker-compose up -d
   ```

   This will start Jenkins on port 8081 and MLflow on port 5000.

2. **Get the Jenkins admin password**

   ```bash
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

3. **Access Jenkins**

   Open a browser and navigate to http://localhost:8081

4. **Complete the Jenkins setup**

   - Install the suggested plugins
   - Create an admin user
   - Configure Jenkins URL

5. **Install additional plugins**

   Go to "Manage Jenkins" > "Manage Plugins" > "Available" and install the following plugins:
   - Docker Pipeline
   - Pipeline
   - Git
   - Google Kubernetes Engine
   - Google OAuth Credentials
   - Google Storage Plugin

6. **Configure GCP credentials**

   Go to "Manage Jenkins" > "Manage Credentials" > "Jenkins" > "Global credentials" > "Add Credentials"
   - Kind: Google Service Account from private key
   - Project Name: your-gcp-project-id
   - JSON key: Upload your GCP service account key file
   - ID: gcp-credentials

7. **Create a Jenkins pipeline**

   - Go to "New Item"
   - Enter a name for the pipeline (e.g., "ResuMatrix-Retraining")
   - Select "Pipeline"
   - Click "OK"
   - In the "Pipeline" section, select "Pipeline script from SCM"
   - SCM: Git
   - Repository URL: your-git-repo-url
   - Script Path: retraining_pipeline/Jenkinsfile
   - Click "Save"

8. **Run the pipeline**

   - Go to the pipeline you created
   - Click "Build Now"

## Environment Variables

The following environment variables are used by the pipeline:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_BUCKET_NAME`: The name of the GCS bucket containing embeddings and metadata
- `MLFLOW_TRACKING_URI`: The URI of the MLflow tracking server
- `ARTIFACT_REGISTRY_REPO`: The Google Artifact Registry repository for storing Docker images

These variables can be set in the `.env` file in the root directory of the project or in the Jenkins pipeline configuration.

## Troubleshooting

- If you encounter permission issues with Docker, make sure the Jenkins user has permission to access the Docker socket.
- If you encounter issues with GCP authentication, make sure the GCP credentials are properly configured in Jenkins.
- If the pipeline fails, check the Jenkins logs for more information.
