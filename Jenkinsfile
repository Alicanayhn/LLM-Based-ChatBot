pipeline {
    agent any

    environment{
        VENV = 'venv'
    }
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
        stage('Build') {
            steps{
                sh '''
                   docker compose build 
                   docker compose up -d db mlflow
                '''
            }
        }
        stage("Test"){
            steps{
                sh '''
                    docker compose run --rm backend pytest -v test_app.py    
                '''
            }
        }
        stage("Down"){
            steps{
                sh '''
                    docker compose down
                '''
            }
        }
    }
}
