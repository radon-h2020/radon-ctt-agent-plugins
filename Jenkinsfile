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
          steps {
            script {
              dockerTag = 'jmeter'
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } when { fileExists 'jmeter' }

        stage('HTTP') {
          steps {
            script {
              dockerTag = 'http'
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } when { fileExists 'http' }

        stage('Ping') {
          steps {
            script {
              dockerTag = 'ping'
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } when { fileExists 'ping' }

        stage('ApacheBench') {
          steps {
            script {
              dockerTag = 'apachebench'
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } when { fileExists 'apachebench' }

        stage('Locust') {
          steps {
            script {
              dockerTag = 'locust'
              dir dockerTag
              dockerImage = docker.build("radonconsortium/radon-ctt-agent:${dockerTag}")
              withDockerRegistry(credentialsId: 'dockerhub-radonconsortium') {
                dockerImage.push(dockerTag)
              }
            }
          }
        } when { fileExists 'locust' }
      }
    }
  }
}

