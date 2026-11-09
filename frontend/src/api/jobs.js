// src/api/jobs.js
// All backend calls related to jobs.

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

// GET /api/jobs — fetch all jobs
export async function fetchJobs() {
  return request('/jobs')
}

// POST /api/jobs — start a new simulation job
// payload: { name, model_id, model_name, solver, licence,
//            preset, instance, nodes, started_by }
export async function startJob(payload) {
  const form = new FormData()
    form.append('project_name', payload.projectName)
    form.append('model_id',      payload.modelId)
    form.append('revision_id', payload.revisionId)
    form.append('loadcase',   payload.loadcase)
    form.append('job_name', payload.jobName)    
    form.append('solver', payload.solver)
    form.append('instance', payload.instance)
    form.append('nodes', payload.nodes)
    form.append('started_by', payload.startedBy)

  const res = await fetch(`${BASE}/jobs`, {
    method: 'POST',
    body: form,
    // No Content-Type header — browser sets it automatically with boundary
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

