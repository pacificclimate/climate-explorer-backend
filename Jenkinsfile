node {
    stage('Code Collection') {
        checkout scm
    }

    withDockerServer([uri: PCIC_DOCKER]) {
        // Use image with gdal already installed
        def gdalenv = docker.image('pcic/geospatial-python')

        gdalenv.inside('-u root') {
            stage('Python Installs') {
                sh 'pip3 install -i https://pypi.pacificclimate.org/simple/ -r requirements.txt'
                sh 'pip3 install pytest'
                sh 'pip3 install -e .'
            }

            stage('Python Test Suite') {
                sh 'py.test -v'
            }
        }
    }

    stage('Clean Workspace') {
        cleanWs()
    }

    stage('Recollect Code') {
        checkout scm
    }

    def image
    String name = BASE_REGISTRY + 'climate-explorer-backend'

    // tag branch
    if (BRANCH_NAME == 'master') {
        // TODO: detect tags and releases for master
    } else {
        name = name + ':' + BRANCH_NAME + "_${BUILD_ID}"
    }

    stage('Build and Publish Image') {
        withDockerServer([uri: PCIC_DOCKER]) {
            image = docker.build(name)

            docker.withRegistry('', 'PCIC_DOCKERHUB_CREDS') {
                image.push()
            }
        }
    }

    stage('Security Scan') {
        writeFile file: 'anchore_images', text: name
        anchore name: 'anchore_images', engineRetries: '700'
    }

    stage('Clean Up Local Image') {
        withDockerServer([uri: PCIC_DOCKER]){
            sh "docker rmi ${name}"
        }
    }
}
