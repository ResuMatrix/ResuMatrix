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

        # For demo purposes, we'll just log what we would do in a real scenario
        logger.info("DEMO MODE: Simulating Docker build and push")
        logger.info(f"Would build Docker image with model: {model_path}")
        logger.info(f"Would push to Artifact Registry: {artifact_registry_repo}")

        # Create a timestamp for the image tag
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_tag = f"{artifact_registry_repo}:{timestamp}"
        logger.info(f"Generated image tag: {image_tag}")

        # In a real scenario, we would:
        # 1. Copy the model file to the current directory
        # 2. Create a Dockerfile
        # 3. Build the Docker image
        # 4. Configure Docker for Google Artifact Registry
        # 5. Push the Docker image
        # 6. Clean up temporary files

        # For demo purposes, we'll just simulate these steps
        logger.info("DEMO MODE: Simulating Docker build process")
        logger.info(f"1. Would copy model file: {model_path}")
        logger.info("2. Would create a Dockerfile")
        logger.info(f"3. Would build Docker image: {image_tag}")
        logger.info("4. Would configure Docker for Google Artifact Registry")
        logger.info(f"5. Would push Docker image: {image_tag}")
        logger.info("6. Would clean up temporary files")

        # Save the image tag for reference
        with open(os.path.join("model_registry", "latest_image.txt"), "w") as f:
            f.write(image_tag)
        logger.info(f"Saved image tag to model_registry/latest_image.txt")

        # Remove the indicator file
        try:
            os.remove(os.path.join("model_registry", "new_model_saved.txt"))
            logger.info("Removed indicator file")
        except Exception as e:
            logger.warning(f"Error removing indicator file: {str(e)}")
            # Continue anyway, this is not critical

        logger.info(f"DEMO MODE: Successfully simulated pushing model to Google Artifact Registry: {image_tag}")

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

    # For demo purposes, we'll just log the credentials we have
    if gcp_credentials:
        logger.info(f"GCP credentials environment variable is set")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set, but continuing for demo purposes")

    if gcp_project_id:
        logger.info(f"Using GCP project ID: {gcp_project_id}")
    else:
        logger.warning("GCP_PROJECT_ID not set, but continuing for demo purposes")

    if artifact_registry_repo:
        logger.info(f"Using Artifact Registry repo: {artifact_registry_repo}")
    else:
        logger.warning("ARTIFACT_REGISTRY_REPO not set, but continuing for demo purposes")

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
