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
        DOCKER_IMAGE = "nexus:8082/docker-repo/jewelry-app"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    def imageTag   = "${commitHash}-${env.BUILD_NUMBER}"

                    withCredentials([usernamePassword(credentialsId: 'nexus-credentials',
                                                     usernameVariable: 'NEXUS_USER',
                                                     passwordVariable: 'NEXUS_PASS')]) {
                        sh """
                            echo "$NEXUS_PASS" | docker login -u "$NEXUS_USER" --password-stdin nexus:8082
                            docker build -t ${DOCKER_IMAGE}:${imageTag} -t ${DOCKER_IMAGE}:latest .
                            docker push ${DOCKER_IMAGE}:${imageTag}
                            docker push ${DOCKER_IMAGE}:latest
                        """
                    }

                    env.IMAGE_TAG = imageTag
                }
            }
        }

        stage('Quality & Tests') {
            parallel {
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

                stage('Static Code Linting') {
                    steps {
                        script {
                            sh '''
                                python3 -m pip install -r requirements.txt
                                python3 -m pylint *.py --rcfile=.pylintrc || true
                            '''
                        }
                    }
                }
            }
        }

        stage('Security Scan (Snyk)') {
            steps {
                withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                    sh """
                        echo ">>> Scanning Docker image ${DOCKER_IMAGE}:${IMAGE_TAG} for vulnerabilities..."
                        snyk container test ${DOCKER_IMAGE}:${IMAGE_TAG} --file=Dockerfile --severity-threshold=high

                        # Optional: ignore vulnerabilities listed in snyk-ignore.yml
                        if [ -f snyk-ignore.yml ]; then
                            while IFS= read -r line; do
                                snyk ignore --id="$line"
                            done < snyk-ignore.yml
                        fi
                    """
                }
            }
        }

        stage('Deploy App') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'nexus-credentials',
                                                     usernameVariable: 'NEXUS_USER',
                                                     passwordVariable: 'NEXUS_PASS')]) {
                        sh """
                            echo "$NEXUS_PASS" | docker login -u "$NEXUS_USER" --password-stdin nexus:8082
                            docker pull ${DOCKER_IMAGE}:${IMAGE_TAG}
                            docker pull ${DOCKER_IMAGE}:latest
                            docker-compose -f docker-compose.yml up -d
                        """
                    }
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
