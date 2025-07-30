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
        stage('Set env and Install requirements') {
            steps {
                sh '''
                    python -m venv $VENV
                    . $VENV/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements.txt
                '''
            }
        }
    }
}
