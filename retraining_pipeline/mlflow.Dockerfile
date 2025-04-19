FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Git Python Refresh to quiet to avoid warnings
ENV GIT_PYTHON_REFRESH=quiet
ENV PYTHONUNBUFFERED=1

# Create directory for MLflow
RUN mkdir -p /mlflow

# Install MLflow and dependencies
RUN pip install mlflow>=2.0.0 scikit-learn pandas

# Expose port
EXPOSE 5000

# Set working directory
WORKDIR /mlflow

# Start MLflow server
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "/mlflow", "--default-artifact-root", "/mlflow"]
