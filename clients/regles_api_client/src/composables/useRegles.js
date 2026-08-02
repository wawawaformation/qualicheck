import { ref, computed } from 'vue'
import { listerRegles, annoterRegle, ErreurAuthentification } from '../services/reglesApiService.js'
import { useCleApi } from './useCleApi.js'

export function useRegles() {
  const reglesBrutes = ref([])
  const chargement = ref(false)
  const erreurChargement = ref(null)

  const recherche = ref('')
  const filtreTheme = ref([])
  const filtrePhase = ref([])
  const filtreOutil = ref([])
  const filtreReviewStatus = ref([])

  const regleSelectionneeNumero = ref(null)
  const dernierResultat = ref(null)
  const erreurAnnotation = ref(null)
  const redirectionCleApi = ref(false)

  const themesDisponibles = computed(() =>
    [...new Set(reglesBrutes.value.map((r) => r.theme))].sort()
  )
  const phasesDisponibles = computed(() =>
    [...new Set(reglesBrutes.value.flatMap((r) => r.phases))].sort()
  )

  const reglesFiltrees = computed(() =>
    reglesBrutes.value.filter((regle) => {
      const texte = recherche.value.trim().toLowerCase()
      const matchRecherche = texte === '' || regle.intitule.toLowerCase().includes(texte)
      const matchTheme = filtreTheme.value.length === 0 || filtreTheme.value.includes(regle.theme)
      const matchPhase =
        filtrePhase.value.length === 0 || filtrePhase.value.some((p) => regle.phases.includes(p))
      const matchOutil =
        filtreOutil.value.length === 0 || filtreOutil.value.some((o) => regle.outils.includes(o))
      const matchStatut =
        filtreReviewStatus.value.length === 0 ||
        filtreReviewStatus.value.some((statut) =>
          statut === 'aucun' ? regle.review_status === null : regle.review_status === statut
        )
      return matchRecherche && matchTheme && matchPhase && matchOutil && matchStatut
    })
  )

  const regleSelectionnee = computed(
    () => reglesBrutes.value.find((r) => r.numero === regleSelectionneeNumero.value) ?? null
  )

  async function charger() {
    chargement.value = true
    erreurChargement.value = null
    try {
      reglesBrutes.value = await listerRegles()
    } catch (e) {
      erreurChargement.value = e.message
    } finally {
      chargement.value = false
    }
  }

  function selectionner(numero) {
    regleSelectionneeNumero.value = numero
    dernierResultat.value = null
    erreurAnnotation.value = null
  }

  // Renvoie explicitement le résultat plutôt que de laisser l'appelant
  // observer dernierResultat par un watch() : deux annotations réussies de
  // suite sur la même règle mettraient dernierResultat à 'succes' deux fois
  // de suite, soit la même valeur — un watch ne déclenche que sur un
  // changement de valeur, donc ne verrait pas la deuxième réussite.
  async function annoter(numero, patch) {
    const { hasKey, cle, clearKey } = useCleApi()
    if (!hasKey.value) {
      redirectionCleApi.value = true
      return 'redirection'
    }
    try {
      const regleMiseAJour = await annoterRegle(numero, patch, cle.value)
      const index = reglesBrutes.value.findIndex((r) => r.numero === numero)
      if (index !== -1) reglesBrutes.value[index] = regleMiseAJour
      dernierResultat.value = 'succes'
      erreurAnnotation.value = null
      return 'succes'
    } catch (e) {
      if (e instanceof ErreurAuthentification) {
        clearKey()
        redirectionCleApi.value = true
        return 'redirection'
      }
      dernierResultat.value = 'erreur'
      erreurAnnotation.value = e.message
      return 'erreur'
    }
  }

  return {
    reglesBrutes,
    chargement,
    erreurChargement,
    recherche,
    filtreTheme,
    filtrePhase,
    filtreOutil,
    filtreReviewStatus,
    themesDisponibles,
    phasesDisponibles,
    reglesFiltrees,
    regleSelectionneeNumero,
    regleSelectionnee,
    dernierResultat,
    erreurAnnotation,
    redirectionCleApi,
    charger,
    selectionner,
    annoter,
  }
}
