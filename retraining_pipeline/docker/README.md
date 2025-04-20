# Unified MLOps Environment: Jenkins + MLflow

This directory contains a Docker setup that runs both Jenkins and MLflow in a single container for model retraining automation.

## Features

- Jenkins LTS with CI/CD plugins
- MLflow tracking server (port 5001)
- Automated model retraining pipeline
- Google Cloud integration

## Prerequisites

- Docker installed
- Google Cloud Platform account with:
  - GCS bucket for embeddings
  - Artifact Registry repository
  - Service account with permissions

## Quick Start

```bash
cd retraining_pipeline/docker
chmod +x init-container.sh
./init-container.sh
```

The script will:
- Create Docker volumes
- Build and run the container
- Display the Jenkins admin password

## Manual Setup

```bash
# Build image
docker build -t unified-mlops .

# Create volumes
docker volume create jenkins_home
docker volume create mlflow_data

# Run container
docker run -d --name unified-mlops \
  --restart unless-stopped \
  -p 8080:8080 -p 50000:50000 -p 5001:5001 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  -v mlflow_data:/mlflow \
  unified-mlops
```

## Jenkins Setup

### Using env_variables.json (Recommended)

1. Ensure your `env_variables.json` file contains the following variables:
   ```json
   {
     "MLFLOW_TRACKING_URI": "http://localhost:5001",
     "GCP_PROJECT_ID": "your-gcp-project-id",
     "GCP_BUCKET_NAME": "your-gcs-bucket-name",
     "GOOGLE_APPLICATION_CREDENTIALS": "path/to/service-account-key.json",
     "EMAIL_ADDRESS": "your-email@example.com",
     "ARTIFACT_REGISTRY_REPO": "region-docker.pkg.dev/project-id/repository-name/image-name"
   }
   ```

2. Upload the `env_variables.json` file to Jenkins:
   - Go to Jenkins dashboard
   - Navigate to Manage Jenkins > Script Console
   - Use the following script to create credentials from your JSON file:

```groovy
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*
import hudson.util.Secret
import groovy.json.JsonSlurper

// Path to the uploaded JSON file (update this path)
def jsonContent = '''PASTE_YOUR_JSON_CONTENT_HERE'''

try {
    // Parse the JSON content
    def jsonSlurper = new JsonSlurper()
    def credentials = jsonSlurper.parseText(jsonContent)

    // Get Jenkins instance
    def jenkins = Jenkins.getInstance()
    def domain = Domain.global()
    def store = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

    // Add each credential
    credentials.each { key, value ->
        println "Adding credential: ${key}"

        // Create a string credential
        def credential = new StringCredentialsImpl(
            CredentialsScope.GLOBAL,
            key,
            key,
            Secret.fromString(value.toString())
        )

        // Add the credential to the store
        store.addCredentials(domain, credential)
    }

    println "All credentials loaded successfully!"
} catch (Exception e) {
    println "ERROR: ${e.message}"
    e.printStackTrace()
}
```

3. Replace `PASTE_YOUR_JSON_CONTENT_HERE` with the contents of your `env_variables.json` file
4. Click "Run" to execute the script

### Manual Setup (Alternative)

Alternatively, add these credentials manually in Jenkins (Manage Jenkins > Credentials > Add):
- `MLFLOW_TRACKING_URI`: MLflow tracking server URI (http://localhost:5001)
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_BUCKET_NAME`: Your GCS bucket name
- `GOOGLE_APPLICATION_CREDENTIALS`: GCP service account key file
- `EMAIL_ADDRESS`: Notification email
- `ARTIFACT_REGISTRY_REPO`: Full path to your Artifact Registry repository (region-docker.pkg.dev/project-id/repository-name/image-name)

## Pipeline Stages

1. **Setup**: Install dependencies
2. **Download**: Get embeddings from GCS
3. **Train**: Train XGBoost model with MLflow tracking
4. **Deploy**: Push model to Google Artifact Registry

## Accessing Services

- Jenkins: http://localhost:8080
- MLflow: http://localhost:5001

## Troubleshooting

- Check logs: `docker logs unified-mlops`
- Ensure Docker socket is properly mounted
