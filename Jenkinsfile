pipeline {
    agent any

    stages {
        stage('Docker-control') {
            steps {
                sh '''
                    docker version
                    docker info
                    docker container ls
                    docker network ls
                '''
            }
        }
        stage('Build'){
            steps{
                sh '''
                    pytest -v backend/test_ap.py
                '''
            }
        }
    }
}
