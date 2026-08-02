import { createRouter, createWebHistory } from 'vue-router'
import RevueRegles from '../views/RevueRegles.vue'
import CleApi from '../views/CleApi.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/revue' },
    { path: '/revue', name: 'revue', component: RevueRegles },
    { path: '/cle-api', name: 'cle-api', component: CleApi },
  ],
})

export default router
