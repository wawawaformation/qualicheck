import { ref } from 'vue'

// État au niveau du module (comme useCleApi) : un seul toast pour toute
// l'application, quel que soit l'écran ou le type de message. Rendu une
// seule fois dans App.vue, entre l'entête et <router-view> — pas dans le
// <main> d'un écran particulier, sinon sa largeur suit celle de cet écran
// (ex. --container-narrow sur /cle-api) au lieu de --container-wide comme
// l'entête. App.vue ne se démonte jamais entre deux routes : un message
// affiché juste avant une navigation reste donc visible après.
const message = ref(null)
const type = ref('succes')
let masquer = null

export function useToast() {
  function afficher(texte, typeMessage = 'succes', duree = 4000) {
    message.value = texte
    type.value = typeMessage
    clearTimeout(masquer)
    masquer = setTimeout(() => {
      message.value = null
    }, duree)

    // Le toast est juste sous l'entête : si une action précédente a fait
    // défiler la page (ex. le scroll automatique vers le bouton
    // "Enregistrer" dans PanneauDetailRegle.vue), le message resterait
    // caché au-dessus du cadre visible sans ce retour en haut.
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function effacer() {
    clearTimeout(masquer)
    message.value = null
  }

  return { message, type, afficher, effacer }
}
