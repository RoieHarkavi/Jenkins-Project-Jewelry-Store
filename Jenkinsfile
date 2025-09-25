@Library('jewelry-shared-lib') _

properties([
    pipelineTriggers([
        [$class: 'GenericTrigger',
         genericVariables: [],
         causeString: 'Triggered on GitHub push',
         token: 'MY_WEBHOOK_TOKEN',
         printContributedVariables: true,
         printPostContent: true,
         regexpFilterText: '$ref',
         regexpFilterExpression: 'refs/heads/main']
    ])
])

pipeline {
    agent any  // הרצה על node כלשהו, אין צורך ב-agent docker
    options {
        buildDiscarder(logRotator(daysToKeepStr: '30'))
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        DOCKER_IMAGE = "nexus:8082/docker-repo/jewelry-app"
        NEXUS_CREDENTIALS = 'nexus-credentials'
        SNYK_CREDENTIALS = 'snyk-token'
    }

    stages {
        stage('Build & Push Docker Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${commitHash}-${env.BUILD_NUMBER}"

                    // שימוש ב־withRegistry כדי להתחבר ל־Nexus
                    withCredentials([usernamePassword(credentialsId: NEXUS_CREDENTIALS,
                                                     usernameVariable: 'NEXUS_USER',
                                                     passwordVariable: 'NEXUS_PASS')]) {
                        docker.withRegistry('http://nexus:8082', NEXUS_CREDENTIALS) {
                            def img = docker.build("${DOCKER_IMAGE}:${IMAGE_TAG}")
                            img.push()
                            img.push('latest')
                        }
                    }
                }
            }
        }

        stage('Quality & Tests') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${IMAGE_TAG}").inside {
                        sh 'python3 -m pip install -r requirements.txt'
                        sh 'python3 -m pytest --junitxml results.xml tests/*.py'
                        sh 'python3 -m pylint *.py --rcfile=.pylintrc || true'
                    }
                    junit allowEmptyResults: true, testResults: 'results.xml'
                }
            }
        }

        stage('Security Scan (Snyk)') {
            steps {
                withCredentials([string(credentialsId: SNYK_CREDENTIALS, variable: 'SNYK_TOKEN')]) {
                    sh """
                        echo ">>> Scanning Docker image ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                        snyk container test ${DOCKER_IMAGE}:${IMAGE_TAG} --file=Dockerfile --severity-threshold=high
                    """
                }
            }
        }
