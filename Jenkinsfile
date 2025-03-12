pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "docker-test-v05"
        GITHUB_REPO = "https://github.com/ResuMatrix/ResuMatrix.git"
        GITHUB_BRANCH = "docker-integration"
        LOGS_PATH = "/app/logs"
        LOCAL_LOGS = "C:/NEU Courses/IE7374_MLOps/ResuMatrix"
        EMAIL_RECIPIENTS = "mlops.team20@gmail.com"
    }

    stages {

        stage('Pull latest code') {

            steps {
                echo "Pulling latest code from GitHub..."
                sh """
                rm -rf ResuMatrix
                git clone -b ${GITHUB_BRANCH} ${GITHUB_REPO} ResuMatrix
                """
            }
        }

        stage('Build Docker image') {
            steps {
                echo "Building Docker image..."
                sh """
                cd ResuMatrix
                docker build -t ${DOCKER_IMAGE} .
                """
            }
        }

        stage('Run Docker container') {
            steps {
                echo "Running Docker container..."
                sh """
                docker run --rm -v "${LOCAL_LOGS}/logs:/app/logs" ${DOCKER_IMAGE}
                """
            }
        }

        stage('Archive Logs') {
            steps {
                echo "Archiving logs..."
                archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
            }
        }

        stage('Clean up') {
            steps {
                echo "Cleaning up Docker containers..."
                sh """
                docker ps -aq | xargs -r docker stop || true
                docker ps -aq | xargs -r docker rm || true
                """
            }
        }
    }

    post {
        success {
            echo "Job succeeded. Logs captured."
            emailext (
                subject: "Jenkins Build SUCCESS: Docker Build Successful",
                body: """
                    ✅ Build Completed Successfully 
                    - **Git Branch:** ${GITHUB_BRANCH}
                    - **Docker Image:** ${DOCKER_IMAGE}
                    - **Logs Path:** ${LOCAL_LOGS}/logs
                    - **Build URL:** ${env.BUILD_URL}
                    
                    **Please check the logs for more details.**
                """,
                to: "${EMAIL_RECIPIENTS}"
            )
        }
        failure {
            echo "Job failed. Logs captured."
            emailext (
                subject: "Jenkins Build FAILED: Docker Build Failed",
                body: """
                    ❌ Build Failed 
                    - **Git Branch:** ${GITHUB_BRANCH}
                    - **Docker Image:** ${DOCKER_IMAGE}
                    - **Logs Path:** ${LOCAL_LOGS}/logs
                    - **Build URL:** ${env.BUILD_URL}
                    
                    **Please investigate the logs and resolve the issue.**
                """,
                to: "${EMAIL_RECIPIENTS}"
            )
        }
    }
}