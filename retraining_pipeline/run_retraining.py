#!/usr/bin/env python3
"""
Run retraining pipeline for XGBoost model.
This script:
1. Loads train/test embeddings and metadata from local files
2. Trains a new XGBoost model
3. Compares the new model to the best previous model
4. Saves the model if it performs better
"""

import os
import sys
import json
import logging
import numpy as np
import mlflow
from mlflow.tracking import MlflowClient
import joblib
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the training function
from src.model_training.similarity_with_xgboost import train_xgboost_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_embeddings(file_path):
    """Load embeddings from a .npz file."""
    try:
        data = np.load(file_path,allow_pickle=True)
        X = data['X']
        y = data['y']
        return X, y
    except Exception as e:
        logger.error(f"Error loading embeddings from {file_path}: {str(e)}")
        return None, None

def load_metadata(file_path):
    """Load metadata from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        logger.error(f"Error loading metadata from {file_path}: {str(e)}")
        return None

def get_best_model_metrics():
    """Get the metrics of the best model from MLflow."""
    try:
        # Set up MLflow client
        client = MlflowClient(tracking_uri=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))

        # Get the experiment ID for XGBoost with Similarity
        experiment = client.get_experiment_by_name("XGBoost Model with Similarity")
        if not experiment:
            logger.warning("No experiment found for XGBoost Model with Similarity")
            return None

        # Get all runs for the experiment
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.accuracy DESC"]
        )

        if not runs:
            logger.warning("No runs found for the experiment")
            return None

        # Get the best run (highest accuracy)
        best_run = runs[0]
        best_metrics = {
            "run_id": best_run.info.run_id,
            "accuracy": best_run.data.metrics.get("accuracy", 0.0)
        }

        logger.info(f"Best model metrics: {best_metrics}")
        return best_metrics

    except Exception as e:
        logger.error(f"Error getting best model metrics: {str(e)}")
        return None

def save_model(model, output_dir="model_registry"):
    """Save the model to the model registry."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save the model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(output_dir, f"xgboost_model_{timestamp}.joblib")
        joblib.dump(model, model_path)

        # Create indicator file for Jenkins
        with open(os.path.join(output_dir, "new_model_saved.txt"), "w") as f:
            f.write(f"New model saved at {model_path} with timestamp {timestamp}")

        logger.info(f"Model saved to {model_path}")
        return model_path

    except Exception as e:
        logger.error(f"Error saving model: {str(e)}")
        return None

def main():
    """Main function to run the retraining pipeline."""
    # Set up environment variables
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")
    gcp_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    data_dir = os.environ.get("DATA_DIR", "data")

    # Log essential information
    logger.info(f"Using MLflow tracking URI: {mlflow_uri}")
    logger.info(f"Using data directory: {data_dir}")

    # Ensure GCP credentials are properly set
    if gcp_credentials:
        # If the path is relative, convert it to absolute
        if not os.path.isabs(gcp_credentials):
            gcp_credentials = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', gcp_credentials))
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_credentials
        logger.info(f"Using GCP credentials from: {gcp_credentials}")

        # Check if the file exists
        if os.path.exists(gcp_credentials):
            logger.info("GCP credentials file exists.")
        else:
            logger.error(f"GCP credentials file does not exist at: {gcp_credentials}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Using default credentials.")

    # Set up MLflow tracking URI
    try:
        mlflow.set_tracking_uri(mlflow_uri)
        logger.info(f"MLflow tracking URI: {mlflow_uri}")

        # Wait for MLflow server to start up (max 60 seconds)
        import time
        import requests
        from urllib3.exceptions import NewConnectionError

        max_retries = 12
        retry_delay = 5
        for i in range(max_retries):
            try:
                response = requests.get(f"{mlflow_uri}/api/2.0/mlflow/experiments/list")
                if response.status_code == 200:
                    logger.info("Successfully connected to MLflow server")
                    break
                else:
                    logger.warning(f"MLflow server returned status code {response.status_code}")
            except (requests.exceptions.ConnectionError, NewConnectionError) as e:
                if i < max_retries - 1:
                    logger.warning(f"Waiting for MLflow server to start up (attempt {i+1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    logger.warning("Failed to connect to MLflow server after multiple attempts")
                    logger.warning("Continuing without MLflow tracking...")
    except Exception as e:
        logger.warning(f"Failed to set MLflow tracking URI: {str(e)}")
        logger.warning("Continuing without MLflow tracking...")

    # Load file paths
    data_dir = os.environ.get("DATA_DIR", "data")
    file_paths_file = os.path.join(data_dir, "file_paths.json")

    try:
        with open(file_paths_file, "r") as f:
            file_paths = json.load(f)
    except Exception as e:
        logger.error(f"Error loading file paths: {str(e)}")
        exit(1)

    # Load embeddings and metadata
    train_path = file_paths.get("train_embeddings_path")
    test_path = file_paths.get("test_embeddings_path")
    metadata_path = file_paths.get("metadata_path")

    if not (train_path and test_path and metadata_path):
        logger.error("Missing file paths")
        exit(1)

    # Load train and test embeddings
    X_train, y_train = load_embeddings(train_path)
    X_test, y_test = load_embeddings(test_path)
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train)
    y_test = label_encoder.transform(y_test)

    if X_train is None or y_train is None or X_test is None or y_test is None:
        logger.error("Failed to load embeddings")
        exit(1)

    # Load metadata
    metadata = load_metadata(metadata_path)
    if metadata is None:
        logger.error("Failed to load metadata")
        exit(1)

    logger.info(f"Loaded train embeddings with shape: {X_train.shape}")
    logger.info(f"Loaded test embeddings with shape: {X_test.shape}")

    # Train the model
    logger.info("Training XGBoost model...")
    model = train_xgboost_model(X_train, y_train, X_test, y_test)

    # Get the accuracy from the latest run
    client = MlflowClient(tracking_uri=mlflow_uri)
    experiment = client.get_experiment_by_name("XGBoost Model with Similarity")

    if not experiment:
        logger.error("No experiment found for XGBoost Model with Similarity")
        exit(1)

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time DESC"]
    )

    if not runs:
        logger.error("No runs found for the experiment")
        exit(1)

    latest_run = runs[0]
    new_accuracy = latest_run.data.metrics.get("accuracy", 0.0)

    # Get the best model metrics
    best_metrics = get_best_model_metrics()

    if best_metrics is None:
        # If no previous model exists, save the new model
        logger.info("No previous model found. Saving the new model.")
        save_model(model)
        exit(0)

    # Compare the new model to the best model
    best_accuracy = best_metrics.get("accuracy", 0.0)

    logger.info(f"New model accuracy: {new_accuracy}")
    logger.info(f"Best model accuracy: {best_accuracy}")

    if new_accuracy > best_accuracy:
        logger.info("New model performs better than the best model. Saving...")
        save_model(model)
    else:
        logger.info("New model does not perform better than the best model. Not saving.")

if __name__ == "__main__":
    main()
