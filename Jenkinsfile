pipeline {
    agent any
    stages {
        stage('Build docs') {
            steps {
                sh 'haatch run docs:build'
            }
        }
    }
    post {
      success {
        publishHTML([allowMissing: false, 
		     alwaysLinkToLastBuild: false, 
                     keepAll: true, 
                     reportDir: 'docs/site', 
                     reportFiles: 'index.html', 
                     includes: '**/*', 
                     reportName: 'Cycax', 
                     reportTitles: 'Cycax report'
         ])
      }	
   }
}
