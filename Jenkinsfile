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
      // matrix {
        agent any
      // axes {
      //  axis {
      //    name 'AGENT_PLUGIN'
      //    values 'http', 'jmeter', 'ping'
      //   }
      // }
      stages {
        stage('Build and Push http Docker Agent Images') { 
          steps {
            echo "Building http plugin."
            script {
              dir('http') {
                dockerImage = docker.build("${DOCKER_FQN}:http")
                withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                  dockerImage.push("http")
                }
              }
            }
          }
        }
        stage('Build and Push jmeter Docker Agent Images') { 
          steps {
            echo "Building jmeter plugin."
            script {
              dir('jmeter') {
                dockerImage = docker.build("${DOCKER_FQN}:jmeter")
                withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                  dockerImage.push("jmeter")
                }
              }
            }
          }
        }
        stage('Build and Push ping Docker Agent Images') { 
          steps {
            echo "Building ping plugin."
            script {
              dir('ping') {
                dockerImage = docker.build("${DOCKER_FQN}:ping")
                withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                  dockerImage.push("ping")
                }
              }
            }
          }
        }
      }
    }
  }
}


