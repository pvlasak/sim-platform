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


**The full startup sequence**
- Browser loads index.html
- downloads and runs main.js
- createApp(App) — Vue starts with App.vue as root
- app.mount('#app') — renders into <div id="app">
- App.vue renders AppShell and AppShell renders sidebar + topbar + <slot>
- <RouterView> renders the current route's view
- URL is / → redirects to /models --> ModelsView renders inside RouterView

##Project goals:
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

---
## Start with Docker Compose
- application is running on localhost:8080
- mongo-express is accessible on localhost:8081
- `docker-compose.yaml` starts 4 containers via command *docker compose -f docker-compose.yaml up*:
  1. backend
  2. frontend
  4. mongodb
  5. mongo-express
- enter backend container: *docker exec -it <container_id> /bin/sh*
- create private key file id_rsa in `/root/.ssh` and adjust permissions as chmod 600 for the whole `/root/.ssh` directory
- `known_hosts` file can be updated by running a command: *ssh-keyscan -t rsa gitlab.com >> /root/.ssh/known_hosts* that fetches the public key from github server. 

## Stop application 
- *docker compose -f docker-compose.yaml down*

--
## Deploy application on EKS Cluster
- `mongo-secret.yaml` not needed. 

### 1. Create cluster with OIDC enabled
eksctl create cluster \
  --name my-cluster \
  --region us-east-2 \
  --version 1.30 \
  --nodegroup-name ng-1 \
  --node-type m5.large \
  --nodes 3 \
  --with-oidc
### 2. Create IAM service account for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster my-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve
### 3. Install the driver add-on
eksctl create addon \
  --cluster my-cluster \
  --name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::<account-id>:role/AmazonEKS_EBS_CSI_DriverRole \
  --force
### 4. Create StorageClass
kubectl apply -f mongodb-storageClass.yaml
### 5. Install MongoDB as StatefulSet to persist database data
helm repo add bitnami https://charts.bitnami.com/bitnami
helm search repo bitnami
helm install mongodb --values mongodb-helm-values.yaml bitnami/mongodb
### 6. Create MongoDB ConfigMap
kubectl apply -f mongodb-configmap.yaml
### 7. Create application backend configmap
kubectl apply -f backend-configmap.yaml
### 8. Create SSH key secret for GitLab
kubectl apply -f gitlab-private-key-secret.yaml
### 9. Create known_hosts configmap for GitLab
kubectl apply -f known_hosts_config.yaml
### 10. Create backend deployment
kubectl apply -f backend.yaml
### 11. Create frontend deployment
kubectl apply -f frontend.yaml
### 12. - install Nginx Ingress Controller using helm as sequence of commands in a new namespace:
  - *kubectl create namespace ingress-nginx*
  - *helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx*
  - *helm repo update*
  - *helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx*

### 13. Update DNS name of AWS Loadbalancer and in both ingress config files and apply them:
kubectl apply -f api-ingress.yaml
kubectl apply -f frontend-ingress.yaml
