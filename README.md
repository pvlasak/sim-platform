# sim-platform
In some cases the model and the simulation can be two disconnected processes. The environments where engineer builds the model and where the HPC computation runs have no automatic link between each other. Sim-Platform makes the model commit and the simulation job the same atomic operation — version controlled, traceable, and reproducible from a single interface on the engineer's local machine.

**Idea behind sim-platform:**       
Engineer works locally
- uploads model through sim-platform frontend
- model is uploaded to S3 storage
- model meta-data are versioned in GitLab with model_id set as a main identifier. 
- same model_id is stored in MongoDB for each job
- cluster pulls exactly model data having given model_id
- results are linked to that exact model_id
- anyone can reproduce the run from the model that can be easily identified. 

## Project goals:
- build **simulation operations platform**
### 1 — Model Management
Engineers upload a model files through a browser interface. Each upload creates automatically a GitLab commit of manifest file to `/models` directory — giving every model version a unique id, a timestamp, and an author and data are saved to MongoDB.

### 2 — Automated Model Check
After every model upload, model manifest file is pushed to GitLab. User has an option to start model check manually. If the check is successful, model status is changed to READY and start of simulation is allowed. Otherwise another model revision has to be uploaded after fixing the bug. Start of simulation initiates git push of the job manifest file to GitLab `/jobs` directory and it automatically triggers provisioning of the HPC cluster on AWS from Jenkins pipeline. 
The result — passed or failed — is reported back to the platform. 

### 3 — Cloud Simulation on Demand
When an engineer starts a simulation, the platform automatically provisions an AWS ParallelCluster via Terraform, pulls the exact model version from S3 storage, runs simulation via Slurm, monitors progress in real time, and destroys the cluster when finished. The engineer never touches AWS directly to prepare or destroy computational resources.

### 4 — Results Storage and Traceability
After simulation completes, output files are downloaded to S3, key metrics are parsed and stored in MongoDB, and everything is linked back to the original model id. Result manifest file is pushed to GitLab directory `/results`. Six months later anyone can answer — which model version produced which result.

<img width="1814" height="818" alt="Screenshot from 2026-11-10 14-49-10" src="https://github.com/user-attachments/assets/09cee3c3-5071-41b7-8b3f-e145fddfbaea" />

## Deploy application on localhost using Docker Compose
### Prerequisities 
- GitLab repository is existing and public SSH key is set for GitLab account, private key is available locally. 
- install docker daemon
- install docker compose
- authentication against public DockerHub registry is successfull: *docker login*

### Set up 
1. Build Frontend Docker Image
  - *cd frontend*
  - *docker build -t sim-app-frontend:{version} .*
2. Build Backend Docker Image
  - *cd backend*
  - *docker build -t sim-app-backend:{version} .*
3. Attach private SSH key to backend container as a volume in order to authenticate on GitLab
4. All environmental variables in `docker-compose.yaml` are updated.
5. MinIO docker image is available locally. Source: https://github.com/minio/minio
6. Start Application - run docker compose
  - *docker compose -f docker-compose/docker-compose.yaml up*
     application runs on 0.0.0.0:8080
7. Stop Application
  - *docker compose -f docker-compose/docker-compose.yaml down*


## Deploy application on AWS EKS Cluster
<img width="3200" height="2000" alt="sim-platform-architecture" src="https://github.com/user-attachments/assets/a18efff1-cdaf-4324-9b6e-1fec1d772039" />

### 1. Manual Application Deployment

#### Prerequisites

**Installation**
- AWS CLI installed - *aws configure* command sets access credentials for AWS user
- docker daemon
- eksctl
- kubectl
- helm 
- node and npm

#### 1. Create cluster with OIDC enabled
eksctl create cluster \
  --name my-cluster \
  --region us-east-2 \
  --version 1.30 \
  --nodegroup-name ng-1 \
  --node-type m5.large \
  --nodes 3 \
  --with-oidc
#### 2. Create IAM service account for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster my-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve
#### 3. Install the driver add-on
eksctl create addon \
  --cluster my-cluster \
  --name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::<account-id>:role/AmazonEKS_EBS_CSI_DriverRole \
  --force
#### 4. Create StorageClass
kubectl apply -f mongodb-storageClass.yaml
#### 5. Install MongoDB as StatefulSet to persist database data
helm repo add bitnami https://charts.bitnami.com/bitnami
helm search repo bitnami
helm install mongodb --values mongodb-helm-values.yaml bitnami/mongodb
#### 6. Create MongoDB ConfigMap
kubectl apply -f mongodb-configmap.yaml
#### 7. Create application backend configmap
kubectl apply -f backend-configmap.yaml
#### 8. Create SSH key secret for GitLab
kubectl apply -f gitlab-private-key-secret.yaml
#### 9. Create known_hosts configmap for GitLab
kubectl apply -f known_hosts_config.yaml
####### 10. Create backend deployment
kubectl apply -f backend.yaml
#### 11. Create frontend deployment
kubectl apply -f frontend.yaml
#### 12. - install Nginx Ingress Controller using helm as sequence of commands in a new namespace:
  - *kubectl create namespace ingress-nginx*
  - *helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx*
  - *helm repo update*
  - *helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx*

#### 13. Update DNS name of AWS Loadbalancer and in both ingress config files and apply them:
kubectl apply -f api-ingress.yaml
kubectl apply -f frontend-ingress.yaml

### 2. Automated Application Deployment
- there are two main parts:
  A. Terraform - script `main.tf` provisioning AWS EKS cluster
  started as *terraform init* + *terraform apply*
  B. Ansible - playbook configuring EKS cluster and setting up the application. 
  - DNS name of AWS Loadbalancer must be updated in `api-ingress.yaml` and `frontend-ingress.yaml`
  *ansible-playbook ansible-playbook-sim-app.yaml*

- terraform script and ansible playbook are started subsequently once after each other. 

#### Prerequisites

**Installation**
 - AWS CLI installed - *aws configure* command sets access credentials for AWS user
- docker daemon
- kubectl
- helm 
- node and npm
- terraform
- ansible 
- python3
- python3-boto3
- python3-botocore
- python3-kubernetes
- python3-yaml
- python3-jsonpatch
  
#### 1. Infrastructure Provisioning using Terraform 
  - Terraform script provisioning EKS cluster on AWS is available in the repository.
  - Be careful about the region name where the cluster is going to be created. 
  - It is necessary to create `terraform.tfvars` file that defines few variables that `main.tf` needs:
    1. vpc_cidr_block = ""
    2. private_subnets = ["", "", ""]
    3. public_subnets = ["", "", ""]
    4. instance_types = [""]
    
  - Terraform is initialized and provisioner is installed by *terraform init*
  - Terraform configuration gets executed by command: *terraform apply*
  - Terraform Infrastructure is destroyed by running a command *terraform destroy*

#### 2. Configuring EKS cluster using Ansible

- Get kubeconfig file from newly created cluster and save it to location that ansible playbook references and that is defined in `ansible-vars`. kubeconfig file can be found and downloaded by AWS CLI commands:
*aws eks update-kubeconfig --region eu-central-1 --name sim-app-cluster --kubeconfig {kubeconfig_path}*
- Ansible Playbook can be started as *ansible-playbook ansible-playbook-sim-app.yaml*
- To connect to EKS cluster from localhost an environmental variable KUBECONFIG has to be exported as *export KUBECONFIG={kubeconfig_path}* and kubectl commands can be used subsequently. 

### 3. CICD in Jenkins
- Jenkinsfile runs the CICD pipeline where infrastructure is provisioned and application is configured by Ansible playbook running on dedicated server. 
- kubeconfig file is obtained by AWS CLI command and copied onto ansible server 

#### Prerequisites

- Ansible server is running as virtual Ubuntu server, for example on Digital Ocean droplet
- Public IP Address of Ansible Server is defined in the `Jenkinsfile` as environmental variable.
- Jenkins is running as docker container on a Digital Ocean Droplet. 
- Firewall rules are adjusted to allow Jenkins server to connect via SSH.
- AWS ECR private repository credentials are available to Jenkins, password is valid 12 hours only.
- private SSH key to access the Ansible server is available to Jenkins 

**Installation Ansible Server**
- AWS CLI - *aws configure* command sets access credentials for AWS user
- docker daemon
- kubectl in `/usr/local/bin`
- helm 
- terraform
- ansible 
- python3
- python3-boto3
- python3-botocore
- python3-kubernetes
- python3-yaml
- python3-jsonpatch
- all necessary secret YAML files for MongoDB and GitLab are copied onto Ansible server

**Installation Jenkins Container**
- AWS CLI 
- node and npm
- docker daemon
- terraform


