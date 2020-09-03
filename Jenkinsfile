#!/usr/bin/env groovy

pipeline {
  agent none

  options {
    timeout(time: 30, unit: 'MINUTES')
  }

  triggers {
    cron('H 4 * * *')
  }

  environment {
    DOCKER_ORG = 'radonconsortium'
    DOCKER_REPO = 'radon-ctt-agent'
    DOCKER_FQN = "${DOCKER_ORG}/${DOCKER_REPO}"
  }

  stages {
    stage('Pull Docker Agent Base Image') {
      agent any
      steps {
        sh "docker pull ${DOCKER_FQN}:base"
      }
    }

    stage('Build Docker Agent Plugin Images') {
      matrix {
        agent any
        axes {
          axis {
            name 'AGENT_PLUGIN'
            values 'jmeter', 'http', 'ping'
          }
        }
        stages {
          stage('Build and Push Docker Agent Images') { 
            steps {
              script {
                dir("${AGENT_PLUGIN}") {
                  dockerImage = docker.build("${DOCKER_FQN}:${AGENT_PLUGIN}")
                  withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                    dockerImage.push()
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

