import { ref } from 'vue'

// État au niveau du module (comme useCleApi) : un seul toast pour toute
// l'application, quel que soit l'écran qui l'a déclenché. Rendu une seule
// fois dans App.vue, qui ne se démonte jamais entre deux routes — un
// message affiché juste avant une navigation reste donc visible après.
const message = ref(null)
let masquer = null

export function useToast() {
  function afficher(texte, duree = 4000) {
    message.value = texte
    clearTimeout(masquer)
    masquer = setTimeout(() => {
      message.value = null
    }, duree)
  }

  function effacer() {
    clearTimeout(masquer)
    message.value = null
  }

  return { message, afficher, effacer }
}
