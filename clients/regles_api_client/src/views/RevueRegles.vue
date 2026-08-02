<script setup>
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRegles } from '../composables/useRegles.js'
import { useToast } from '../composables/useToast.js'
import BarreFiltres from '../components/BarreFiltres.vue'
import ListeRegles from '../components/ListeRegles.vue'
import PanneauDetailRegle from '../components/PanneauDetailRegle.vue'
import BandeauMessage from '../components/BandeauMessage.vue'

const route = useRoute()
const router = useRouter()
const { afficher: afficherToast } = useToast()
const {
  reglesBrutes,
  reglesFiltrees,
  erreurChargement,
  recherche,
  filtreTheme,
  filtrePhase,
  filtreOutil,
  filtreReviewStatus,
  themesDisponibles,
  phasesDisponibles,
  regleSelectionneeNumero,
  regleSelectionnee,
  dernierResultat,
  erreurAnnotation,
  redirectionCleApi,
  charger,
  selectionner,
  annoter,
} = useRegles()

onMounted(async () => {
  await charger()
  // Retour depuis l'écran clé API après une redirection (voir le watch
  // ci-dessous) : la règle qu'on tentait d'annoter est rouverte directement.
  // Le toast affiché par CleApi.vue avant de rediriger ici (useToast est
  // partagé, App.vue le rend sans jamais se démonter) reste visible tel quel
  // — pas besoin de le redéclencher ici.
  const regleARestaurer = Number(route.query.regle)
  if (!Number.isNaN(regleARestaurer)) {
    selectionner(regleARestaurer)
  }
})

watch(redirectionCleApi, (doitRediriger) => {
  if (doitRediriger) {
    router.push({ path: '/cle-api', query: { retour: regleSelectionneeNumero.value } })
  }
})

// Le bandeau de succès inline était affiché en haut du panneau de détail,
// hors du cadre visible juste après l'auto-scroll vers le bouton
// "Enregistrer" (même souci que le bouton disabled invisible) : remplacé
// par le toast global (useToast), visible quel que soit le scroll. La liste
// est aussi rechargée depuis le serveur pour rester synchro au-delà de la
// mise à jour locale déjà faite par annoter() — la règle sélectionnée et
// les filtres ne bougent pas.
watch(dernierResultat, async (valeur) => {
  if (valeur !== 'succes') return
  afficherToast('Annotation enregistrée.')
  await charger()
})
</script>

<template>
  <main class="ecran-revue-regles">
    <div class="ecran-revue-regles__entete">
      <h1 class="ecran-revue-regles__titre">Revue du référentiel</h1>
      <p class="ecran-revue-regles__sous-titre">Classification des règles Opquast par l'agent d'enrichissement</p>
    </div>

    <p v-if="erreurChargement" class="ecran-revue-regles__liste-vide">{{ erreurChargement }}</p>

    <template v-else>
      <BarreFiltres
        v-model:recherche="recherche"
        v-model:filtre-theme="filtreTheme"
        v-model:filtre-phase="filtrePhase"
        v-model:filtre-outil="filtreOutil"
        v-model:filtre-review-status="filtreReviewStatus"
        :themes-disponibles="themesDisponibles"
        :phases-disponibles="phasesDisponibles"
        :compte-affiche="reglesFiltrees.length"
        :compte-total="reglesBrutes.length"
      />

      <div class="ecran-revue-regles__corps">
        <ListeRegles
          :regles="reglesFiltrees"
          :selectionnee-numero="regleSelectionneeNumero"
          @selectionner="selectionner"
        />

        <div class="ecran-revue-regles__detail">
          <template v-if="regleSelectionnee">
            <BandeauMessage
              v-if="dernierResultat === 'erreur'"
              type="erreur"
              :message="erreurAnnotation ?? 'Une erreur est survenue, veuillez réessayer.'"
            />
            <PanneauDetailRegle
              :regle="regleSelectionnee"
              @annoter="(patch) => annoter(regleSelectionnee.numero, patch)"
            />
          </template>
          <p v-else class="ecran-revue-regles__detail-placeholder">
            Sélectionnez une règle dans la liste pour l'examiner et l'annoter.
          </p>
        </div>
      </div>
    </template>
  </main>
</template>
