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
        # Get environment variables
        gcp_project_id = os.environ.get("GCP_PROJECT_ID")
        artifact_registry_repo = os.environ.get("ARTIFACT_REGISTRY_REPO")

        if not gcp_project_id:
            logger.error("GCP_PROJECT_ID environment variable not set.")
            return False

        if not artifact_registry_repo:
            logger.error("ARTIFACT_REGISTRY_REPO environment variable not set.")
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
        check_repo_cmd = f"gcloud artifacts repositories describe {repository_name} --location={region} --project={gcp_project_id} || gcloud artifacts repositories create {repository_name} --repository-format=docker --location={region} --project={gcp_project_id}"
        subprocess.run(check_repo_cmd, shell=True, check=True)

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
        subprocess.run(build_command, shell=True, check=True)

        # Configure Docker to use Google Artifact Registry
        logger.info("Configuring Docker for Google Artifact Registry")
        configure_command = f"gcloud auth configure-docker {registry_host}"
        subprocess.run(configure_command, shell=True, check=True)

        # Push the Docker image to Google Artifact Registry
        logger.info(f"Pushing Docker image to Google Artifact Registry: {image_tag}")
        push_command = f"docker push {image_tag}"
        subprocess.run(push_command, shell=True, check=True)

        # Clean up
        cleanup_command = f"rm ModelDockerfile {model_filename}"
        subprocess.run(cleanup_command, shell=True, check=True)

        # Remove the indicator file
        os.remove(os.path.join("model_registry", "new_model_saved.txt"))

        logger.info(f"Successfully pushed model to Google Artifact Registry: {image_tag}")

        # Save the image tag to a file for reference
        with open(os.path.join("model_registry", "latest_image.txt"), "w") as f:
            f.write(image_tag)

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
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Using default credentials.")

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
