<template>
  <div class="shell">

    <!-- ── Sidebar ─────────────────────────────────────────────── -->
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark" />
        <span class="logo-text">Sim<em>Flow</em></span>
      </div>

      <nav class="nav">
        <div class="nav-section">Workspace</div>

        <RouterLink class="nav-item" to="/models">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 7l9-4 9 4v10l-9 4-9-4V7z"/><path d="M12 3v18M3 7l9 4 9-4"/></svg>
          Models
          <span class="badge">{{ jobStore.models.length }}</span>
        </RouterLink>

        <div class="nav-section">Compute</div>

        <RouterLink class="nav-item" to="/jobs">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/></svg>
          Jobs
          <span v-if="jobStore.runningCount" class="badge badge-green">
            {{ jobStore.runningCount }}
          </span>
        </RouterLink>

        <div class="nav-section">Analysis</div>

        <RouterLink class="nav-item" to="/results">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 6 3-4"/></svg>
          Results
          <span v-if="jobStore.completedCount" class="badge">
            {{ jobStore.completedCount }}
          </span>
        </RouterLink>

        <RouterLink class="nav-item" to="/cost">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M4 2h16v22l-3-2-3 2-3-2-3 2-4-2V2z"/><path d="M8 8h8M8 12h8M8 16h4"/></svg>
          Cost
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="user-chip">
          <div class="avatar">PV</div>
          <div>
            <div class="user-name">P. Vlasak </div>
            <div class="user-role">CAE Engineer</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- ── Main ────────────────────────────────────────────────── -->
    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <!-- Back button — shown only on hidden pages like Job Start -->
          <button v-if="showBack" class="back-btn" @click="$router.back()">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
            Back
          </button>
          <div class="topbar-title">{{ title }}</div>
        </div>
      </header>

      <div class="content">
        <slot />
      </div>
    </main>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useJobStore } from '@/stores/jobs'

const jobStore = useJobStore()
const route    = useRoute()

const titles = {
  '/models':  'Models',
  '/jobs':    'Jobs',
  '/results': 'Results',
  '/cost':    'Cost Dashboard',
}

// For the hidden job-start route, show a dynamic title
const title = computed(() => {
  if (route.path.startsWith('/job-start')) return 'Start Simulation'
  return titles[route.path] ?? 'SimFlow'
})

// Show back button only on hidden pages not in the sidebar
const showBack = computed(() => route.path.startsWith('/job-start'))
</script>

<style scoped>
.shell {
  --bg:        #080E1C;
  --surf:      #0F1829;
  --card:      #131E33;
  --brd:       #1E2E4A;
  --brd2:      #253550;
  --blue:      #3B82F6;
  --blue-dim:  #1D3F7A;
  --blue-glow: rgba(59,130,246,.15);
  --green:     #10B981;
  --green-dim: rgba(16,185,129,.13);
  --amber:     #F59E0B;
  --amber-dim: rgba(245,158,11,.12);
  --red:       #EF4444;
  --red-dim:   rgba(239,68,68,.12);
  --t1:        #E2E8F0;
  --t2:        #8DA0BC;
  --t3:        #4A6080;
  --mono:      'JetBrains Mono', monospace;

  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
  color: var(--t1);
}

.sidebar {
  width: 210px; flex-shrink: 0;
  background: var(--surf); border-right: 1px solid var(--brd);
  display: flex; flex-direction: column;
}
.logo {
  padding: 16px; border-bottom: 1px solid var(--brd);
  display: flex; align-items: center; gap: 10px;
}
.logo-mark {
  width: 22px; height: 22px; background: var(--blue);
  clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  flex-shrink: 0;
}
.logo-text { font-family: var(--mono); font-size: 14px; font-weight: 600; letter-spacing: .04em; font-style: normal; }
.logo-text em { color: var(--blue); font-style: normal; }

.nav { flex: 1; padding: 8px 0; overflow-y: auto; }
.nav-section {
  padding: 10px 14px 3px;
  font-family: var(--mono); font-size: 9px; font-weight: 600;
  letter-spacing: .12em; text-transform: uppercase; color: var(--t3);
}
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 500;
  color: var(--t2); text-decoration: none;
  border-left: 2px solid transparent; transition: all .15s;
}
.nav-item:hover { color: var(--t1); background: rgba(59,130,246,.05); }
.nav-item.router-link-active {
  color: var(--blue); border-left-color: var(--blue); background: var(--blue-glow);
}
.badge {
  margin-left: auto; background: var(--blue-dim); color: var(--blue);
  font-family: var(--mono); font-size: 9px; font-weight: 600;
  padding: 1px 6px; border-radius: 8px;
}
.badge-green { background: var(--green-dim); color: var(--green); }

.sidebar-footer { padding: 12px 14px; border-top: 1px solid var(--brd); }
.user-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 6px; cursor: pointer;
}
.user-chip:hover { background: rgba(255,255,255,.04); }
.avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, var(--blue-dim), var(--blue));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--mono); font-size: 10px; font-weight: 600;
  color: #fff; flex-shrink: 0;
}
.user-name { font-size: 12px; font-weight: 500; color: var(--t2); }
.user-role { font-size: 10px; color: var(--t3); font-family: var(--mono); }

.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar {
  height: 50px; flex-shrink: 0;
  background: var(--surf); border-bottom: 1px solid var(--brd);
  display: flex; align-items: center; padding: 0 24px;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.topbar-title { font-family: var(--mono); font-size: 13px; font-weight: 600; color: var(--t1); }

.back-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 10px; border-radius: 5px;
  background: transparent; border: 1px solid var(--brd2);
  color: var(--t2); font-size: 12px; font-weight: 500;
  cursor: pointer; transition: all .15s;
}
.back-btn:hover { border-color: var(--blue); color: var(--blue); }

.content {
  flex: 1; overflow-y: auto; padding: 24px;
  scrollbar-width: thin; scrollbar-color: var(--brd2) transparent;
}
.content::-webkit-scrollbar { width: 5px; }
.content::-webkit-scrollbar-thumb { background: var(--brd2); border-radius: 3px; }
</style>
