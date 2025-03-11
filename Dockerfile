# Use the official Python image from DockerHub
FROM python:3.11-slim

# Set environment variables
ENV VIRTUAL_ENV=/venv

# Create a virtual environment
RUN python3 -m venv $VIRTUAL_ENV

# Activate the virtual environment
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Git to pull the latest code from GitHub
RUN apt-get update && apt-get install -y git

# Set working directory inside the container
WORKDIR /app

# Adding logs directory
RUN mkdir -p /app/logs

# Pull the latest code from GitHub
# RUN git clone -b docker-integration https://github.com/ResuMatrix/ResuMatrix.git .
COPY . .

# Install dependencies from requirements.txt
RUN pip install --no-deps -r requirements.txt

# Ensure that every time the container starts, it pulls the latest code
CMD git -C /app pull && python src/test_code.py > logs/latest.log 2>&1 && cp logs/latest.log logs/log-$(date +%Y%m%d%H%M%S).log && echo "Execution complete. Shutting down container."
