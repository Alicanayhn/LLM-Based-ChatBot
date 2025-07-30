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
        stage('TEST') {
            agent {
                docker { image 'python:3.10' }
            }
            steps{
                sh '''
                    python --version
                    python -m venv $VENV
                    . $VENV/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements.txt
                    pytest -v backend/test_app.py
                '''
            }
        }
    }
}
