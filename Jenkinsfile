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
        stage('Install requirements'){
            steps{
                sh '''
                    pip install -r backend/requirement.txt
                '''
            }
        }
    }
}
