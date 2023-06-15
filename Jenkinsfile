pipeline {
    agent any
    stages {
        stage('Build docs') {
            steps {
                sh 'hatch run docs:build'
            }

	    post {
      		 success {
        	  publishHTML([allowMissing: false,
                     alwaysLinkToLastBuild: false,
                     keepAll: true,
                     reportDir: 'docs/site',
                     reportFiles: 'index.html',
                     includes: '**/*',
                     reportName: 'Cycax Docs',
                     reportTitles: 'Cycax Docs report'
                  ])
                }
            }	
        }
	stage('Mypy') {
	    steps {
		sh 'hatch run lint:typing | tee mypy.log'
	    }

	    post{
                always {
                  recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                  publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'logs/site', reportFiles: 'index.html', reportName: 'MyPy Logs', reportTitles: 'Cycax Mypy logs'])
                 }
             }
        }
    }
}
