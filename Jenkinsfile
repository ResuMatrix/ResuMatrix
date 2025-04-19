pipeline {
    agent any

    environment {
        GCP_PROJECT_ID = credentials('GCP_PROJECT_ID')
        GCP_JSON_PATH = credentials('GCP_JSON_PATH')
        SUPABASE_URL = credentials('SUPABASE_URL')
        SUPABASE_KEY = credentials('SUPABASE_KEY')
        GCP_BUCKET_NAME = credentials('GCP_BUCKET_NAME')
        MLFLOW_TRACKING_URI = "http://localhost:5001"
        DOCKER_BUILDKIT = "1"
        VENV_PATH = "${WORKSPACE}/.venv"
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

        stage('Setup Environment') {
            steps {
                script {
                    // Create .env file for docker-compose
                    sh '''
                    cat > .env << EOF
                    GCP_PROJECT_ID=${GCP_PROJECT_ID}
                    GCP_JSON_PATH=${GCP_JSON_PATH}
                    GCP_BUCKET_NAME=${GCP_BUCKET_NAME}
                    SUPABASE_URL=${SUPABASE_URL}
                    SUPABASE_KEY=${SUPABASE_KEY}
                    MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
                    EOF
                    '''

                    // Ensure directories exist
                    sh '''
                    mkdir -p retraining_pipeline/data
                    mkdir -p retraining_pipeline/model_registry
                    mkdir -p retraining_pipeline/mlflow
                    '''

                    // Create and activate virtual environment
                    sh '''
                    python -m venv ${VENV_PATH}
                    . ${VENV_PATH}/bin/activate
                    pip install --upgrade pip
                    pip install -r retraining_pipeline/requirements.txt
                    '''
                }
            }
        }

        stage('Download Embeddings') {
            steps {
                dir('retraining_pipeline') {
                    sh 'python download_from_gcs.py'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('retraining_pipeline') {
                    sh 'docker-compose build'
                }
            }
        }

        stage('Run Retraining Pipeline') {
            steps {
                dir('retraining_pipeline') {
                    sh 'docker-compose up --abort-on-container-exit'
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
                dir('retraining_pipeline') {
                    sh 'python push_to_artifactory.py'
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
            cleanWs()
        }
    }
}
