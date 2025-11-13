pipeline {
    agent any 

    environment {
        VENV_DIR = 'venv_project_2'
    }
    stages {

        stage("Cloning from Github........."){
            steps{
                script{
                    echo "Cloning from Github............."
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-tokens', url: 'https://github.com/Joseph-Charles2/anime-recommendation-system-mlops-project.git']])
                }
            }
        }

        stage("Making a Virtual Environment.........")
        {
            steps{
                script{
                    echo "Making a Virtual Environment........."
                    sh '''
                    python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip 
                    pip install -e .
                    pip install dvc
                     '''
                }       
            }
        }

        stage('DVC Pull')
        {
            steps 
            {
                withCredentials([file(credentialsId:'gcp-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')])
                {
                    script 
                    {
                        echo "DVC PUll...."
                        sh ''' 
                        . ${VENV_DIR}/bin/activate
                        dvc pull
                        '''


                    }
                }
            }
            
        }


    }


}