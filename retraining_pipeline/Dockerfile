FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY retraining_pipeline/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Create directories for data and model registry
RUN mkdir -p /app/data /app/model_registry

# Set environment variables for the application
ENV DATA_DIR=/app/data \
    MODEL_REGISTRY_DIR=/app/model_registry \
    PYTHONPATH=/app \
    GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json \
    MLFLOW_TRACKING_URI=http://localhost:5000

# Create a directory for GCP credentials
RUN mkdir -p /app/credentials

# Default command
CMD ["python", "retraining_pipeline/run_retraining.py"]
