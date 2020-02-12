@Library('pcic-pipeline-library')_


node {
    stage('Code Collection') {
        collectCode()
    }

    stage('Python Test Suite') {
        runPythonTestSuite('pcic/geospatial-python', ['requirements.txt'], '-v')
    }

    stage('Clean Workspace') {
        cleanWs()
    }

    stage('Re-collect Code') {
        collectCode()
    }

    def image
    def imageName
    def imageSuffix = 'climate-explorer-backend'

    stage('Build Image') {
        (image, imageName) = buildDockerImage(imageSuffix)
    }

    stage('Publish Image') {
        publishDockerImage(image, 'PCIC_DOCKERHUB_CREDS')
    }

    // Only conduct security scan on branches filed as pull requests
    if(BRANCH_NAME.contains('PR') || BRANCH_NAME == 'master') {
        stage('Security Scan') {
            writeFile file: 'anchore_images', text: getScanName(imageSuffix)
            anchore name: 'anchore_images', engineRetries: '700'
        }
    }

    stage('Clean Local Image') {
        removeDockerImage(imageName)
    }

    stage('Clean Workspace') {
        cleanWs()
    }
}
