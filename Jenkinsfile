pipeline {
    agent any 

    stages {

        stage("Cloning from Github........."){
            steps{
                script{
                    echo "Cloning from Github............."
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-tokens', url: 'https://github.com/Joseph-Charles2/anime-recommendation-system-mlops-project.git']])
                }
            }
        }
    }
}