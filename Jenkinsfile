#!groovy

import groovy.json.JsonSlurper


node {

    properties([
        parameters([
            string(name: 'OIDC_CLIENT_ISSUER', defaultValue: 'https://ags-gateway.cloudapps.digital'),
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
                sh "venv/bin/pip install -r requirements.txt"
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

        config = registerOIDCClient(appName)

        withEnv([
            "OIDC_CLIENT_ID=${config['client_id']}",
            "OIDC_CLIENT_SECRET=${config['client_secret']}"]) {

            retry(2) {
                deployToPaaS(appName)
            }
        }
    }
}


def deployToPaaS(appName) {

    withEnv([
            "CF_APPNAME=${appName}",
            "SERVER_NAME=https://${appName}.cloudapps.digital"]) {
        withCredentials([
            usernamePassword(
                credentialsId: 'paas-deploy',
                usernameVariable: 'CF_USER',
                passwordVariable: 'CF_PASSWORD')]) {

            ansiColor('xterm') {
                sh "./deploy-to-paas"
            }
        }
    }
}


@NonCPS
def parseJson(def json) {
    def config = new groovy.json.JsonSlurper().parseText(json)
    [client_id: config['client_id'], client_secret: config['client_secret']]
}


def registerOIDCClient(appName) {
    def url = "${OIDC_CLIENT_ISSUER}/oidc/registration"
    def json = "{\"redirect_uris\": [\"https://${appName}.cloudapps.digital/oidc_callback\"]}"
    echo "POSTing ${json}"
    def response = httpRequest(contentType: 'APPLICATION_JSON', httpMode: 'POST', requestBody: json, url: url)
    config = parseJson(response.content)
    echo "Received client ID: ${config['client_id']}"
    return config
}
