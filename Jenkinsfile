#!/user/bin/env groovy

pipeline {
    agent any
    environment {
        AWS_ECR_SERVER = "086241318794.dkr.ecr.eu-central-1.amazonaws.com"
        AWS_ECR_FRONTEND_REPO = "${AWS_ECR_SERVER}/sim-app-frontend"
        AWS_ECR_BACKEND_REPO = "${AWS_ECR_SERVER}/sim-app-backend"
        VERSION = "1.0.0"
    }
    stages {
        stage("init") {
            steps {
                script {
                    echo "initializing stage..."
                }
            }
        }
        stage('build static index.html') {
            steps {
                sh "npm --prefix frontend install"
                sh "npm --prefix frontend run build"
            }
        }
        stage('build and push images'){
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'aws-ecr-simapp-credentials', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
                        echo "starting to build images and pushing them to AWS ECR repository"
                        dir('frontend') {
                            sh "docker build -t ${AWS_ECR_FRONTEND_REPO}:${VERSION} ."
                        }
                        dir('backend') {
                            sh "docker build -t ${AWS_ECR_BACKEND_REPO}:${VERSION} ."
                        }
                        sh 'echo ${PASSWORD} | docker login -u ${USERNAME} --password-stdin ${AWS_ECR_SERVER}'
                        sh "docker push ${AWS_ECR_FRONTEND_REPO}:${VERSION}"
                        sh "docker push ${AWS_ECR_BACKEND_REPO}:${VERSION}"
                    }
                    echo "image successfully built and pushed to AWS ECR repository..."
                }
            }
        }
        stage('provisioning eks cluster on AWS') {
            environment {
                AWS_ACCESS_KEY_ID = credentials('jenkins-user-aws-access-key-id')
                AWS_SECRET_ACCESS_KEY = credentials('jenkins-user-aws-secret-access-key')
            }
            steps {
                script {
                    echo "provisioning eks cluster on AWS..."
                    dir('terraform') {
                        sh "terraform init"
                        sh "terraform apply --auto-approve"
                        sh "aws eks update-kubeconfig --name sim-app-cluster --region eu-central-1 --kubeconfig ~/.kube/sim-eks-kubeconfig"
                        sh "chmod 400 ~/.kube/sim-eks-kubeconfig"
                    }
                }
            }
        }
        stage('deploy app') {
            steps {
                script {
                    echo "Waiting for AWS EKS cluster to be provisioned..."
                    sleep(time: 90, unit: "SECONDS")
                    echo "deploying app..."
                }                
            }
        }
    }
}