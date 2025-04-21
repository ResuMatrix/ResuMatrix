FROM apache/airflow:2.10.5-python3.11

# Switch to root user for system dependencies
USER root

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq-dev \
        python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AIRFLOW_HOME=/opt/airflow

# Copy requirements file
COPY requirements.txt /requirements.txt

# Switch back to airflow user for pip installations
USER airflow

# Install Python packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary wheel setuptools && \
    pip install --no-cache-dir --prefer-binary -r /requirements.txt && \
    pip install --no-cache-dir --prefer-binary nltk && \
    pip install --no-cache-dir --prefer-binary torch==2.0.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --prefer-binary transformers==4.30.0 && \
    pip install --no-cache-dir --prefer-binary textstat>=0.7.3 && \
    python -m spacy download en_core_web_sm && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab')"

# Switch back to root to create directories and set permissions
USER root

# Create necessary directories
RUN mkdir -p /opt/airflow/data \
    /opt/airflow/logs \
    /opt/airflow/dags \
    /opt/airflow/scripts \
    /opt/airflow/config

# Set the correct permissions
RUN chown -R airflow: ${AIRFLOW_HOME}

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

USER root
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates gnupg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] \
      http://packages.cloud.google.com/apt cloud-sdk main" \
      | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
      | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get install -y google-cloud-sdk


# Switch back to the airflow user
USER airflow
WORKDIR ${AIRFLOW_HOME}
