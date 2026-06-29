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
  return request('/jobs', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// PATCH /api/jobs/:id — update job status (called by Jenkins later)
export async function updateJob(id, update) {
  return request(`/jobs/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}
