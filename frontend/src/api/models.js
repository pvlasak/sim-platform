// src/api/models.js

const BASE = '/api'

// ── JSON request helper — used for simple GET calls ───────────────
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

// GET /api/models — fetch all committed models
export async function fetchModels() {
  return request('/models')
}

// POST /api/models — commit a new model WITH the actual file
// We use FormData instead of JSON because we are sending a binary file.
// When using FormData, the browser sets the correct Content-Type
// header (multipart/form-data) automatically — do NOT set it manually.
export async function commitModel(payload) {
  const form = new FormData()

  // The actual file object from the drop zone or file input
  form.append('file',         payload.file)

  // Text fields sent alongside the file
  form.append('project',      payload.project)
  form.append('commit_msg',   payload.commitMsg)
  form.append('committed_by', payload.committedBy)

  const res = await fetch(`${BASE}/models`, {
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
