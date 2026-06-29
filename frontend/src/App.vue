<template>
  <AppShell>
    <!-- Global error banner -->
    <div v-if="jobStore.error" class="error-banner">
      ⚠ {{ jobStore.error }}
      <button @click="jobStore.error = null">✕</button>
    </div>

    <!-- Loading state on first load -->
    <div v-if="jobStore.loading && !jobStore.models.length" class="loading-screen">
      <div class="loading-spinner" />
      <div class="loading-text">Connecting to SimFlow...</div>
    </div>

    <RouterView v-else />
  </AppShell>
</template>

<script setup>
import { onMounted } from 'vue'
import AppShell from '@/components/AppShell.vue'
import { useJobStore } from '@/stores/jobs'

const jobStore = useJobStore()

// Load all data from MongoDB on app start
onMounted(() => jobStore.loadAll())
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; overflow: hidden; }
body { font-family: 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }

.error-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 24px;
  background: rgba(239,68,68,.12); border-bottom: 1px solid rgba(239,68,68,.3);
  color: #EF4444; font-size: 12px; font-family: 'JetBrains Mono', monospace;
}
.error-banner button {
  background: none; border: none; color: #EF4444; cursor: pointer; font-size: 14px;
}

.loading-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; gap: 12px;
}
.loading-spinner {
  width: 28px; height: 28px; border-radius: 50%;
  border: 2px solid #1E2E4A; border-top-color: #3B82F6;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #4A6080; }
</style>
