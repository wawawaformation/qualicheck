import { createRouter, createWebHistory } from 'vue-router'
import RevueRegles from '../views/RevueRegles.vue'
import CleApi from '../views/CleApi.vue'
import LeProjet from '../views/LeProjet.vue'
import MentionsLegales from '../views/MentionsLegales.vue'
import PolitiqueDonnees from '../views/PolitiqueDonnees.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/revue' },
    { path: '/revue', name: 'revue', component: RevueRegles },
    { path: '/cle-api', name: 'cle-api', component: CleApi },
    { path: '/le-projet', name: 'le-projet', component: LeProjet },
    { path: '/mentions-legales', name: 'mentions-legales', component: MentionsLegales },
    { path: '/politique-des-donnees', name: 'politique-des-donnees', component: PolitiqueDonnees },
  ],
})

export default router
