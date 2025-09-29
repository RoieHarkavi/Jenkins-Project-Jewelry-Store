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

    environment {
        DOCKER_IMAGE = "nexus:8082/docker-repo/jewelry-app"
        NEXUS_CREDENTIALS = 'nexus-credentials'
    }

    options {
        buildDiscarder(logRotator(daysToKeepStr: '30'))
        disableConcurrentBuilds()
        timestamps()
    }

    stages {
        stage('Prepare Workspace') {
            steps {
                sh 'git config --global --add safe.directory /var/jenkins_home/workspace/Jewelry-App-Pipeline'
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${commitHash}-${env.BUILD_NUMBER}"

                    withCredentials([usernamePassword(credentialsId: NEXUS_CREDENTIALS, usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {

                        sh "docker login -u $NEXUS_USER -p $NEXUS_PASS http://nexus:8082"
                    }

                    buildAndPush(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS)
                }
            }
        }

        stage('Quality & Tests') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
                sh 'python3 -m pylint *.py --rcfile=.pylintrc || true'
            }
        }

        stage('Security Scan (Snyk)') {
            steps {
                withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                    sh "snyk container test ${DOCKER_IMAGE}:${IMAGE_TAG} --file=Dockerfile --severity-threshold=high"
                }
            }
        }

        stage('Deploy App') {
            steps {
                deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'dev')
            }
        }

        stage('Promote to Staging') {
            when { branch 'main' }
            steps {
                input message: 'Deploy to Staging?', ok: 'Yes, Deploy'
                deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'staging')
            }
        }
    }

    post {
        always {
            sh "docker rmi \$(docker images -q ${DOCKER_IMAGE}) || true"
            cleanWs()
        }
    }
}
