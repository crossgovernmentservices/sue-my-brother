#!groovy

node {

    properties([
        parameters([
            string(name: 'OIDC_CLIENT_ISSUER', defaultValue: 'https://ags-gateway.cloudapps.digital'),
            string(name: 'OIDC_CLIENT_ID', defaultValue: 'test-client'),
            string(name: 'OIDC_CLIENT_SECRET', defaultValue: 'test-secret')
        ])
    ])

    stage("Source") {
        checkout scm
    }

    stage("Build") {

        parallel (

            "Initialize virtualenv": {
                sh "rm -rf venv"
                sh "python3 -m venv venv"
                sh "venv/bin/pip install -U pip"
                sh "venv/bin/pip install -r requirements/jenkins.txt"
            },

            "Build GOV.UK assets": {
                sh "./install-govuk-assets"
            }
        )
    }

    stage("Test") {
        try{
            sh "venv/bin/python manage.py test"

        } catch(err) {
            if (currentBuild.result == 'UNSTABLE') {
                currentBuild.result == 'FAILURE'
            }

            throw err
        }
    }

    stage("Deploy") {
        def appName = "sue-my-brother"

        if (BRANCH_NAME != 'master') {
            appName = "${appName}-${BRANCH_NAME.replace('_', '-')}"
        }

        retry(2) {
            deployToPaaS(appName)
        }
    }
}


def deployToPaaS(appName) {
    def paasUser = 'f8b4788a-0383-4c2a-ba4f-64415628debb'

    withEnv([
            "CF_APPNAME=${appName}",
            "SERVER_NAME=https://${appName}.cloudapps.digital"]) {
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
