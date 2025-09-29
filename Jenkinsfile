@Library('jewelry-shared-lib') _

pipeline {
    agent {
        docker {
            image 'roieharkavi/jewelry-agent:latest'
            args '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        DOCKER_IMAGE = "localhost:8082/docker-repo/jewelry-app"
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
                    // מקבלים את ה־commit hash
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.IMAGE_TAG = "${commitHash}-${env.BUILD_NUMBER}"

                    // התחברות ל־Nexus
                    withCredentials([usernamePassword(credentialsId: NEXUS_CREDENTIALS, usernameVariable: 'NEXUS_USER', passwordVariable: 'NEXUS_PASS')]) {
                        sh '''
                            echo $NEXUS_PASS | docker login --username $NEXUS_USER --password-stdin http://localhost:8082
                        '''
                    }

                    // Build ו־Push
                    buildAndPush(DOCKER_IMAGE, env.IMAGE_TAG, NEXUS_CREDENTIALS)
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
