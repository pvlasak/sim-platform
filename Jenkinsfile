#!/user/bin/env groovy

pipeline {
    agent any
    environment {
        AWS_ECR_SERVER = "086241318794.dkr.ecr.eu-central-1.amazonaws.com"
        AWS_ECR_FRONTEND_REPO = "${AWS_ECR_SERVER}/sim-app-frontend"
        AWS_ECR_BACKEND_REPO = "${AWS_ECR_SERVER}/sim-app-backend"
        VERSION = "1.0.0"
        ANSIBLE_SERVER = "167.71.47.101"
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
                    }
                }
                script {
                    def kubeconfig ="${env.HOME}/sim-eks-kubeconfig"
                    if (!fileExists(kubeconfig)) {
                        sh "aws eks update-kubeconfig --name sim-app-cluster --region eu-central-1 --kubeconfig ${kubeconfig}"
                        sh "chmod 400 ${kubeconfig}"
                    } else {
                        echo "kubeconfig already exists, skipping..."
                    }
                }
            }
        }
        stage("Copy Ansible files to Ansible Server") {
            steps {
                script {
                    echo "Waiting for AWS EKS cluster to be provisioned..."
                    sleep(time: 90, unit: "SECONDS")
                    echo "copying Ansible files to ansible server..."
                    sshagent(credentials: ['ansible-server-key']) {
                        sh "scp -o StrictHostKeyChecking=no ansible/* root@${ANSIBLE_SERVER}:/root/"
                        sh "scp -o StrictHostKeyChecking=no ${kubeconfig} root@${ANSIBLE_SERVER}:/root/kubeconfig"
                    }
                }
            }
        }
        stage ("Execute Ansible playbook") {
            steps {
                script {
                    echo "starting ansible playbook to configure EKS cluster"
                    def remote = [:]
                    remote.name = 'ansible-server'
                    remote.host = "${ANSIBLE_SERVER}"
                    remote.allowAnyHosts = true

                    withCredentials([sshUserPrivateKey(credentialsId: 'ansible-server-key', keyFileVariable: 'keyfile', usernameVariable: 'user')]) {
                        remote.user = user
                        remote.identityFile = keyfile
                        withCredentials([usernamePassword(credentialsId: 'aws-ecr-simapp-credentials', usernameVariable: 'ECR_USER', passwordVariable: 'ECR_PASS')]) {
                            sshCommand remote: remote, command: 'ansible-playbook ansible-playbook-sim-app.yaml -e "ecr_password=${ECR_PASS} kubeconfig_path=/root/kubeconfig sim_app_namespace=sim-app"'                           
                        }
                    }
                }
            }  
        }  
    }
}