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

---
Three terminals, three commands.

## Step 1 — Start MongoDB

MongoDB runs as a background service after installation.

**macOS (Homebrew):**
```bash
brew services start mongodb-community
```

**Windows:**
MongoDB starts automatically as a Windows Service after installation.
Or start it manually:
```bash
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath C:\data\db
```

**Linux (Ubuntu):**
```bash
sudo systemctl start mongod
```

Verify it is running — open a new terminal and type:
```bash
mongosh
```
You should see a MongoDB shell prompt. Type `exit` to close it.

---

## Step 2 — Start the Backend (FastAPI)

Open a terminal in the `backend/` folder:

```bash
cd backend

# Create a Python virtual environment (only once)
python -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies (only once)
pip install -r requirements.txt

# Start FastAPI
uvicorn app.main:app --reload --port 8000
```

FastAPI is now running at:
- API:       http://localhost:8000
- Swagger UI: http://localhost:8000/docs  ← test endpoints here

---

## Step 3 — Start the Frontend (Vue / Vite)

Open a second terminal in the `frontend/` folder:

```bash
cd frontend

# Install dependencies (only once)
npm install

# Start Vite dev server
npm run dev
```

The app is now running at:
- http://localhost:5173

---

## How they connect

```
Browser (localhost:5173)
  └── Vite dev server
        └── proxies /api/* → localhost:8000  (FastAPI)
                                └── reads/writes MongoDB (localhost:27017)
```

---

## Stopping everything

- Frontend: `Ctrl+C` in the Vite terminal
- Backend:  `Ctrl+C` in the uvicorn terminal
- MongoDB:
  - macOS:  `brew services stop mongodb-community`
  - Linux:  `sudo systemctl stop mongod`
  - Windows: MongoDB service keeps running (fine to leave it)

---

## Inspecting the database

Use **MongoDB Compass** (free GUI) to browse the data:
- Download: https://www.mongodb.com/products/compass
- Connection string: `mongodb://localhost:27017`
- Database: `simflow`
- Collections: `models`, `jobs`
