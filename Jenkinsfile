pipeline {
    agent {
        docker {
            image 'roieharkavi/jenkins-agent:latest'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
            }
        }

        stage('Build Images') {
            steps {
                echo 'Building Docker images for all services...'
                sh 'docker-compose build'
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running tests inside containers...'
                sh 'docker-compose run --rm backend-service pytest'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying services...'
                sh 'docker-compose up -d'
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished. Cleaning up...'
            sh 'docker-compose down' 
        }

        success {
            echo 'Pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed.'
        }
    }
}
