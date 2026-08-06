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
- install git and openssh inside the backend container:
  1. *apk add git*
  2. *apk add openssh*
- `known_hosts` file can be updated by running a command: *ssh -T git@gitlab.com*
- create private key file id_rsa in `/root/.ssh` and adjust permissions as chmod 600 for the whole `/root/.ssh` directory

## Stop application 
- *docker compose -f docker-compose.yaml down*