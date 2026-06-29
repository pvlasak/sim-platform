import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',                  redirect: '/models' },
  { path: '/models',            component: () => import('@/views/ModelsView.vue') },
  { path: '/jobs',              component: () => import('@/views/JobsView.vue')   },

  // Hidden — only reachable from the Start Sim button in ModelsView
  { path: '/job-start/:modelId', component: () => import('@/views/JobStartView.vue'), props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
