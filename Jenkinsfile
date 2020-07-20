#!/usr/bin/env groovy

pipeline {
  agent any

  options {
    timeout(time: 30, unit: 'MINUTES')
  }

  triggers {
    cron('H 4 * * *')
  }

  stages {
    stage('Build Docker Agent Plugin Images') {
      matrix {
        agent any
        axes {
          axis {
            name 'AGENT_PLUGIN'
            values 'jmeter', 'http', 'ping'
          }
        }
      } 
      stages {
        stage('Build and Push Docker Agent Images') { 
          steps {
            script {
              dir(AGENT_PLUGIN) {
                dockerImage = docker.build("radonconsortium/radon-ctt-agent:${AGENT_PLUGIN}")
                withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                  dockerImage.push(AGENT_PLUGIN)
                }
              }
            }
          }
        }
      }
    }
  }
}

