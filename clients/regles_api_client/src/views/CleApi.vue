<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCleApi } from '../composables/useCleApi.js'
import { useToast } from '../composables/useToast.js'

const route = useRoute()
const router = useRouter()
const { hasKey, setKey, clearKey } = useCleApi()
const { afficher: afficherToast } = useToast()
const saisie = ref('')
const enModification = ref(false)
const cleVisible = ref(false)

function commencerModification() {
  enModification.value = true
  saisie.value = ''
}

function enregistrer() {
  if (saisie.value.trim() === '') return
  const modification = hasKey.value
  setKey(saisie.value.trim())
  saisie.value = ''
  enModification.value = false
  afficherToast(modification ? 'Clé API mise à jour.' : 'Clé API enregistrée.')

  // Arrivée ici depuis une tentative d'annotation sans clé valide (RevueRegles.vue
  // ajoute ?retour=<numero> avant de rediriger) : une fois la clé enregistrée, on
  // retourne directement sur la règle plutôt que de laisser l'utilisateur y revenir
  // à la main. Le toast déclenché ci-dessus reste visible après la navigation : il
  // est géré par useToast (état partagé) et rendu dans App.vue, qui ne se démonte
  // jamais entre deux routes.
  if (route.query.retour) {
    router.push({ path: '/revue', query: { regle: route.query.retour } })
  }
}

function supprimer() {
  clearKey()
  afficherToast('Clé API supprimée.')
}
</script>

<template>
  <main class="ecran-cle-api">
    <div>
      <h1 class="ecran-cle-api__titre">Clé API</h1>
      <p class="ecran-cle-api__sous-titre">Nécessaire pour modifier les règles du référentiel.</p>
    </div>

    <template v-if="!hasKey || enModification">
      <div class="champ-texte">
        <label for="cle-api">Votre clé API</label>
        <div class="champ-texte__saisie-avec-bouton">
          <input
            :type="cleVisible ? 'text' : 'password'"
            id="cle-api"
            v-model="saisie"
            placeholder="Collez votre clé ici"
          />
          <button
            type="button"
            class="champ-texte__bouton-visibilite"
            :aria-label="cleVisible ? 'Masquer la clé' : 'Afficher la clé'"
            @click="cleVisible = !cleVisible"
          >
            <i class="bi" :class="cleVisible ? 'bi-eye-slash' : 'bi-eye'"></i>
          </button>
        </div>
        <p class="champ-texte__aide">
          Cette clé vous a été fournie par l'équipe QualiCheck. Elle n'est nécessaire que pour
          enregistrer des annotations sur les règles.
        </p>
      </div>
      <div class="ecran-cle-api__actions">
        <button class="bouton bouton--plein" type="button" @click="enregistrer">
          {{ hasKey ? 'Enregistrer la nouvelle clé' : 'Enregistrer la clé' }}
        </button>
      </div>
    </template>

    <template v-else>
      <p class="ecran-cle-api__statut">Une clé API est enregistrée sur cet appareil.</p>
      <dl class="bloc-provenance">
        <div class="bloc-provenance__item"><dt>Clé API</dt><dd>••••••••••••••••••••••••••••••••</dd></div>
      </dl>
      <div class="ecran-cle-api__actions">
        <button class="bouton bouton--contour" type="button" @click="commencerModification">Modifier la clé</button>
        <button class="bouton bouton--neutre" type="button" @click="supprimer">Supprimer la clé</button>
      </div>
    </template>
  </main>
</template>
