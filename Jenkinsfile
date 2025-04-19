pipeline {
    agent any

    environment {
        // Use Jenkins credentials for sensitive values
        GCP_PROJECT_ID = credentials('GCP_PROJECT_ID')
        GCP_JSON_PATH = credentials('GCP_JSON_PATH')
        SUPABASE_URL = credentials('SUPABASE_URL')
        SUPABASE_KEY = credentials('SUPABASE_KEY')
        GCP_BUCKET_NAME = credentials('GCP_BUCKET_NAME')
        MLFLOW_TRACKING_URI = "http://localhost:5050"
        DOCKER_BUILDKIT = "1"
        VENV_PATH = "${WORKSPACE}/.venv"
        // Add common Python paths
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:${PATH}"
        // Docker image details
        DOCKER_IMAGE = "us-east1-docker.pkg.dev/${GCP_PROJECT_ID}/resume-fit-supervised/xgboost_and_cosine_similarity:latest"
        // Email for notifications
        EMAIL_ADDRESS = "mlops.team20@gmail.com"
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Validate Credentials') {
            steps {
                script {
                    // Check if credentials are properly set up
                    // Note: We're only checking if they're non-empty, not their validity
                    if (!env.GCP_PROJECT_ID?.trim()) {
                        error "GCP_PROJECT_ID credential is not set up in Jenkins"
                    }
                    if (!env.GCP_JSON_PATH?.trim()) {
                        error "GCP_JSON_PATH credential is not set up in Jenkins"
                    }
                    if (!env.SUPABASE_URL?.trim()) {
                        error "SUPABASE_URL credential is not set up in Jenkins"
                    }
                    if (!env.SUPABASE_KEY?.trim()) {
                        error "SUPABASE_KEY credential is not set up in Jenkins"
                    }
                    if (!env.GCP_BUCKET_NAME?.trim()) {
                        error "GCP_BUCKET_NAME credential is not set up in Jenkins"
                    }
                    
                    // Log non-sensitive parts of credentials for debugging
                    echo "Using GCP Project ID: ${env.GCP_PROJECT_ID}"
                    echo "Using GCP Bucket: ${env.GCP_BUCKET_NAME}"
                    echo "Using Supabase URL: ${env.SUPABASE_URL}"
                }
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                # Check for Python installations
                echo "Checking for Python installations..."
                echo "PATH: $PATH"
                
                # Try different Python commands
                if command -v python3 &> /dev/null; then
                    echo "python3 found at: $(which python3)"
                    echo "python3 version: $(python3 --version)"
                    PYTHON_CMD="python3"
                elif command -v python &> /dev/null; then
                    echo "python found at: $(which python)"
                    echo "python version: $(python --version)"
                    PYTHON_CMD="python"
                else
                    echo "ERROR: No Python installation found!"
                    echo "Checking common locations..."
                    ls -la /usr/bin/python* || true
                    ls -la /usr/local/bin/python* || true
                    ls -la /opt/homebrew/bin/python* || true
                    exit 1
                fi
                
                # Create directories
                mkdir -p retraining_pipeline/data
                mkdir -p retraining_pipeline/model_registry
                mkdir -p retraining_pipeline/mlflow
                
                # Create virtual environment
                $PYTHON_CMD -m venv ${VENV_PATH}
                . ${VENV_PATH}/bin/activate
                
                # Install dependencies
                python -m pip install --upgrade pip
                
                # Create a minimal requirements file without torch and transformers
                cat > retraining_pipeline/requirements_minimal.txt << EOF
                scikit-learn>=1.0.0
                xgboost>=1.5.0
                mlflow>=2.0.0
                imbalanced-learn>=0.8.0
                google-cloud-storage>=2.0.0
                pandas>=1.3.0
                numpy>=1.20.0
                joblib>=1.0.0
                nltk>=3.6.0
                python-dotenv>=0.19.0
                EOF
                
                # Try to install with full requirements first
                echo "Attempting to install full requirements..."
                if ! python -m pip install -r retraining_pipeline/requirements.txt; then
                    echo "Full requirements installation failed. Using minimal requirements..."
                    python -m pip install -r retraining_pipeline/requirements_minimal.txt
                fi
                
                # Always install these core packages
                python -m pip install google-cloud-storage python-dotenv
                '''
                
                // Create .env file for docker-compose
                script {
                    def gcp_json_path = env.GCP_JSON_PATH
                    
                    // Check if GCP_JSON_PATH is a JSON string rather than a file path
                    if (gcp_json_path.startsWith('{') && gcp_json_path.endsWith('}')) {
                        // It's a JSON string, write it to a file
                        writeFile file: "${WORKSPACE}/gcp-credentials.json", text: gcp_json_path
                        gcp_json_path = "${WORKSPACE}/gcp-credentials.json"
                        echo "Created GCP credentials file at ${gcp_json_path}"
                    } else {
                        echo "Using GCP credentials from path: ${gcp_json_path}"
                    }
                    
                    // Create .env file using writeFile instead of shell
                    def envContent = """
                    GCP_PROJECT_ID=${GCP_PROJECT_ID}
                    GCP_JSON_PATH=${gcp_json_path}
                    GCP_BUCKET_NAME=${GCP_BUCKET_NAME}
                    SUPABASE_URL=${SUPABASE_URL}
                    SUPABASE_KEY=${SUPABASE_KEY}
                    MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
                    """.trim()
                    
                    writeFile file: "${WORKSPACE}/.env", text: envContent
                    echo "Created .env file at ${WORKSPACE}/.env"
                }
            }
        }

        stage('Download Data') {
            steps {
                script {
                    def gcp_json_path = env.GCP_JSON_PATH

                    sh """
                    # Activate virtual environment
                    . ${VENV_PATH}/bin/activate
                    
                    # Make sure required packages are installed
                    python -m pip install google-cloud-storage python-dotenv
                    
                    # Set environment variables
                    export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}
                    
                    # Print debug information
                    echo "GOOGLE_APPLICATION_CREDENTIALS: ${gcp_json_path}"
                    echo "Checking if credentials file exists:"
                    ls -la ${gcp_json_path} || echo "Credentials file not found!"
                    
                    # Run the script
                    cd retraining_pipeline
                    python download_from_gcs.py
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dir('retraining_pipeline') {
                        def gcp_json_path = env.GCP_JSON_PATH

                        sh """
                        # Set environment variables for Docker
                        export GCP_PROJECT_ID=${GCP_PROJECT_ID}
                        export GCP_JSON_PATH=${gcp_json_path}
                        export GCP_BUCKET_NAME=${GCP_BUCKET_NAME}
                        export SUPABASE_URL=${SUPABASE_URL}
                        export SUPABASE_KEY=${SUPABASE_KEY}
                        export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
                        export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}
                        
                        # Build the Docker image
                        docker-compose build
                        """
                    }
                }
            }
        }
        
        stage('Train Model') {
            steps {
                script {
                    dir('retraining_pipeline') {
                        def gcp_json_path = env.GCP_JSON_PATH

                        sh """
                        # Set environment variables for Docker
                        export GCP_PROJECT_ID=${GCP_PROJECT_ID}
                        export GCP_JSON_PATH=${gcp_json_path}
                        export GCP_BUCKET_NAME=${GCP_BUCKET_NAME}
                        export SUPABASE_URL=${SUPABASE_URL}
                        export SUPABASE_KEY=${SUPABASE_KEY}
                        export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
                        export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}
                        
                        # Run the Docker container
                        docker-compose up --abort-on-container-exit
                        """
                    }
                }
            }
        }

        stage('Evaluate Model') {
            steps {
                script {
                    def modelImproved = fileExists('retraining_pipeline/model_registry/new_model_saved.txt')
                    if (modelImproved) {
                        echo "New model performs better than previous model. Proceeding with artifact upload."
                    } else {
                        echo "New model does not perform better than previous model. Skipping artifact upload."
                        currentBuild.result = 'SUCCESS'
                        return
                    }
                }
            }
        }

        stage('Push to Artifact Registry') {
            when {
                expression {
                    return fileExists('retraining_pipeline/model_registry/new_model_saved.txt')
                }
            }
            steps {
                script {
                    def gcp_json_path = env.GCP_JSON_PATH

                    sh """
                    # Activate virtual environment
                    . ${VENV_PATH}/bin/activate
                    
                    # Make sure required packages are installed
                    python -m pip install google-cloud-storage python-dotenv
                    
                    # Set environment variables
                    export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}
                    export GCP_PROJECT_ID=${GCP_PROJECT_ID}
                    
                    # Print debug information
                    echo "GOOGLE_APPLICATION_CREDENTIALS: ${gcp_json_path}"
                    echo "Checking if credentials file exists:"
                    ls -la ${gcp_json_path} || echo "Credentials file not found!"
                    
                    # Run the script
                    cd retraining_pipeline
                    python push_to_artifactory.py
                    """
                }
            }
        }
        
        stage('Send Email Notification') {
            steps {
                script {
                    // Send email notification
                    echo "Email notification to ${EMAIL_ADDRESS}"
                }
            }
        }
    }

    post {
        success {
            script {
                // Send email for success
                emailext(
                    subject: "Pipeline Success: ${env.JOB_NAME} [${env.BUILD_NUMBER}]",
                    body: "The Jenkins pipeline has completed successfully.\n\nJob: ${env.JOB_NAME}\nBuild: ${env.BUILD_NUMBER}\nStatus: SUCCESS",
                    to: "${EMAIL_ADDRESS}"
                )
            }
        }
        failure {
            script {
                // Send email for failure
                emailext(
                    subject: "Pipeline Failure: ${env.JOB_NAME} [${env.BUILD_NUMBER}]",
                    body: "The Jenkins pipeline has failed.\n\nJob: ${env.JOB_NAME}\nBuild: ${env.BUILD_NUMBER}\nStatus: FAILURE\nPlease check the logs for details.",
                    to: "${EMAIL_ADDRESS}"
                )
            }
        }
        always {
            // Clean up virtual environment if it exists
            sh "rm -rf ${WORKSPACE}/.venv || true"
            // Clean workspace
            cleanWs()
        }
    }
}
