pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'wget -c https://files.openscad.org/OpenSCAD-2021.01-x86_64.AppImage -O ~/Applications/OpenSCAD-2021.01-x86_64.AppImage'
                sh 'wget -c https://github.com/FreeCAD/FreeCAD-Bundle/releases/download/0.20.2/FreeCAD_0.20.2-2022-12-27-conda-Linux-x86_64-py310.AppImage -O ~/Applications/FreeCAD_0.20.2-2022-12-27-conda-Linux-x86_64-py310.AppImage'
                sh 'chmod a+x ~/Applications/*.AppImage'
            }
        }
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
                     reportName: 'CyCAx docs',
                     reportTitles: 'CyCAx docs'
                  ])
                }
            }
        }
        stage('PyTest') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE', message: "One or more tests failed at this stage.") {
                    sh "hatch run cov"
                }
                    
            }
            post {
                always{
                    junit 'reports/tests.xml'
                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
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
    }
}
