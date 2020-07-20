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
    stage('Pull base image') {
      steps {
        script {
          dockerImage = docker.pull("radonconsortium/radon-ctt-agent:base")
        }
      }
    }

    stage('Build Docker Agent Plugin Images') {
      parallel {
        stage('JMeter') {
          environment {
            dockerTag = 'jmeter'
          }
          steps {
            script {
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        }

        stage('HTTP') {
          environment {
            dockerTag = 'http'
          }
          steps {
            script {
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } 
      }
    }
  }
}

