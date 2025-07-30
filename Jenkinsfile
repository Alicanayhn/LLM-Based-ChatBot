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
                    docker compose up --build -d
                '''
                
            }
        }
    }
}
