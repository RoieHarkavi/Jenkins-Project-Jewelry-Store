pipeline {
    agent {
        docker {
            image 'roieharkavi/jenkins-agent:latest'
            // מחייב host עם Docker daemon והגדרות privileged
            args '--privileged -u root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    options {
        timestamps()
    }

    stages {
        stage('Verify Docker CLI') {
            steps {
                sh '''#!/bin/bash -l
                echo ">>> User: $(whoami)"
                echo ">>> PATH: $PATH"
                
                # בדיקה אם Docker CLI קיים
                which docker || { echo "docker CLI not found"; exit 1; }

                # בדיקה אם Docker CLI עובד
                docker --version || { echo "docker --version failed"; exit 1; }

                # בדיקה אם ניתן להתחבר ל-Docker daemon
                docker info || { echo "Cannot connect to Docker daemon"; exit 1; }
                '''
            }
        }
    }
}
