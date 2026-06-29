<template>
  <div class="view">

    <!-- KPI row -->
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

    <div class="two-col">

      <!-- LEFT: job list -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">All Jobs</div>
          <div class="live-indicator">
            <div class="dot running" />
            <span>{{ running.length }} running</span>
          </div>
        </div>
        <div class="card-body">
          <div
            v-for="job in jobStore.jobs"
            :key="job.id"
            class="job-card"
            :class="{ selected: selectedJob?.id === job.id }"
            @click="selectedJob = job"
          >
            <div class="job-card-top">
              <div class="dot" :class="job.status" />
              <div class="job-name">{{ job.name }} / {{ job.id }}</div>
              <div class="tag" :class="job.status">{{ job.status }}</div>
            </div>
            <div class="job-meta">
              {{ job.instance }} · {{ job.nodes }} nodes · {{ job.preset }}
            </div>
            <div v-if="job.status === 'running'" class="progress-wrap">
              <div class="progress-label">
                <span>Simulation</span>
                <span>{{ job.progress }}%</span>
              </div>
              <div class="progress-track">
                <div class="progress-fill green" :style="{ width: job.progress + '%' }" />
              </div>
            </div>
            <div v-if="job.status === 'queued'" class="queued-msg">
              Waiting for cluster provisioning...
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: job detail -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            {{ selectedJob ? selectedJob.name + ' / ' + selectedJob.id : 'Select a job' }}
          </div>
        </div>

        <div v-if="!selectedJob" class="empty-state">
          <svg width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" style="color:var(--t3)"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/></svg>
          <div>Click a job to see details</div>
        </div>

        <div v-else class="card-body">

          <!-- Stats grid -->
          <div class="stats-grid">
            <div class="stat">
              <div class="stat-label">Status</div>
              <div class="stat-value">
                <span class="tag" :class="selectedJob.status">{{ selectedJob.status }}</span>
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">Solver</div>
              <div class="stat-value mono">{{ selectedJob.solver }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Instance</div>
              <div class="stat-value mono">{{ selectedJob.instance }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Nodes</div>
              <div class="stat-value mono">{{ selectedJob.nodes }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Preset</div>
              <div class="stat-value">{{ selectedJob.preset }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Est. Cost</div>
              <div class="stat-value mono">${{ selectedJob.cost_est ?? '—' }}</div>
            </div>
          </div>

          <!-- Progress -->
          <div v-if="selectedJob.status === 'running'" style="margin-top:14px">
            <div class="progress-label">
              <span>Simulation progress</span>
              <span>{{ selectedJob.progress }}%</span>
            </div>
            <div class="progress-track" style="margin-top:4px">
              <div class="progress-fill green" :style="{ width: selectedJob.progress + '%' }" />
            </div>
          </div>

          <!-- Live log terminal -->
          <div class="term-label">Live Output</div>
          <div class="terminal" ref="termEl">
            <div v-for="(line, i) in logLines" :key="i" :class="lineClass(line)">
              {{ line }}
            </div>
            <div><span class="cursor" /></div>
          </div>

          <!-- Actions -->
          <div class="action-row">
            <button
              v-if="selectedJob.status === 'running' || selectedJob.status === 'queued'"
              class="btn btn-danger"
              @click="cancelJob"
            >
              Cancel Job
            </button>
            <button
              v-if="selectedJob.status === 'done'"
              class="btn btn-primary"
              @click="$router.push('/results')"
            >
              View Results →
            </button>
          </div>

        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { useJobStore } from '@/stores/jobs'

const jobStore   = useJobStore()
const selectedJob = ref(null)
const termEl      = ref(null)
const logLines    = ref([])
let   logTimer    = null

const running = computed(() => jobStore.jobs.filter(j => j.status === 'running'))
const queued  = computed(() => jobStore.jobs.filter(j => j.status === 'queued'))

// Auto-select first running job on load
if (running.value.length) selectedJob.value = running.value[0]

// Simulate live log output when a job is selected
watch(selectedJob, (job) => {
  clearInterval(logTimer)
  logLines.value = []
  if (!job || job.status === 'done') return

  let cycle = 101200 + Math.floor(Math.random() * 1000)

  logTimer = setInterval(async () => {
    const dt = (6.17 + (Math.random() - 0.5) * 0.04).toFixed(2)
    const t  = (cycle * 6.17e-7).toFixed(3)
    logLines.value.push(`  ${cycle}   dt=${dt}E-07   t= ${t}E-02`)
    cycle += 20

    if (Math.random() < 0.05) {
      logLines.value.push(`W A R N: negative volume element ${Math.floor(Math.random() * 9000000 + 1000000)}`)
    }

    // Keep last 40 lines only
    if (logLines.value.length > 40) logLines.value.shift()

    // Scroll to bottom
    await nextTick()
    if (termEl.value) termEl.value.scrollTop = termEl.value.scrollHeight
  }, 700)
}, { immediate: true })

onUnmounted(() => clearInterval(logTimer))

function lineClass(line) {
  if (line.includes('W A R N')) return 'line-warn'
  if (line.includes('E r r o r')) return 'line-err'
  return 'line-normal'
}

function cancelJob() {
  if (!selectedJob.value) return
  const job = jobStore.jobs.find(j => j.id === selectedJob.value.id)
  if (job) job.status = 'failed'
  clearInterval(logTimer)
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

/* Actions */
.action-row { display:flex;gap:8px;margin-top:12px; }
.btn {
  display:flex;align-items:center;gap:6px;padding:7px 14px;border-radius:5px;
  font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all .15s;
}
.btn-primary { background:var(--blue);color:#fff; }
.btn-primary:hover { background:#2563EB; }
.btn-danger  { background:var(--red-dim);color:var(--red);border:1px solid var(--red-dim); }
.btn-danger:hover  { background:rgba(239,68,68,.2); }
</style>
