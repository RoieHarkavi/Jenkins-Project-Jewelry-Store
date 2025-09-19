pipeline {
    agent {
        docker {
            image 'roieharkavi/jewelry-agent:latest'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    options {
        buildDiscarder(logRotator(daysToKeepStr: '30'))
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        DOCKER_IMAGE = "roieharkavi/jewelry-app"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    def imageTag   = "${commitHash}-${env.BUILD_NUMBER}"

                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                                     usernameVariable: 'DOCKER_USER',
                                                     passwordVariable: 'DOCKER_PASS')]) {
                        sh """
                            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                            docker build -t ${DOCKER_IMAGE}:${imageTag} -t ${DOCKER_IMAGE}:latest .
                            docker push ${DOCKER_IMAGE}:${imageTag}
                            docker push ${DOCKER_IMAGE}:latest
                        """
                    }
                    env.IMAGE_TAG = imageTag
                }
            }
        }

        stage('Unit Tests inside Docker') {
            steps {
                script {
                    sh """
                        docker run --rm ${DOCKER_IMAGE}:${env.IMAGE_TAG} \
                        bash -c "pip3 install -r requirements.txt && python3 -m pytest --junitxml results.xml tests/*.py"
                    """
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'results.xml'
                }
            }
        }
    }

    post {
        always {
            echo ">>> Cleaning up Docker images..."
            sh "docker rmi \$(docker images -q ${DOCKER_IMAGE}) || true"
            echo ">>> Cleaning workspace..."
            cleanWs()
        }
    }
}
