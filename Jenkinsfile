#!groovy

import groovy.json.JsonSlurper


node {

    properties([
        parameters([
            string(name: 'OIDC_CLIENT_ISSUER', defaultValue: 'https://ags-gateway.cloudapps.digital'),
            string(name: 'GATEWAY_BRANCH', defaultValue: ''),
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
        def appName = cfAppName("sue-my-brother")

        def config = registerOIDCClient(appName)

        withEnv(config) {
            retry(2) {
                deployToPaaS(appName)
            }
        }
    }
}


def cfAppName(appName) {

    def branch = "${BRANCH_NAME.replace('_', '-')}"

    if (BRANCH_NAME != 'master') {
        appName = "${appName}-${branch}"
    }

    try {
        if (GATEWAY_BRANCH) {
            appName = "${appName}-g-${GATEWAY_BRANCH}"
        }
    } catch (err) {
        // not a gateway dependent deploy, so do nothing
    }

    return appName
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
def parseOIDCCreds(def json) {
    def config = new groovy.json.JsonSlurper().parseText(json)
    [
        "OIDC_CLIENT_ID=${config['client_id']}",
        "OIDC_CLIENT_SECRET=${config['client_secret']}",
    ]
}


def registerOIDCClient(appName) {
    def url = "${OIDC_CLIENT_ISSUER}/oidc/registration"
    def json = "{\"redirect_uris\": [\"https://${appName}.cloudapps.digital/oidc_callback\"]}"

    def delay = 4
    def response = null
    timeout(time: 240, unit: 'SECONDS') {
        waitUntil {
            try {
                response = httpRequest(
                    contentType: 'APPLICATION_JSON',
                    httpMode: 'POST',
                    requestBody: json,
                    url: url
                )
                return true
            } catch (err) {
                sleep(time: delay, unit: 'SECONDS')
            }
            return false
        }
    }

    parseOIDCCreds(response.content)
}
