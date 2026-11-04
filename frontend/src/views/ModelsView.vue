<template>
  <div class="view">
    <div class="two-col">

      <!-- ── LEFT: commit form ──────────────────────────────────── -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Commit New Model</div>
          <div class="branch-tag">
            <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9"/><path d="M12 12v3"/></svg>
            main
          </div>
        </div>
        <div class="card-body">

          <div
            class="dropzone"
            :class="{ active: dragging, filled: fileName }"
            @dragover.prevent="dragging = true"
            @dragleave="dragging = false"
            @drop.prevent="onDrop"
            @click="fileInput.click()"
          >
            <svg width="30" height="30" fill="none" stroke="currentColor" stroke-width="1.4" viewBox="0 0 24 24" style="color:var(--t3);margin-bottom:8px;display:block;margin-left:auto;margin-right:auto"><path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M12 3v18M3 7l9 4 9-4"/></svg>
            <div class="dz-text">{{ fileName || 'Drop .key file or archive' }}</div>
            <div class="dz-sub">.zip · .tar.gz · .k · .key</div>
            <input ref="fileInput" type="file" accept=".zip,.tar.gz,.k,.key" style="display:none" @change="onFileChange" />
          </div>

          <div class="field">
            <div class="label">Project Name</div>
            <input v-model="form.project" class="input" type="text" placeholder="e.g. Project-XYZ-v01" />
          </div>

          <div class="field">
            <div class="label">Model Description </div>
            <input v-model="form.description" class="input" type="text" placeholder="Describe the model" />
          </div>

          <div class="field">
            <div class="label">Commit Message</div>
            <input v-model="form.commitMsg" class="input" type="text" placeholder="Describe the modification you made" />
          </div>

          <div class="info-box">
            <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
            <div>
               Model details are saved to MongoDB and commit YAML manifest is pushed to GitLab.
              <strong>Model archive is uploaded to S3 storage.</strong> 
            </div>
          </div>

          <button
            class="btn btn-primary"
            :disabled="!fileObject || !form.commitMsg || submitting"
            @click="commit"
          >
            <span v-if="submitting" class="btn-spinner" />
            <svg v-else width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
            {{ submitting ? 'Saving...' : 'Commit &amp; Start Model Upload' }}
          </button>

          <div v-if="committed" class="notice-success">
            ✓ Model uploaded to S3 storage.
          </div>
          <div v-if="commitError" class="notice-error">
            ✗ {{ commitError }}
          </div>

        </div>
      </div>

      <!-- ── RIGHT: model table ─────────────────────────────────── -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Committed Models</div>
          <div class="count-badge">{{ jobStore.models.length }} models</div>
        </div>

        <div v-if="!jobStore.models.length" class="empty-table">
          No models yet — commit your first model
        </div>

        <div v-else class="table-wrap">
          <table class="model-table">
            <thead>
              <tr>
                <th>Model File</th>
                <th>Commit</th>
                <th>Check</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="model in jobStore.models" :key="model.id">
                <tr
                  v-for="(revision, index) in model.revisions"
                  :key="`${model.id}-${revision.revision_id}`"
                >
                  <td
                    v-if="index === 0"
                    :rowspan="model.revisions.length"
                    class="model-group-cell"
                  >
                    <div class="model-name">{{ model.project }}</div>
                    <div class="model-meta">{{ model.description || 'No description' }}</div>
                    <div class="model-meta">Model ID: {{ model.id }}</div>
                  </td>

                  <td>
                    <div class="model-name">
                      Revision {{ revision.revision_id }} · {{ revision.file_name }}
                    </div>
                    <div class="commit-id">{{ revision.git_commit_id || 'Commit pending' }}</div>
                    <div class="commit-msg-short" :title="revision.commit_msg">
                      {{ revision.commit_msg }}
                    </div>
                    <div class="model-meta">{{ formatDate(revision.committed_at) }}</div>
                  </td>

                  <td>
                    <div
                      class="check-badge"
                      :class="{
                        pending: revision.check_status === 'PENDING',
                        running: revision.check_status === 'CHECKING',
                        passed: revision.check_status === 'READY',
                        failed: revision.check_status === 'NEEDS_FIX',
                      }"
                    >
                      <span v-if="revision.check_status === 'READY'">✓ Passed</span>
                      <span v-else-if="revision.check_status === 'NEEDS_FIX'">✗ Needs fix</span>
                      <span v-else-if="revision.check_status === 'CHECKING'">
                        <span class="spin">⟳</span> Checking
                      </span>
                    </div>

                    <button
                      v-if="revision.check_status === 'PENDING'"
                      class="btn-check"
                      :disabled="
                        revision.check_status !== 'PENDING' ||
                        checkingRevisionKey === `${model.id}:${revision.revision_id}`
                      "
                      @click="startCheck(model, revision)"
                              >
                      {{
                        revision.check_status === 'CHECKING' ||
                        checkingRevisionKey === `${model.id}:${revision.revision_id}`
                          ? 'Checking…'
                          : 'Start Check'
                      }}
                    </button>
                  </td>

                  <td>
                    <button
                      v-if="revision.check_status === 'NEEDS_FIX' &&
                            revision.revision_id === model.revisions.at(-1)?.revision_id

                      "
                      class="btn-upload-correction"
                      :disabled="uploadingCorrectionKey === `${model.id}:${revision.revision_id}`"
                      @click="uploadCorrection(model, revision)"
                    >
                      {{
                        uploadingCorrectionKey === `${model.id}:${revision.revision_id}`
                          ? 'Uploading…'
                          : 'Upload Correction'
                      }}
                    </button>
                    <button
                      v-else
                      class="btn-sim"
                      :disabled="revision.check_status !== 'READY'"
                      :title="
                        revision.check_status !== 'READY'
                          ? 'This revision must pass checking first'
                          : 'Start simulation with this revision'
                      "
                      @click="startSimulation(model, revision)"
                    >
                      Start Sim
                    </button>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <input
  ref="correctionFileInput"
  type="file"
  accept=".zip,.tar.gz,.k,.key"
  hidden
  @change="handleCorrectionFile"
/>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useJobStore } from '@/stores/jobs'

const router     = useRouter()
const jobStore   = useJobStore()
const fileInput   = ref(null)
const fileName    = ref('')
const fileObject  = ref(null)   // the raw File object — needed for upload
const dragging    = ref(false)
const submitting  = ref(false)
const committed   = ref(false)
const commitError = ref(null)
const checkingRevisionKey = ref(null)
const correctionFileInput = ref(null)
const correctionTarget = ref(null)
const uploadingCorrectionKey = ref(null)


const form = reactive({ project: '', commitMsg: '' })

let pollTimer = null
let stopPolling = false


function latestRevision(model) {
  return model.revisions?.at(-1)
}


function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    fileObject.value = file        // store the File object
    fileName.value   = file.name   // store name for display
  }
}
function onFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    fileObject.value = file
    fileName.value   = file.name
  }
}

async function startCheck(model, revision) {
  if (revision.check_status !== 'PENDING') return

  const key = `${model.id}:${revision.revision_id}`
  checkingRevisionKey.value = key
  commitError.value = null

  try {
    await jobStore.startCheck({
      modelId: model.id,
      revisionId: revision.revision_id,
    })
    pollCheckStatus(model.id, revision.revision_id)
  } catch (error) {
    commitError.value = `Could not start model check: ${error.message}`
  } finally {
    checkingRevisionKey.value = null
  }
}

async function commit() {
  submitting.value  = true
  commitError.value = null
  try {
    // Pass the actual File object — api/models.js sends it as FormData
    await jobStore.commitModel({
      file:      fileObject.value,
      project:   form.project || 'default-project',
      description: form.description,
      commitMsg: form.commitMsg,
    })
    committed.value  = true
    fileName.value   = ''
    fileObject.value = null
    form.commitMsg   = ''
    form.project     = ''
    setTimeout(() => committed.value = false, 4000)
  } catch (e) {
    commitError.value = 'Failed to save: ' + e.message
  } finally {
    submitting.value = false
  }
}

function formatDate(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const h = Math.floor(diff / 3600000)
  if (h < 1)  return 'just now'
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

onBeforeUnmount(() => {
  stopPolling = true
  clearTimeout(pollTimer)
})

async function pollCheckStatus(modelId, revisionId) {
  if (stopPolling) return

  try {
    const model = await jobStore.refreshModel(modelId)
    const revision = model.revisions?.find(
      item => item.revision_id === revisionId
    )

    if (!revision) {
      throw new Error(`Revision ${revisionId} not found`)
    }

    if (revision.check_status === 'READY' ||
        revision.check_status === 'NEEDS_FIX') {
      return
    }

    pollTimer = setTimeout(
      () => pollCheckStatus(modelId, revisionId),
      2000
    )
  } catch (error) {
    commitError.value = `Could not refresh check status: ${error.message}`
  }
}

function uploadCorrection(model, revision) {
  if (revision.check_status !== 'NEEDS_FIX') return

  correctionTarget.value = {
    modelId: model.id,
    revisionId: revision.revision_id,
  }
  correctionFileInput.value?.click()
}

async function handleCorrectionFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''

  const target = correctionTarget.value
  correctionTarget.value = null

  if (!file || !target) return

  const commitMsg = window.prompt('Enter a unique commit message for this correction')
  if (!commitMsg?.trim()) return

  const key = `${target.modelId}:${target.revisionId}`
  uploadingCorrectionKey.value = key
  commitError.value = null

  try {
    await jobStore.uploadModelRevision({
      modelId: target.modelId,
      file,
      commitMsg: commitMsg.trim(),
    })
  } catch (error) {
    commitError.value = `Could not upload correction: ${error.message}`
  } finally {
    uploadingCorrectionKey.value = null
  }
}

</script>

<style scoped>
.view    { display:flex;flex-direction:column;gap:16px; }
.two-col { display:grid;grid-template-columns:380px 1fr;gap:16px; }
.card    { background:var(--card);border:1px solid var(--brd);border-radius:8px;overflow:hidden; }
.card-header { padding:12px 16px;border-bottom:1px solid var(--brd);display:flex;align-items:center;justify-content:space-between; }
.card-title  { font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--t2); }
.card-body   { padding:16px; }
.branch-tag  { display:flex;align-items:center;gap:4px;font-family:var(--mono);font-size:9px;color:var(--t3); }
.count-badge { font-family:var(--mono);font-size:9px;color:var(--t3); }

.dropzone {
  border:1.5px dashed var(--brd2);border-radius:6px;padding:22px 16px;
  text-align:center;cursor:pointer;transition:all .2s;background:rgba(59,130,246,.02);
}
.dropzone:hover,.dropzone.active { border-color:var(--blue);background:var(--blue-glow); }
.dropzone.filled { border-color:var(--green); }
.dz-text { font-size:12px;font-weight:500;color:var(--t2);margin-bottom:3px; }
.dz-sub  { font-size:10px;color:var(--t3);font-family:var(--mono); }

.field { margin-top:12px; }
.label { font-family:var(--mono);font-size:9px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:var(--t3);margin-bottom:5px; }
.input { width:100%;background:var(--surf);border:1px solid var(--brd2);border-radius:5px;padding:7px 10px;font-family:var(--mono);font-size:11px;color:var(--t1);outline:none;transition:border-color .15s;appearance:none; }
.input:focus { border-color:var(--blue); }
.input::placeholder { color:var(--t3); }

.info-box { display:flex;gap:8px;align-items:flex-start;margin:14px 0;padding:10px 12px;background:var(--blue-glow);border:1px solid var(--blue-dim);border-radius:6px;font-size:11px;color:var(--t2);line-height:1.5; }
.info-box svg { flex-shrink:0;margin-top:1px;color:var(--blue); }
.info-box strong { color:var(--t1); }

.btn { display:flex;align-items:center;justify-content:center;gap:6px;width:100%;padding:8px 14px;border-radius:5px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all .15s; }
.btn-primary { background:var(--blue);color:#fff; }
.btn-primary:hover:not(:disabled) { background:#2563EB; }
.btn-primary:disabled { opacity:.4;cursor:not-allowed; }
.btn-spinner { width:11px;height:11px;border-radius:50%;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;animation:spin .7s linear infinite;flex-shrink:0; }
@keyframes spin { to { transform:rotate(360deg); } }

.notice-success { margin-top:10px;padding:8px 12px;border-radius:5px;background:var(--green-dim);color:var(--green);font-family:var(--mono);font-size:11px;text-align:center; }
.notice-error   { margin-top:10px;padding:8px 12px;border-radius:5px;background:var(--red-dim);color:var(--red);font-family:var(--mono);font-size:11px;text-align:center; }

.empty-table { padding:32px 16px;text-align:center;font-size:12px;color:var(--t3); }
.table-wrap  { overflow-x:auto; }
.model-table { width:100%;border-collapse:collapse;font-size:12px; }
.model-table th { padding:10px 14px;text-align:left;font-family:var(--mono);font-size:9px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--t3);border-bottom:1px solid var(--brd);background:var(--surf); }
.model-table td { padding:10px 14px;border-bottom:1px solid var(--brd);vertical-align:middle; }
.model-table tr:last-child td { border-bottom:none; }
.model-table tr:hover td { background:rgba(59,130,246,.03); }
.model-name { font-family:var(--mono);font-size:11px;font-weight:500;color:var(--t1); }
.model-meta { font-size:10px;color:var(--t3);margin-top:2px; }
.commit-id  { font-family:var(--mono);font-size:10px;color:var(--blue); }
.commit-msg-short { font-size:10px;color:var(--t3);margin-top:2px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.check-badge { display:inline-flex;align-items:center;gap:4px;font-family:var(--mono);font-size:10px;font-weight:600;padding:3px 8px;border-radius:4px; }
.check-badge.passed  { background:var(--green-dim);color:var(--green); }
.check-badge.failed  { background:var(--red-dim);color:var(--red); }
.check-badge.running { background:var(--amber-dim);color:var(--amber); }
.check-badge.pending { background:rgba(148,163,184,.1);color:var(--t3); }
.spin { display:inline-block;animation:spin 1s linear infinite; }
.btn-sim { display:flex;align-items:center;gap:5px;padding:5px 10px;border-radius:5px;font-family:var(--mono);font-size:10px;font-weight:600;background:var(--blue);color:#fff;border:none;cursor:pointer;transition:all .15s;white-space:nowrap; }
.btn-sim:hover:not(:disabled) { background:#2563EB; }
.btn-sim:disabled { opacity:.3;cursor:not-allowed; }
.btn-check { display:flex;align-items:center;gap:5px;padding:5px 10px;border-radius:5px;font-family:var(--mono);font-size:10px;font-weight:600;background:var(--blue-dim);color:#fff;border:none;cursor:pointer;transition:all .15s;white-space:nowrap; }
.btn-check:hover:not(:disabled) { background:#2563EB; }
.btn-check:disabled { opacity:.3;cursor:not-allowed; }
.btn-upload-correction { display:flex;align-items:center;gap:5px;padding:5px 10px;border-radius:5px;font-family:var(--mono);font-size:10px;font-weight:600;background:var(--red);color:#fff;border:none;cursor:pointer;transition:all .15s;white-space:nowrap; }
.btn-upload-correction:hover:not(:disabled) { background:#b30b0b; }
.btn-upload-correction:disabled { opacity:.3;cursor:not-allowed; }
</style>
