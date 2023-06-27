pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'hatch run docs:build'
		        sh 'cd src/cycax && hatch build'
		        sh 'pip install --force-reinstall $(ls dist/cycax-*.whl | sort | head -n1)'
            }
            post {
                 success {
                  publishHTML([allowMissing: false,
                     alwaysLinkToLastBuild: false,
                     keepAll: true,
                     reportDir: 'docs/site',
                     reportFiles: 'index.html',
                     includes: '**/*',
                     reportName: 'CyCAx docs',
                     reportTitles: 'CyCAx docs'
                  ])
                }
            }
        }
        stage('PyTest') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE', message: "One or more tests failed at this stage.") {
                    sh "hatch run coverage run -m pytest --junitxml=reports/test_results_cov.xml ./tests"
                }
                    
            }
            post {
                always{
                    junit 'reports/test_results_cov.xml'
                }
            }
        }
        stage('Mypy') {
            steps {
                sh "mkdir -p reports"
                sh "hatch run lint:typing 2>&1 | tee reports/mypy.txt"
                recordIssues(tools: [myPy(pattern: 'reports/mypy.txt', skipSymbolicLinks: true)])
            }
        }
        stage('Ruff') {
            steps {
                sh "hatch run lint:ruff check . --format=pylint 2>&1 | tee reports/ruff.txt"
                recordIssues(tools: [pyLint(pattern: 'reports/ruff.txt', skipSymbolicLinks: true)])
            }
        }
	stage('Test Coverage') {
	   steps {
	       catchError(buildResult: 'UNSTABLE', stageResult: 'SUCCESS') {
		        sh "python3 -m coverage xml -o reports/coverage.xml"
	       }
	   }
	   post {
	       always{
		        recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
	       }
	   }
	}
    }
}

