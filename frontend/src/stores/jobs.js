// stores/jobs.js

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchModels, commitModel as apiCommitModel } from '@/api/models.js'
import { fetchJobs,   startJob   as apiStartJob    } from '@/api/jobs.js'

export const useJobStore = defineStore('jobs', () => {

  // ── State ──────────────────────────────────────────────────────
  const models  = ref([])
  const jobs    = ref([])
  const loading = ref(false)
  const error   = ref(null)

  // ── Computed ───────────────────────────────────────────────────
  const runningCount   = computed(() => jobs.value.filter(j => j.status === 'running').length)
  const completedCount = computed(() => jobs.value.filter(j => j.status === 'done').length)

  // ── Load from backend ──────────────────────────────────────────
  async function loadAll() {
    try {
      loading.value = true
      error.value   = null
      const [m, j] = await Promise.all([fetchModels(), fetchJobs()])
      models.value  = m
      jobs.value    = j
    } catch (e) {
      error.value = e.message
      console.error('Failed to load data:', e)
    } finally {
      loading.value = false
    }
  }

  // ── Commit model ───────────────────────────────────────────────
  // payload must now include the raw File object from the drop zone:
  // {
  //   file:      File object   ← the actual .key / .zip file
  //   project:   string
  //   commitMsg: string
  // }
  async function commitModel(payload) {
    try {
      const newModel = await apiCommitModel({
        file:         payload.file,        // File object — sent as multipart
        project:      payload.project,
        commitMsg:    payload.commitMsg,
        committedBy:  'P.Vlasak',       // later: from auth session
      })
      models.value.unshift(newModel)
      return newModel
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  // ── Start job ──────────────────────────────────────────────────
  async function startJob(payload) {
    try {
      const newJob = await apiStartJob({
        name:        payload.name,
        model_id:    payload.modelId,
        model_name:  payload.modelName,
        solver:      payload.solver,
        licence:     payload.licence,
        preset:      payload.preset,
        instance:    payload.instance,
        nodes:       payload.nodes,
        started_by:  'P.Vlasak',
      })
      jobs.value.unshift(newJob)
      return newJob
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  return {
    models, jobs, loading, error,
    runningCount, completedCount,
    loadAll, commitModel, startJob,
  }
})
