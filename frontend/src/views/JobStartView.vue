<template>
  <div class="view">

    <div class="model-banner" v-if="model">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M12 3v18M3 7l9 4 9-4"/></svg>
      <div>
        <div class="banner-label">Starting simulation for</div>
        <div class="banner-model">{{ model.name }} <span class="banner-commit">{{ model.commit_id }}</span></div>
      </div>
      <div class="banner-check passed">✓ Model check passed</div>
    </div>

    <div class="two-col">

      <!-- ── LEFT: config ───────────────────────────────────────── -->
      <div class="card">
        <div class="card-header"><div class="card-title">Simulation Configuration</div></div>
        <div class="card-body">

          <div class="field">
            <div class="label">Simulation Name</div>
            <input v-model="form.name" class="input" type="text"
              :placeholder="'e.g. ' + (model?.name.replace('.key','') ?? 'sim') + '-run-01'" />
          </div>

          <div class="field">
            <div class="label">Instance Type</div>
            <div class="option-group">
              <div v-for="inst in instances" :key="inst.value"
                class="option-card" :class="{ selected: form.instance === inst.value }"
                @click="form.instance = inst.value">
                <div class="option-name">{{ inst.value }}</div>
                <div class="option-meta">{{ inst.vcpu }} vCPU · {{ inst.ram }} · ${{ inst.price }}/h</div>
                <div class="option-note">{{ inst.note }}</div>
              </div>
            </div>
          </div>

          <div class="field">
            <div class="label">
              Node Count
              <span class="label-hint">{{ form.nodes * selectedInstance.vcpu }} total vCPUs</span>
            </div>
            <input type="range" v-model.number="form.nodes" min="1" max="16" step="1" class="slider" />
            <div class="node-labels"><span>1</span><span class="node-val">{{ form.nodes }} nodes</span><span>16</span></div>
          </div>

          <div class="field">
            <div class="label">LS-DYNA Licence</div>
            <div class="radio-group">
              <label v-for="lic in licences" :key="lic.value"
                class="radio-item" :class="{ selected: form.licence === lic.value }">
                <input type="radio" v-model="form.licence" :value="lic.value" />
                <div>
                  <div class="radio-name">{{ lic.label }}</div>
                  <div class="radio-desc">{{ lic.desc }}</div>
                </div>
              </label>
            </div>
          </div>

          <div class="field">
            <div class="label">Load Case Preset</div>
            <select v-model="form.preset" class="input">
              <option>Frontal ODB 56 km/h</option>
              <option>Side Pole 32 km/h</option>
              <option>FMVSS 214</option>
              <option>Rear Impact</option>
              <option>Custom</option>
            </select>
          </div>

        </div>
      </div>

      <!-- ── RIGHT: summary + launch ────────────────────────────── -->
      <div style="display:flex;flex-direction:column;gap:16px">

        <div class="card">
          <div class="card-header">
            <div class="card-title">Cost Estimate</div>
            <div style="font-family:var(--mono);font-size:9px;color:var(--t3)">per run</div>
          </div>
          <div class="card-body">
            <div class="cost-rows">
              <div class="cost-row">
                <div class="cost-name">Compute<small>{{ form.nodes }} × ${{ selectedInstance.price }}/h × 2.5h est.</small></div>
                <div class="cost-val">${{ computeCost }}</div>
              </div>
              <div class="cost-row">
                <div class="cost-name">Storage (S3)<small>~{{ form.nodes * 30 }}GB output</small></div>
                <div class="cost-val">${{ storageCost }}</div>
              </div>
              <div class="cost-row">
                <div class="cost-name">LS-DYNA Licence<small>{{ form.licence }} · customer-owned</small></div>
                <div class="cost-val">$0.00</div>
              </div>
            </div>
            <div class="cost-total">
              <div class="cost-total-label">Estimated Total</div>
              <div class="cost-total-val">${{ totalCost }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">Job Summary</div></div>
          <div class="card-body">
            <div class="summary-rows">
              <div class="summary-row"><div class="sk">Model</div><div class="sv mono">{{ model?.name ?? '—' }}</div></div>
              <div class="summary-row"><div class="sk">Commit</div><div class="sv mono blue">{{ model?.commit_id ?? '—' }}</div></div>
              <div class="summary-row"><div class="sk">Name</div><div class="sv mono">{{ form.name || '—' }}</div></div>
              <div class="summary-row"><div class="sk">Instance</div><div class="sv mono">{{ form.instance }}</div></div>
              <div class="summary-row"><div class="sk">Nodes</div><div class="sv mono">{{ form.nodes }} ({{ form.nodes * selectedInstance.vcpu }} vCPUs)</div></div>
              <div class="summary-row"><div class="sk">Licence</div><div class="sv mono">{{ form.licence }}</div></div>
              <div class="summary-row"><div class="sk">Preset</div><div class="sv">{{ form.preset }}</div></div>
              <div class="summary-row"><div class="sk">Started by</div><div class="sv">M. Kowalski</div></div>
            </div>
          </div>
        </div>

        <button class="btn-launch" :disabled="!form.name || launching" @click="launch">
          <span v-if="launching" class="btn-spinner" />
          <svg v-else width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          {{ launching ? 'Saving to MongoDB...' : 'Launch Simulation' }}
        </button>

        <div v-if="!form.name" class="hint">Give the simulation a name to continue</div>
        <div v-if="launchError" class="notice-error">✗ {{ launchError }}</div>

      </div>
    </div>

    <!-- Success overlay -->
    <div v-if="launched" class="success-overlay">
      <div class="success-box">
        <div class="success-icon">✓</div>
        <div class="success-title">Job Saved to MongoDB</div>
        <div class="success-sub">{{ form.name }} is now queued</div>
        <div style="display:flex;gap:8px;margin-top:16px">
          <button class="btn btn-ghost" @click="$router.push('/models')">Back to Models</button>
          <button class="btn btn-primary" @click="$router.push('/jobs')">View Jobs →</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useJobStore } from '@/stores/jobs'

const props      = defineProps({ modelId: String })
const jobStore   = useJobStore()
const launched   = ref(false)
const launching  = ref(false)
const launchError = ref(null)

const model = computed(() => jobStore.models.find(m => m.id === props.modelId) ?? null)

const instances = [
  { value: 'c5n.18xlarge',   vcpu: 72, ram: '192GB', price: 3.888, note: 'Recommended — EFA, tight MPI coupling' },
  { value: 'hpc6a.48xlarge', vcpu: 96, ram: '384GB', price: 5.760, note: 'High memory — large models' },
  { value: 'c5n.9xlarge',    vcpu: 36, ram: '96GB',  price: 1.944, note: 'Economy — smaller jobs' },
]
const licences = [
  { value: 'MPPDYNA',  label: 'MPPDYNA',  desc: 'MPP solver — required for multi-node runs' },
  { value: 'DYNA_960', label: 'DYNA 960', desc: 'SMP solver — single node only' },
]

const form = reactive({ name: '', instance: 'c5n.18xlarge', nodes: 4, licence: 'MPPDYNA', preset: 'Frontal ODB 56 km/h' })

const selectedInstance = computed(() => instances.find(i => i.value === form.instance) ?? instances[0])
const computeCost = computed(() => (form.nodes * selectedInstance.value.price * 2.5).toFixed(2))
const storageCost = computed(() => (form.nodes * 30 * 0.023).toFixed(2))
const totalCost   = computed(() => (parseFloat(computeCost.value) + parseFloat(storageCost.value)).toFixed(2))

async function launch() {
  launching.value  = true
  launchError.value = null
  try {
    // Calls store → calls API → saves to MongoDB jobs collection → updates Pinia
    await jobStore.startJob({
      name:       form.name,
      modelId:    props.modelId,
      modelName:  model.value?.name ?? '',
      solver:     'LS-DYNA MPP R14',
      licence:    form.licence,
      preset:     form.preset,
      instance:   form.instance,
      nodes:      form.nodes,
    })
    launched.value = true
  } catch (e) {
    launchError.value = 'Failed to save: ' + e.message
  } finally {
    launching.value = false
  }
}
</script>

<style scoped>
.view    { display:flex;flex-direction:column;gap:16px;position:relative; }
.two-col { display:grid;grid-template-columns:1fr 380px;gap:16px; }
.model-banner { display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:8px;background:var(--surf);border:1px solid var(--brd); }
.banner-label  { font-size:10px;color:var(--t3);margin-bottom:2px; }
.banner-model  { font-family:var(--mono);font-size:12px;font-weight:600;flex:1; }
.banner-commit { color:var(--blue);font-size:11px;margin-left:6px; }
.banner-check  { font-family:var(--mono);font-size:10px;font-weight:600;padding:3px 8px;border-radius:4px; }
.banner-check.passed { background:var(--green-dim);color:var(--green); }
.card    { background:var(--card);border:1px solid var(--brd);border-radius:8px;overflow:hidden; }
.card-header { padding:12px 16px;border-bottom:1px solid var(--brd);display:flex;align-items:center;justify-content:space-between; }
.card-title  { font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--t2); }
.card-body   { padding:16px; }
.field { margin-bottom:16px; }
.label { display:flex;align-items:center;justify-content:space-between;font-family:var(--mono);font-size:9px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:var(--t3);margin-bottom:8px; }
.label-hint { font-weight:400;color:var(--blue); }
.input { width:100%;background:var(--surf);border:1px solid var(--brd2);border-radius:5px;padding:8px 10px;font-family:var(--mono);font-size:11px;color:var(--t1);outline:none;transition:border-color .15s;appearance:none; }
.input:focus { border-color:var(--blue); }
.input::placeholder { color:var(--t3); }
.option-group { display:flex;flex-direction:column;gap:6px; }
.option-card  { padding:10px 12px;border-radius:6px;border:1px solid var(--brd2);cursor:pointer;transition:all .15s; }
.option-card.selected { border-color:var(--blue);background:var(--blue-glow); }
.option-name  { font-family:var(--mono);font-size:12px;font-weight:600;margin-bottom:2px; }
.option-meta  { font-family:var(--mono);font-size:10px;color:var(--t2);margin-bottom:2px; }
.option-note  { font-size:10px;color:var(--t3); }
.slider { width:100%;-webkit-appearance:none;height:3px;background:var(--brd2);border-radius:2px;outline:none;display:block; }
.slider::-webkit-slider-thumb { -webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:var(--blue);cursor:pointer;border:2px solid var(--card); }
.node-labels  { display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;color:var(--t3);margin-top:4px; }
.node-val     { color:var(--blue);font-weight:600; }
.radio-group  { display:flex;flex-direction:column;gap:6px; }
.radio-item   { display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:6px;border:1px solid var(--brd2);cursor:pointer;transition:all .15s; }
.radio-item input { margin-top:3px;accent-color:var(--blue);flex-shrink:0; }
.radio-item.selected { border-color:var(--blue);background:var(--blue-glow); }
.radio-name   { font-family:var(--mono);font-size:11px;font-weight:600; }
.radio-desc   { font-size:10px;color:var(--t3);margin-top:1px; }
.cost-rows    { display:flex;flex-direction:column;gap:6px;margin-bottom:12px; }
.cost-row     { display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:var(--surf);border:1px solid var(--brd);border-radius:5px; }
.cost-name    { font-size:11px;color:var(--t2); }
.cost-name small { font-family:var(--mono);font-size:9px;color:var(--t3);display:block;margin-top:1px; }
.cost-val     { font-family:var(--mono);font-size:12px;font-weight:600; }
.cost-total   { display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:var(--blue-glow);border:1px solid var(--blue-dim);border-radius:6px; }
.cost-total-label { font-size:12px;font-weight:600; }
.cost-total-val   { font-family:var(--mono);font-size:16px;font-weight:600;color:var(--blue); }
.summary-rows { display:flex;flex-direction:column; }
.summary-row  { display:flex;align-items:baseline;gap:8px;padding:7px 0;border-bottom:1px solid var(--brd); }
.summary-row:last-child { border-bottom:none; }
.sk  { font-family:var(--mono);font-size:9px;color:var(--t3);width:80px;flex-shrink:0;text-transform:uppercase;letter-spacing:.05em; }
.sv  { font-size:11px;color:var(--t1); }
.sv.mono { font-family:var(--mono); }
.sv.blue { color:var(--blue); }
.btn-launch { width:100%;padding:11px;border-radius:6px;background:var(--blue);color:#fff;font-size:13px;font-weight:600;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:background .15s; }
.btn-launch:hover:not(:disabled) { background:#2563EB; }
.btn-launch:disabled { opacity:.35;cursor:not-allowed; }
.btn-spinner { width:12px;height:12px;border-radius:50%;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;animation:spin .7s linear infinite;flex-shrink:0; }
@keyframes spin { to { transform:rotate(360deg); } }
.hint { text-align:center;font-size:11px;color:var(--t3);margin-top:-8px; }
.notice-error { padding:8px 12px;border-radius:5px;background:var(--red-dim);color:var(--red);font-family:var(--mono);font-size:11px;text-align:center; }
.success-overlay { position:absolute;inset:0;background:rgba(8,14,28,.85);display:flex;align-items:center;justify-content:center;border-radius:8px;z-index:10; }
.success-box  { background:var(--card);border:1px solid var(--brd);border-radius:10px;padding:32px 40px;text-align:center; }
.success-icon { font-size:36px;color:var(--green);margin-bottom:8px; }
.success-title { font-family:var(--mono);font-size:16px;font-weight:600;margin-bottom:4px; }
.success-sub   { font-size:12px;color:var(--t2); }
.btn { display:flex;align-items:center;gap:6px;padding:7px 14px;border-radius:5px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all .15s; }
.btn-ghost   { background:transparent;border:1px solid var(--brd2);color:var(--t2); }
.btn-ghost:hover { border-color:var(--blue);color:var(--blue); }
.btn-primary { background:var(--blue);color:#fff; }
.btn-primary:hover { background:#2563EB; }
</style>
