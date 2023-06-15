pipeline {
    agent any
    stages {
        stage('Build docs') {
            steps {
                sh 'hatch run docs:build'
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
