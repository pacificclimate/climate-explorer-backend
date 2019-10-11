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

    stage('Build Image') {
        String image_name = 'climate-explorer-backend'
        String branch_name = BRANCH_NAME.toLowerCase()

        // Update image name if we are not on the master branch
        if (branch_name != 'master') {
            image_name = image_name + '/' + branch_name
        }

        withDockerServer([uri: PCIC_DOCKER]) {
            def image = docker.build(image_name)
        }
    }
}
