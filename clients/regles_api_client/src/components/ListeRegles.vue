<script setup>
import { libelleStatut } from '../utils/statutRevue.js'

defineProps({
  regles: { type: Array, required: true },
  selectionneeNumero: { type: Number, default: null },
})
const emit = defineEmits(['selectionner'])
</script>

<template>
  <nav class="ecran-revue-regles__liste" aria-label="Liste des règles">
    <p v-if="regles.length === 0" class="ecran-revue-regles__liste-vide">
      Aucune règle ne correspond aux filtres sélectionnés.
    </p>
    <ul v-else class="liste-regles">
      <li v-for="regle in regles" :key="regle.numero">
        <button
          class="ligne-regle"
          type="button"
          :aria-current="regle.numero === selectionneeNumero ? 'true' : undefined"
          @click="emit('selectionner', regle.numero)"
        >
          <span class="ligne-regle__numero">n°{{ regle.numero }}</span>
          <span>
            <p class="ligne-regle__intitule">{{ regle.intitule }}</p>
            <span class="ligne-regle__outils">
              <span class="tag-outil" v-for="outil in regle.outils" :key="outil">{{ outil }}</span>
            </span>
          </span>
          <span class="badge-statut" :class="libelleStatut(regle.review_status).classe">
            {{ libelleStatut(regle.review_status).texte }}
          </span>
        </button>
      </li>
    </ul>
  </nav>
</template>
