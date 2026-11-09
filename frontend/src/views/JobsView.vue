<template>
  <div class="view">
    <template v-if="isSubmissionMode">
      <div class="submission-layout">
        <section class="card">
          <div class="card-header">
            <div class="card-title">Selected Model Revision</div>
          </div>

          <div v-if="selectedModel && selectedRevision" class="card-body model-overview">
            <div class="field">
              <div class="label">Project:</div>
              <div class="overview-value">{{ selectedModel.project }}</div>
            </div>
            <div class="field">
              <div class="label">Description:</div>
              <div class="overview-value">{{ selectedModel.description || '—' }}</div>
            </div>
            <div class="field">
              <div class="label">Model ID:</div>
              <div class="overview-value">{{ selectedModel.id }}</div>
            </div>
            <div class="field">
              <div class="label">Revision:</div>
              <div class="overview-value">{{ selectedRevision.revision_id }}</div>
            </div>
            <div class="field">
              <div class="label">File:</div>
              <div class="overview-value">{{ selectedRevision.file_name }}</div>
            </div>
            <div class="field">
              <div class="label">Check status:</div>
              <div class="overview-value">{{ selectedRevision.check_status }}</div>
            </div>
            <div class="field">
              <div class="label">Commit:</div>
              <div class="overview-value">{{ selectedRevision.git_commit_id || '—' }}</div>
            </div>
            <div class="field">
              <div class="label">Model Archive</div>
              <div class="overview-value">{{ selectedRevision.package_s3_uri }}</div>
            </div>
          </div>

          <div v-else class="card-body">
            The selected model or revision could not be found.
          </div>
        </section>

        <section class="card">
          <div class="card-header">
            <div class="card-title">Job Parameters</div>
          </div>

          <form class="card-body job-request-form" @submit.prevent="submitJob">
            <div class="field">
              <label class="label" for="job-name">Job Name</label>
              <input
                id="job-name"
                v-model="jobRequest.job_name"
                class="input"
                type="text"
                placeholder="e.g. CrashTest-run-01"
                required
                maxlength="100"
                autocomplete="off"
              />
            </div>

            <div class="field">
              <label class="label" for="job-solver">Solver</label>
              <select id="job-solver" v-model="jobRequest.solver" class="input">
                <option value="LS DYNA MPP R9">LS DYNA MPP R9</option>
                <option value="LS DYNA MPP R12">LS DYNA MPP R12</option>
                <option value="LS DYNA MPP R14">LS DYNA MPP R14</option>
              </select>
            </div>

            <div class="field">
              <label class="label" for="loadcase">Load Case Description</label>
              <input
                id="loadcase"
                v-model="jobRequest.loadcase"
                class="input"
                type="text"
                placeholder="Load case description"
                required
                autocomplete="off"
              />
            </div>

            <div class="field">
              <label class="label" for="job-instance">Instance Type</label>
              <select id="job-instance" v-model="jobRequest.instance" class="input">
                <option value="c5n.18xlarge">c5n.18xlarge</option>
                <option value="hpc6a.48xlarge">hpc6a.48xlarge</option>
                <option value="c5n.9xlarge">c5n.9xlarge</option>
              </select>
            </div>

            <div class="field">
              <label class="label" for="job-nodes">Node Count</label>
              <input
                id="job-nodes"
                v-model.number="jobRequest.nodes"
                class="input"
                type="number"
                min="1"
                max="16"
                required
              />
            </div>

            <button
              class="btn btn-primary"
              type="submit"
              :disabled="submitting || !selectedModel || !selectedRevision"
            >
              <span v-if="submitting" class="btn-spinner" />
              <span v-else>▶</span>
              {{ submitting ? 'Submitting…' : 'Submit Job' }}
            </button>
            <div v-if="submitSuccess" class="notice-success" role="status">
              ✓ {{ submitSuccess }}
            </div>
            <div v-if="submitError" class="notice-error" role="alert">
              ✗ {{ submitError }}
            </div>
          </form>
        </section>
      </div>
    </template>
    <!-- Keep the KPI row here -->
    <div class="kpi-row">
      <div class="kpi kpi-green">
        <div class="kpi-label">Running</div>
        <div class="kpi-value">{{ running.length }}</div>
        <div class="kpi-sub">active simulations</div>
      </div>

      <div class="kpi kpi-amber">
        <div class="kpi-label">Queued</div>
        <div class="kpi-value">{{ queued.length }}</div>
        <div class="kpi-sub">waiting to start</div>
      </div>

      <div class="kpi kpi-blue">
        <div class="kpi-label">vCPUs Active</div>
        <div class="kpi-value">{{ running.length * 72 }}</div>
        <div class="kpi-sub">across all nodes</div>
      </div>

      <div class="kpi kpi-red">
        <div class="kpi-label">Est. Cost / hr</div>
        <div class="kpi-value">${{ (running.length * 4 * 3.888).toFixed(2) }}</div>
        <div class="kpi-sub">all running jobs</div>
      </div>
    </div>

    <!-- Keep the jobs list here; render only running jobs -->
    <section class="card">
      <div class="card-header">
        <div class="card-title">Running Jobs</div>
      </div>
      <div class="card-body">
        <div v-for="job in running" :key="job.id" class="job-card">
          <div class="job-card-top">
            <div class="dot" :class="job.status" />
            <div class="job-name">{{ job.name }} / {{ job.id }}</div>
            <div class="tag" :class="job.status">{{ job.status }}</div>
          </div>

          <div class="job-meta">
            Model: {{ job.model_name || job.model_id }}
          </div>

          <div class="job-meta">
            {{ job.solver }} · {{ job.licence }} · {{ job.instance }} · {{ job.nodes }} nodes
          </div>

          <div class="job-meta">
            Preset: {{ job.preset }}
          </div>

          <div class="job-meta">
            Started by: {{ job.started_by }} ·
            {{ job.started_at ? new Date(job.started_at).toLocaleString() : 'Start time unavailable' }}
          </div>

          <div class="job-meta">
            Estimated cost: {{ job.cost_est != null ? `$${job.cost_est}` : '—' }}
          </div>

          <div v-if="job.status === 'running'" class="progress-wrap">
            <div class="progress-label">
              <span>Simulation progress</span>
              <span>{{ job.progress ?? 0 }}%</span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill green"
                :style="{ width: `${job.progress ?? 0}%` }"
              />
            </div>
          </div>
        </div>
        <div v-if="!running.length" class="empty-state">
          No running jobs.
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useJobStore } from '@/stores/jobs'
import { useRoute } from 'vue-router'

const jobStore   = useJobStore()
const route = useRoute()

const running = computed(() => jobStore.jobs.filter(j => j.status === 'running'))
const queued  = computed(() => jobStore.jobs.filter(j => j.status === 'queued'))

const selectedModel = computed(() => {
  const modelId = route.query.modelId
  if (typeof modelId !== 'string') return null

  return jobStore.models.find(model => model.id === modelId) ?? null
})

const selectedRevision = computed(() => {
  const revisionId = Number(route.query.revisionId)
  if (!Number.isInteger(revisionId) || revisionId < 1) return null

  return selectedModel.value?.revisions?.find(
    revision => revision.revision_id === revisionId,
  ) ?? null
})

const hasModelSelection = computed(
  () => route.query.modelId !== undefined || route.query.revisionId !== undefined,
)

const isSubmissionMode = computed(() => hasModelSelection.value)

const jobRequest = reactive({
  job_name: '',
  solver: '',
  loadcase: '',
  instance: 'c5n.18xlarge',
  nodes: 4, 
  started_by: 'P.Vlasak',
})

const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref('')

async function submitJob() {
  if (
    !selectedModel.value ||
    !selectedRevision.value ||
    selectedRevision.value.check_status !== 'READY'
  ) {
    submitError.value = 'Select a model revision that has passed checking.'
    return
  }

  submitting.value = true
  submitError.value = ''
  submitSuccess.value = ''

  try {
    await jobStore.startJob({
      projectName: selectedModel.value.project,
      modelId: selectedModel.value.id,
      revisionId: String(selectedRevision.value.revision_id),
      loadcase: jobRequest.loadcase.trim(),
      jobName: jobRequest.job_name.trim(),
      solver: jobRequest.solver,
      instance: jobRequest.instance,
      nodes: jobRequest.nodes,
      startedBy: jobRequest.started_by,
    })

    submitSuccess.value = 'Job request submitted.'
    Object.assign(jobRequest, {
    job_name: '',
    solver: '',
    loadcase: '',
    instance: 'c5n.18xlarge',
    nodes: 4,
    started_by: 'P.Vlasak',
    })
  } catch (error) {
    submitError.value = error.message || 'Could not submit the job request.'
  } finally {
    submitting.value = false
  }
}

</script>

<style scoped>
.view { display: flex; flex-direction: column; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
.kpi {
  background: var(--card); border: 1px solid var(--brd);
  border-radius: 8px; padding: 14px 16px;
  position: relative; overflow: hidden;
}
.kpi::before { content: ''; position: absolute; top:0;left:0;right:0;height:2px; }
.kpi-blue::before  { background: var(--blue); }
.kpi-green::before { background: var(--green); }
.kpi-amber::before { background: var(--amber); }
.kpi-red::before   { background: var(--red); }
.kpi-label { font-family:var(--mono);font-size:9px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--t3);margin-bottom:6px; }
.kpi-value { font-family:var(--mono);font-size:26px;font-weight:600;line-height:1;color:var(--t1);margin-bottom:4px; }
.kpi-sub   { font-size:10px;color:var(--t3); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.card { background:var(--card);border:1px solid var(--brd);border-radius:8px;overflow:hidden; }
.card-header {
  padding:12px 16px;border-bottom:1px solid var(--brd);
  display:flex;align-items:center;justify-content:space-between;
}
.card-title { font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--t2); }
.card-body  { padding:14px; }

.live-indicator { display:flex;align-items:center;gap:5px;font-family:var(--mono);font-size:9px;color:var(--green); }

/* Job cards in list */
.job-card {
  padding: 10px 12px; border-radius: 6px;
  border: 1px solid var(--brd); margin-bottom: 8px;
  cursor: pointer; transition: all .15s;
}
.job-card:last-child { margin-bottom: 0; }
.job-card:hover { border-color: var(--brd2); background: rgba(59,130,246,.03); }
.job-card.selected { border-color: var(--blue); background: var(--blue-glow); }
.job-card-top { display:flex;align-items:center;gap:8px;margin-bottom:5px; }
.job-name { font-family:var(--mono);font-size:11px;font-weight:500;flex:1; }
.job-meta { font-size:10px;color:var(--t3);font-family:var(--mono);margin-bottom:6px; }
.queued-msg { font-size:10px;color:var(--amber);font-family:var(--mono); }

/* Dots */
.dot { width:7px;height:7px;border-radius:50%;flex-shrink:0; }
.dot.running { background:var(--green);box-shadow:0 0 5px var(--green);animation:pulse 2s ease-in-out infinite; }
.dot.queued  { background:var(--amber); }
.dot.done    { background:var(--t3); }
.dot.failed  { background:var(--red); }
@keyframes pulse { 0%,100%{opacity:1}50%{opacity:.4} }

/* Tags */
.tag { font-family:var(--mono);font-size:9px;font-weight:600;padding:2px 7px;border-radius:3px; }
.tag.running { background:var(--green-dim);color:var(--green); }
.tag.queued  { background:var(--amber-dim);color:var(--amber); }
.tag.done    { background:rgba(148,163,184,.1);color:var(--t3); }
.tag.failed  { background:var(--red-dim);color:var(--red); }

/* Progress */
.progress-wrap  { margin-top:4px; }
.progress-label { display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;color:var(--t3);margin-bottom:3px; }
.progress-track { height:3px;background:var(--brd);border-radius:2px;overflow:hidden; }
.progress-fill  { height:100%;border-radius:2px;transition:width .5s; }
.progress-fill.green { background:var(--green); }
.progress-fill.blue  { background:var(--blue); }

/* Detail panel */
.empty-state {
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:10px;padding:48px 16px;color:var(--t3);font-size:12px;
}

.stats-grid { display:grid;grid-template-columns:1fr 1fr;gap:8px; }
.stat {
  background:var(--surf);border:1px solid var(--brd);
  border-radius:6px;padding:8px 10px;
}
.stat-label { font-family:var(--mono);font-size:9px;color:var(--t3);margin-bottom:3px;letter-spacing:.05em;text-transform:uppercase; }
.stat-value { font-size:12px;font-weight:500;color:var(--t1); }
.stat-value.mono { font-family:var(--mono);font-size:11px; }

/* Terminal */
.term-label { font-family:var(--mono);font-size:9px;color:var(--t3);letter-spacing:.06em;text-transform:uppercase;margin:14px 0 5px; }
.terminal {
  background:#060C18;border:1px solid var(--brd);border-radius:6px;
  padding:10px 12px;font-family:var(--mono);font-size:10px;
  line-height:1.65;height:160px;overflow-y:auto;
}
.terminal::-webkit-scrollbar { width:3px; }
.terminal::-webkit-scrollbar-thumb { background:var(--brd2); }
.line-normal { color:#7CB9E8; }
.line-warn   { color:var(--amber); }
.line-err    { color:var(--red); }
.cursor {
  display:inline-block;width:6px;height:11px;
  background:var(--green);vertical-align:middle;
  animation:blink 1s step-end infinite;
}
@keyframes blink { 0%,100%{opacity:1}50%{opacity:0} }

.model-overview {
  background: rgba(59, 130, 246, 0.06);
}

.model-overview .field:first-child {
  margin-top: 0;
}

.overview-value {
  width: 100%;
  min-height: 32px;
  padding: 7px 10px;
  border: 1px solid var(--blue-dim);
  border-radius: 5px;
  background: rgba(59, 130, 246, 0.08);
  color: var(--t1);
  font-family: var(--mono);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.submission-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: start;
  gap: 16px;
}

@media (max-width: 800px) {
  .submission-layout {
    grid-template-columns: 1fr;
  }
}

.field { margin-top: 12px; }

.label {
  display: block;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--t3);
  margin-bottom: 5px;
}

.input {
  width: 100%;
  background: var(--surf);
  border: 1px solid var(--brd2);
  border-radius: 5px;
  padding: 7px 10px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--t1);
  outline: none;
  transition: border-color .15s;
  appearance: none;
}

.input:focus { border-color: var(--blue); }
.input::placeholder { color: var(--t3); }

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px 14px;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .15s;
}

.btn-primary { background: var(--blue); color: #fff; }
.btn-primary:hover:not(:disabled) { background: #2563EB; }
.btn-primary:disabled { opacity: .4; cursor: not-allowed; }
.btn-spinner {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, .3);
  border-top-color: #fff;
  animation: spin .7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.notice-success {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 5px;
  background: var(--green-dim);
  color: var(--green);
  font-family: var(--mono);
  font-size: 11px;
  text-align: center;
}

.notice-error {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 5px;
  background: var(--red-dim);
  color: var(--red);
  font-family: var(--mono);
  font-size: 11px;
  text-align: center;
}
</style>

