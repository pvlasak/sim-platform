# sim-platform
In some cases the model and the simulation can be two disconnected processes. The environments where engineer builds the model and where the HPC computation runs have no automatic link between each other. Sim-Platform makes the model commit and the simulation job the same atomic operation — version controlled, traceable, and reproducible from a single interface on the engineer's local machine.

**Idea behind sim-platform:**       
Engineer works locally
- uploads model through sim-platform frontend
- model is versioned in GitLab with commit hash
- same commit hash is stored in MongoDB with the job
- cluster pulls exactly that commit
- results are linked to that exact commit
- anyone can reproduce the run rom the same commit hash


## Project goals:
- build **simulation operations platform**
### 1 — Model Management
Engineers upload a model files through a browser interface. Each upload creates a GitLab commit automatically — giving every model version a unique commit hash, a timestamp, and an author. The model repository is the single source of truth.

### 2 — Automated Model Check
After every commit, a Jenkins pipeline pulls the model and runs a validation check automatically. The result — passed or failed — is reported back to the platform. Only models that pass the check can proceed to full simulation.

### 3 — Cloud Simulation on Demand
When an engineer starts a simulation, the platform automatically provisions an AWS ParallelCluster via Terraform, pulls the exact model version from GitLab, runs simulation via Slurm, monitors progress in real time, and destroys the cluster when finished. The engineer never touches AWS directly.

### 4 — Results Storage and Traceability
After simulation completes, output files are downloaded to S3, key metrics are parsed and stored in MongoDB, and everything is linked back to the original GitLab commit. Six months later anyone can answer — which model version produced which result.
  


## Prerequisites

Install these once if you don't have them:

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 18+ | https://nodejs.org |
| Python | 3.11+ | https://python.org |
| MongoDB Community | 7.0 | https://www.mongodb.com/try/download/community |

- Install Docker
- Install Docker Compose
- Configure AWS API Credentials - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- Install eksctl
- Install kubectl 

## Deploy application on EKS Cluster
- `mongo-secret.yaml` not needed. 

### Manual Application Deployment

#### Prerequisites

- Configure AWS API Credentials - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- Install eksctl
- Install kubectl
- Install helm 

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

## Automated Application Deployment

#### Prerequisites
- Configure AWS Credentials
- install terraform
- Install ansible
- Install kubectl
- Install AWS CLI
- Install aws-iam-authenticator
  
#### 1. Infrastructure Provisioning using Terraform 
  - Terraform script provisioning EKS cluster on AWS is available in the repository.
  - Be careful about the region name where the cluster is going to be created. 
  - It is necessary to create `terraform.tfvars` file that defines few variables that `main.tf` needs:
    1. vpc_cidr_block = ""
    2. private_subnets = ["", "", ""]
    3. public_subnets = ["", "", ""]
    4. instance_types = [""]
    
  - Terraform is initialiazed and provisioner is installed by *terraform init*
  - Terraform configuration gets executed by command: *terraform apply*
  - Terraform Infrastructure is destroyed by running a command *terraform destroy*

#### 2. Configuring EKS cluster using Ansible

- Get kubeconfig file from newly created cluster and save it to location that ansible playbook references and that is defined in `ansible-vars`. kubeconfig file can be found and downloaded by AWS CLI commands:
*aws eks update-kubeconfig --region eu-central-1 --name sim-app-cluster --kubeconfig {kubeconfig_path}*
- Ansible Playbook can be started as *ansible-playbook ansible-playbook-sim-app.yaml*
- To connect to EKS cluster from localhost an environmental variable KUBECONFIG has to be exported as *export KUBECONFIG={kubeconfig_path}* and kubectl commands can be used subsequently. 

