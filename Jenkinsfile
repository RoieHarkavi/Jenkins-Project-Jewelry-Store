@Library('jewelry-shared-lib') _

pipeline {
    agent {
        docker {
            image 'roieharkavi/jewelry-agent:latest'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    triggers {
        GenericTrigger(
            genericVariables: [
                [key: 'branch', value: '$.ref']
            ],
            causeString: 'Triggered on $branch',
            token: 'my-token',
            printContributedVariables: true,
            printPostContent: true
        )
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
                sh '''
                    echo ">>> Marking workspace as safe for Git..."
                    git config --global --add safe.directory /var/jenkins_home/workspace/Jewelry-App-Pipeline
                '''
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                script {
                    env.IMAGE_TAG = buildAndPush(DOCKER_IMAGE, NEXUS_CREDENTIALS)
                }
            }
        }

        stage('Quality & Tests') {
            steps {
                sh '''
                    python3 -m pip install -r requirements.txt
                    python3 -m pylint *.py --rcfile=.pylintrc || true
                '''
            }
        }

        stage('Security Scan') {
            steps {
                withCredentials([string(credentialsId: 'snyk-token', variable: 'SNYK_TOKEN')]) {
                    sh "snyk container test ${DOCKER_IMAGE}:${IMAGE_TAG} --file=Dockerfile --severity-threshold=high"
                }
            }
        }

        stage('Deploy') {
            steps {
                deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'dev')
            }
        }

        stage('Promote to Staging') {
            when { branch 'main' }
            steps {
                input message: 'Deploy to Staging?', ok: 'Yes'
                deployApp(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS, 'staging')
            }
        }
    }

    post {
        always {
            echo ">>> Cleaning up Docker images..."
            sh "docker rmi \$(docker images -q ${DOCKER_IMAGE}) || true"
            cleanWs()
        }
    }
}
