#!groovy

node {
    stage("Source") {
        checkout scm
    }

    stage("Build") {

        stage("Initialize virtualenv") {
            sh "rm -rf venv"
            sh "python3 -m venv venv"
            sh "venv/bin/pip install -U wheel pip"
            sh "venv/bin/pip install -r requirements.txt"
        }

        stage("Build GOV.UK assets") {
            sh "venv/bin/python manage.py install_all_govuk_assets"
        }
    }

    stage("Test") {
        try{
            sh "venv/bin/python test"

        } catch(err) {
            if (currentBuild.result == 'UNSTABLE') {
                currentBuild.result == 'FAILURE'
            }

            throw err
        }
    }

    stage("Deploy") {
        def paasUser = 'f8b4788a-0383-4c2a-ba4f-64415628debb'

        withEnv(["CF_APPNAME=sue-my-brother"]) {
            withCredentials([
                usernamePassword(
                    credentialsId: paasUser,
                    usernameVariable: 'CF_USER',
                    passwordVariable: 'CF_PASSWORD')]) {

                ansiColor('xterm') {
                    sh "./deploy-to-paas"
                }
            }
        }
    }
}
