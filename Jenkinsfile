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
        DOCKER_IMAGE = "host.docker.internal:8082/docker-repo/jewelry-app"
        NEXUS_CREDENTIALS = 'nexus-credentials'
    }

    stages {

        stage('Prepare Workspace') {
            steps {
                sh '''
                    echo ">>> Marking workspace as safe for Git..."
                    git config --global --add safe.directory /var/jenkins_home/workspace/Jewelry-App-Pipeline
                '''
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${commitHash}-${env.BUILD_NUMBER}"

                    // Login ל־Nexus באמצעות HTTP
                    withCredentials([usernamePassword(credentialsId: NEXUS_CREDENTIALS, usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
                        sh 'echo $NEXUS_PASS | docker login -u $NEXUS_USER --password-stdin http://host.docker.internal:8082'
                    }

                    // Build & push
                    buildAndPush(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS)
                }
            }
        }

        stage('Quality & Tests') {
            steps {
                script {
                    runTests(DOCKER_IMAGE, env.IMAGE_TAG)
                    sh '''
                        python3 -m pip install -r requirements.txt
                        python3 -m pylint *.py --rcfile=.pylintrc || true
                    '''
                }
            }
        }

        stage('Security Scan (Snyk)') {
            steps {
                withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                    sh """
                        echo ">>> Scanning Docker image ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                        snyk container test ${DOCKER_IMAGE}:${IMAGE_TAG} --file=Dockerfile --severity-threshold=high
                    """
                }
            }
        }

        stage('Deploy App') {
            steps {
                script {
                    deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'dev')
                }
            }
        }

        stage('Promote to Staging') {
            when { branch 'main' }
            steps {
                input message: 'Deploy to Staging?', ok: 'Yes, Deploy'
                script {
                    deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'staging')
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
