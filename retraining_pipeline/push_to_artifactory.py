#!/usr/bin/env python3
"""
Push the trained model to Google Artifact Registry.
This script:
1. Checks if a new model has been saved
2. Builds a Docker image with the model
3. Pushes the image to Google Artifact Registry
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_for_new_model(model_registry_dir="model_registry"):
    """Check if a new model has been saved."""
    indicator_file = os.path.join(model_registry_dir, "new_model_saved.txt")

    if not os.path.exists(indicator_file):
        logger.info("No new model found.")
        return None

    # Read the indicator file to get the model path
    with open(indicator_file, "r") as f:
        content = f.read()

    # Extract the model path from the content
    import re
    match = re.search(r"New model saved at (.*) with timestamp", content)
    if not match:
        logger.error("Could not extract model path from indicator file.")
        return None

    model_path = match.group(1)
    if not os.path.exists(model_path):
        logger.error(f"Model file {model_path} does not exist.")
        return None

    return model_path

def build_and_push_docker_image(model_path):
    """Build a Docker image with the model and push it to Google Artifact Registry."""
    try:
        # Check if gcloud is installed
        try:
            subprocess.run("which gcloud", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Google Cloud SDK (gcloud) is installed")
        except subprocess.CalledProcessError:
            logger.error("Google Cloud SDK (gcloud) is not installed. Please install it first.")
            logger.error("You can install it by running: apt-get update && apt-get install -y google-cloud-sdk")
            return False

        # Get environment variables
        gcp_project_id = os.environ.get("GCP_PROJECT_ID")
        artifact_registry_repo = os.environ.get("ARTIFACT_REGISTRY_REPO")
        gcp_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not gcp_project_id:
            logger.error("GCP_PROJECT_ID environment variable not set.")
            return False

        if not artifact_registry_repo:
            logger.error("ARTIFACT_REGISTRY_REPO environment variable not set.")
            return False

        if not gcp_credentials:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            return False

        # Authenticate with Google Cloud using the service account key
        logger.info(f"Authenticating with Google Cloud using service account key: {gcp_credentials}")
        try:
            # Check if the credentials file exists
            if not os.path.exists(gcp_credentials):
                logger.error(f"Service account key file not found at: {gcp_credentials}")
                return False

            # Authenticate with Google Cloud
            auth_command = f"gcloud auth activate-service-account --key-file={gcp_credentials}"
            process = subprocess.run(auth_command, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                logger.error(f"Error authenticating with Google Cloud: {process.stderr}")
                return False
            logger.info("Successfully authenticated with Google Cloud")

            # Set the project
            project_command = f"gcloud config set project {gcp_project_id}"
            process = subprocess.run(project_command, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                logger.error(f"Error setting Google Cloud project: {process.stderr}")
                return False
            logger.info(f"Set Google Cloud project to: {gcp_project_id}")
        except Exception as e:
            logger.error(f"Error authenticating with Google Cloud: {str(e)}")
            return False

        # Extract repository information from ARTIFACT_REGISTRY_REPO
        # Format: region-docker.pkg.dev/project-id/repository-name/image-name
        repo_parts = artifact_registry_repo.split('/')
        if len(repo_parts) < 4:
            logger.error(f"Invalid ARTIFACT_REGISTRY_REPO format: {artifact_registry_repo}")
            return False

        registry_host = repo_parts[0]  # e.g., us-east1-docker.pkg.dev
        repository_name = repo_parts[2]  # e.g., resume-fit-supervised
        image_name = '/'.join(repo_parts[3:])  # e.g., xgboost_and_cosine_similarity

        # Check if the repository exists, if not create it
        logger.info("Checking if Artifact Registry repository exists...")
        region = registry_host.split('-')[0]  # Extract region (e.g., us-east1)

        # First, check if the repository exists
        describe_cmd = f"gcloud artifacts repositories describe {repository_name} --location={region} --project={gcp_project_id}"
        process = subprocess.run(describe_cmd, shell=True, capture_output=True, text=True)

        if process.returncode != 0:
            # Repository doesn't exist, create it
            logger.info(f"Repository {repository_name} doesn't exist. Creating it...")
            create_cmd = f"gcloud artifacts repositories create {repository_name} --repository-format=docker --location={region} --project={gcp_project_id}"
            process = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)

            if process.returncode != 0:
                logger.error(f"Error creating Artifact Registry repository: {process.stderr}")
                return False
            logger.info(f"Successfully created repository {repository_name}")
        else:
            logger.info(f"Repository {repository_name} already exists")

        # Create a temporary directory for the Docker build
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_tag = f"{artifact_registry_repo}:{timestamp}"

        # Copy the model file to the current directory
        model_filename = os.path.basename(model_path)
        copy_command = f"cp {model_path} ."
        subprocess.run(copy_command, shell=True, check=True)

        # Create a minimal Dockerfile for the model
        with open("ModelDockerfile", "w") as f:
            f.write(f"""FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the model file
COPY {model_filename} /app/model.joblib

# Install dependencies
RUN pip install --no-cache-dir joblib scikit-learn xgboost numpy

# Create an entrypoint script
RUN echo '#!/bin/bash\\necho "Model container is running. Use this container as a base for inference."' > /app/entrypoint.sh && \\
    chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
""")

        # Build the Docker image
        logger.info(f"Building Docker image: {image_tag}")
        build_command = f"docker build -f ModelDockerfile -t {image_tag} ."
        process = subprocess.run(build_command, shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"Error building Docker image: {process.stderr}")
            return False
        logger.info("Successfully built Docker image")

        # Configure Docker to use Google Artifact Registry
        logger.info("Configuring Docker for Google Artifact Registry")
        configure_command = f"gcloud auth configure-docker {registry_host} --quiet"
        process = subprocess.run(configure_command, shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"Error configuring Docker for Google Artifact Registry: {process.stderr}")
            return False
        logger.info("Successfully configured Docker for Google Artifact Registry")

        # Push the Docker image to Google Artifact Registry
        logger.info(f"Pushing Docker image to Google Artifact Registry: {image_tag}")
        push_command = f"docker push {image_tag}"
        process = subprocess.run(push_command, shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"Error pushing Docker image to Google Artifact Registry: {process.stderr}")
            return False
        logger.info("Successfully pushed Docker image to Google Artifact Registry")

        # Clean up
        cleanup_command = f"rm ModelDockerfile {model_filename}"
        process = subprocess.run(cleanup_command, shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            logger.warning(f"Error cleaning up temporary files: {process.stderr}")
            # Continue anyway, this is not critical
        else:
            logger.info("Successfully cleaned up temporary files")

        # Remove the indicator file
        try:
            os.remove(os.path.join("model_registry", "new_model_saved.txt"))
        except Exception as e:
            logger.warning(f"Error removing indicator file: {str(e)}")
            # Continue anyway, this is not critical

        logger.info(f"Successfully pushed model to Google Artifact Registry: {image_tag}")

        # Save the image tag to a file for reference
        try:
            with open(os.path.join("model_registry", "latest_image.txt"), "w") as f:
                f.write(image_tag)
            logger.info(f"Saved image tag to model_registry/latest_image.txt")
        except Exception as e:
            logger.warning(f"Error saving image tag to file: {str(e)}")
            # Continue anyway, this is not critical

        return True

    except Exception as e:
        logger.error(f"Error building and pushing Docker image: {str(e)}")
        return False

def main():
    """Main function to push the model to Google Artifact Registry."""
    # Get environment variables
    gcp_project_id = os.environ.get("GCP_PROJECT_ID")
    gcp_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    artifact_registry_repo = os.environ.get("ARTIFACT_REGISTRY_REPO")

    # Log essential information
    logger.info(f"Using GCP project: {gcp_project_id}")
    logger.info(f"Using Artifact Registry repo: {artifact_registry_repo}")

    # Ensure GCP credentials are properly set
    if gcp_credentials:
        logger.info(f"Using GCP credentials from: {gcp_credentials}")
        # Check if the file exists
        if os.path.exists(gcp_credentials):
            logger.info("GCP credentials file exists.")
        else:
            logger.error(f"GCP credentials file does not exist at: {gcp_credentials}")
            logger.error("Please make sure the service account key file is available.")
            sys.exit(1)
    else:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS not set.")
        logger.error("Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable.")
        sys.exit(1)

    # Check if a new model has been saved
    model_path = check_for_new_model()
    if not model_path:
        logger.info("No new model to push to Google Artifact Registry.")
        sys.exit(0)

    logger.info(f"Found new model at: {model_path}")

    # Build and push the Docker image
    success = build_and_push_docker_image(model_path)
    if not success:
        logger.error("Failed to push model to Google Artifact Registry.")
        sys.exit(1)

    logger.info("Successfully pushed model to Google Artifact Registry.")
    sys.exit(0)

if __name__ == "__main__":
    main()
