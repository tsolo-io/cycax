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
		sh (label: 'Run MyPy',
		    script: '''
			    mkdir -p logs
			    hatch run lint:typing | tee logs/mypy.log
			    '''
		)
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
