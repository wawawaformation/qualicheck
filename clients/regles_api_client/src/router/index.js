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
  // savedPosition n'existe que pour un retour navigateur (précédent/suivant) :
  // on restaure alors la position, sinon (nouveau clic sur un lien) on repart
  // du haut — sans ça, changer de page garde le défilement de la page
  // précédente.
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

export default router
