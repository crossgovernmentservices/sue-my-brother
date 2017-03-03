#!groovy

import groovy.json.JsonSlurper


node {

    properties([
        parameters([
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
            sh "./run-tests"

        } catch(err) {
            if (currentBuild.result == 'UNSTABLE') {
                currentBuild.result == 'FAILURE'
            }

            throw err
        }
    }

    if (!BRANCH_NAME.startsWith('PR-')) {

        stage("Deploy") {
            def appName = cfAppName("sue-my-brother")

            stash(
                name: "app",
                includes: ".cfignore,Procfile,app/**,deploy-to-paas,lib/**,*.yml,migrations/**,*.txt,*.py,*.pem"
            )

            node("master") {

                unstash "app"

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
            if (GATEWAY_BRANCH != 'master') {
                appName = "${appName}-g-${GATEWAY_BRANCH}"
            }
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
