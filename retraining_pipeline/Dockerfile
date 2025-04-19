FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt ./

# Create minimal requirements file
RUN echo "scikit-learn>=1.0.0" > requirements_minimal.txt && \
    echo "xgboost>=1.5.0" >> requirements_minimal.txt && \
    echo "mlflow>=2.0.0" >> requirements_minimal.txt && \
    echo "imbalanced-learn>=0.8.0" >> requirements_minimal.txt && \
    echo "google-cloud-storage>=2.0.0" >> requirements_minimal.txt && \
    echo "pandas>=1.3.0" >> requirements_minimal.txt && \
    echo "numpy>=1.20.0" >> requirements_minimal.txt && \
    echo "joblib>=1.0.0" >> requirements_minimal.txt && \
    echo "nltk>=3.6.0" >> requirements_minimal.txt && \
    echo "python-dotenv>=0.19.0" >> requirements_minimal.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    (pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir -r requirements_minimal.txt)

# Copy the retraining pipeline code
COPY . .

# Create directories for data and model registry
RUN mkdir -p data model_registry mlflow

# Expose port for MLflow
EXPOSE 5000

# Set entrypoint
ENTRYPOINT ["python", "run_retraining.py"]
