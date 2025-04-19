pipeline {
    agent any

    environment {
        // Use Jenkins credentials for sensitive values
        GCP_PROJECT_ID = credentials('GCP_PROJECT_ID')
        GCP_JSON_PATH = credentials('GCP_JSON_PATH')
        SUPABASE_URL = credentials('SUPABASE_URL')
        SUPABASE_KEY = credentials('SUPABASE_KEY')
        GCP_BUCKET_NAME = credentials('GCP_BUCKET_NAME')
        MLFLOW_TRACKING_URI = "http://localhost:5001"
        DOCKER_BUILDKIT = "1"
        VENV_PATH = "${WORKSPACE}/.venv"
        // Add common Python paths
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:${PATH}"
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

        stage('Check Python Installation') {
            steps {
                sh '''
                # Check for Python installations
                echo "Checking for Python installations..."
                echo "PATH: $PATH"

                # Try different Python commands
                if command -v python3 &> /dev/null; then
                    echo "python3 found at: $(which python3)"
                    echo "python3 version: $(python3 --version)"
                elif command -v python &> /dev/null; then
                    echo "python found at: $(which python)"
                    echo "python version: $(python --version)"
                else
                    echo "ERROR: No Python installation found!"
                    echo "Checking common locations..."
                    ls -la /usr/bin/python* || true
                    ls -la /usr/local/bin/python* || true
                    ls -la /opt/homebrew/bin/python* || true
                    exit 1
                fi
                '''
            }
        }

        stage('Setup Environment') {
            steps {
                script {
                    // Create .env file for docker-compose
                    // First, write the GCP credentials to a file if it's not a file path
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

                    // Ensure directories exist
                    sh '''
                    mkdir -p retraining_pipeline/data
                    mkdir -p retraining_pipeline/model_registry
                    mkdir -p retraining_pipeline/mlflow
                    '''

                    // Create and activate virtual environment
                    sh '''
                    # Find the Python executable (try python3 first, then python)
                    PYTHON_CMD="python3"
                    if ! command -v $PYTHON_CMD &> /dev/null; then
                        PYTHON_CMD="python"
                        if ! command -v $PYTHON_CMD &> /dev/null; then
                            echo "Error: Neither python3 nor python found in PATH"
                            exit 1
                        fi
                    fi
                    echo "Using Python command: $PYTHON_CMD"

                    # Create virtual environment
                    $PYTHON_CMD -m venv ${VENV_PATH}
                    . ${VENV_PATH}/bin/activate

                    # Install dependencies
                    python -m pip install --upgrade pip
                    python -m pip install -r retraining_pipeline/requirements.txt
                    python -m pip install google-cloud-storage python-dotenv
                    '''

                    // Set GOOGLE_APPLICATION_CREDENTIALS for the pipeline
                    sh "export GOOGLE_APPLICATION_CREDENTIALS=${WORKSPACE}/${GCP_JSON_PATH}"
                }
            }
        }

        stage('Download Embeddings') {
            steps {
                script {
                    // Use the GCP_JSON_PATH directly from the environment
                    def gcp_json_path = env.GCP_JSON_PATH

                    sh """
                    # Check if virtual environment exists
                    if [ ! -d "${VENV_PATH}" ]; then
                        echo "Error: Virtual environment not found at ${VENV_PATH}"
                        exit 1
                    fi

                    # Activate virtual environment
                    . ${VENV_PATH}/bin/activate

                    # Set environment variables
                    export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}

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
                        // Use the GCP_JSON_PATH directly from the environment
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

        stage('Run Retraining Pipeline') {
            steps {
                script {
                    dir('retraining_pipeline') {
                        // Use the GCP_JSON_PATH directly from the environment
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

        stage('Check Model Improvement') {
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

        stage('Push to Artifactory') {
            when {
                expression {
                    return fileExists('retraining_pipeline/model_registry/new_model_saved.txt')
                }
            }
            steps {
                script {
                    // Use the GCP_JSON_PATH directly from the environment
                    def gcp_json_path = env.GCP_JSON_PATH

                    sh """
                    # Check if virtual environment exists
                    if [ ! -d "${VENV_PATH}" ]; then
                        echo "Error: Virtual environment not found at ${VENV_PATH}"
                        exit 1
                    fi

                    # Activate virtual environment
                    . ${VENV_PATH}/bin/activate

                    # Set environment variables
                    export GOOGLE_APPLICATION_CREDENTIALS=${gcp_json_path}

                    # Run the script
                    cd retraining_pipeline
                    python push_to_artifactory.py
                    """
                }
            }
        }
    }

    post {
        success {
            emailext (
                subject: "SUCCESS: Model Retraining Pipeline",
                body: """
                <p>The model retraining pipeline has completed successfully.</p>
                <p>Build URL: ${BUILD_URL}</p>
                """,
                to: 'mlops.team20@gmail.com',
                mimeType: 'text/html'
            )
        }
        failure {
            emailext (
                subject: "FAILURE: Model Retraining Pipeline",
                body: """
                <p>The model retraining pipeline has failed.</p>
                <p>Build URL: ${BUILD_URL}</p>
                <p>Console Output: ${BUILD_URL}console</p>
                """,
                to: 'mlops.team20@gmail.com',
                mimeType: 'text/html'
            )
        }
        always {
            // Clean up virtual environment if it exists
            sh "rm -rf ${WORKSPACE}/.venv || true"
            // Clean workspace
            cleanWs()
        }
    }
}
