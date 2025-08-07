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
                withCredentials([string(credentialsId: 'ENV_FILE', variable: 'ENV_CONTENT')]) {
                    sh '''
                        echo "$ENV_CONTENT" > backend/.env
                        docker compose up --build -d
                    '''
                }
            }
        }
    }
}
