pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -v ${WORKSPACE}:/app'
        }
    }

    environment {
        // Environment variables from Jenkins credentials
        GOOGLE_APPLICATION_CREDENTIALS = credentials('gcp-credentials')
        GCP_BUCKET_NAME = "${params.GCP_BUCKET_NAME ?: env.GCP_BUCKET_NAME ?: 'resumatrix-embeddings'}"
        GCP_PROJECT_ID = "${params.GCP_PROJECT_ID ?: env.GCP_PROJECT_ID ?: 'awesome-nimbus-452221-v2'}"
        MLFLOW_TRACKING_URI = "${params.MLFLOW_TRACKING_URI ?: env.MLFLOW_TRACKING_URI ?: 'http://mlflow:5000'}"
        ARTIFACT_REGISTRY_REPO = "${params.ARTIFACT_REGISTRY_REPO ?: env.ARTIFACT_REGISTRY_REPO ?: 'us-east1-docker.pkg.dev/' + GCP_PROJECT_ID + '/resume-fit-supervised/xgboost_and_cosine_similarity'}"
        MODEL_TAG = "xgboost-model-${BUILD_NUMBER}"
    }

    triggers {
        // Poll GCS bucket for changes every hour
        pollSCM('H * * * *')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r retraining_pipeline/requirements.txt'
                sh 'mkdir -p data model_registry'
            }
        }

        stage('Download from GCS') {
            steps {
                sh 'python retraining_pipeline/download_from_gcs.py'
            }
        }

        stage('Run Retraining') {
            steps {
                sh 'python retraining_pipeline/run_retraining.py'
            }
        }

        stage('Push to Artifact Registry') {
            when {
                // Only run this stage if a new model was saved
                expression { return fileExists('model_registry/new_model_saved.txt') }
            }
            steps {
                script {
                    // Build the Docker image
                    sh "docker build -t ${ARTIFACT_REGISTRY_REPO}:${MODEL_TAG} -f retraining_pipeline/Dockerfile ."

                    // Authenticate with Google Artifact Registry
                    sh 'gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}'
                    sh 'gcloud auth configure-docker us-east1-docker.pkg.dev'

                    // Push the image to Google Artifact Registry
                    sh "docker push ${ARTIFACT_REGISTRY_REPO}:${MODEL_TAG}"

                    // Tag as latest if needed
                    sh "docker tag ${ARTIFACT_REGISTRY_REPO}:${MODEL_TAG} ${ARTIFACT_REGISTRY_REPO}:latest"
                    sh "docker push ${ARTIFACT_REGISTRY_REPO}:latest"
                }
            }
        }
    }

    post {
        always {
            // Clean up
            sh 'rm -f ${GOOGLE_APPLICATION_CREDENTIALS}'
            cleanWs()
        }

        success {
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}
