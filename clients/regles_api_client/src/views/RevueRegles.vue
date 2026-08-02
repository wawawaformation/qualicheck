<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRegles } from '../composables/useRegles.js'
import BarreFiltres from '../components/BarreFiltres.vue'
import ListeRegles from '../components/ListeRegles.vue'
import PanneauDetailRegle from '../components/PanneauDetailRegle.vue'
import BandeauMessage from '../components/BandeauMessage.vue'

const router = useRouter()
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

onMounted(charger)

watch(redirectionCleApi, (doitRediriger) => {
  if (doitRediriger) router.push('/cle-api')
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
            <BandeauMessage v-if="dernierResultat === 'succes'" type="succes" message="Annotation enregistrée." />
            <BandeauMessage
              v-else-if="dernierResultat === 'erreur'"
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
