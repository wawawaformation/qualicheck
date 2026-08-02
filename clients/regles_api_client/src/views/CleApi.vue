<script setup>
import { onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCleApi } from '../composables/useCleApi.js'
import BandeauMessage from '../components/BandeauMessage.vue'

const route = useRoute()
const router = useRouter()
const { hasKey, setKey, clearKey } = useCleApi()
const saisie = ref('')
const enModification = ref(false)
const cleVisible = ref(false)
const messageAction = ref(null)
let masquerMessageAction = null

function afficherMessage(texte) {
  messageAction.value = texte
  clearTimeout(masquerMessageAction)
  masquerMessageAction = setTimeout(() => {
    messageAction.value = null
  }, 4000)
}

function commencerModification() {
  enModification.value = true
  saisie.value = ''
  messageAction.value = null
}

function enregistrer() {
  if (saisie.value.trim() === '') return
  const modification = hasKey.value
  setKey(saisie.value.trim())
  saisie.value = ''
  enModification.value = false

  // Arrivée ici depuis une tentative d'annotation sans clé valide (RevueRegles.vue
  // ajoute ?retour=<numero> avant de rediriger) : une fois la clé enregistrée, on
  // retourne directement sur la règle plutôt que de laisser l'utilisateur y revenir
  // à la main. Le bandeau de cet écran n'aurait pas le temps de s'afficher (l'écran
  // est quitté immédiatement) : RevueRegles.vue affiche sa propre confirmation via
  // ?cleEnregistree=1.
  if (route.query.retour) {
    router.push({ path: '/revue', query: { regle: route.query.retour, cleEnregistree: '1' } })
    return
  }
  afficherMessage(modification ? 'Clé API mise à jour.' : 'Clé API enregistrée.')
}

function supprimer() {
  clearKey()
  afficherMessage('Clé API supprimée.')
}

onUnmounted(() => clearTimeout(masquerMessageAction))
</script>

<template>
  <main class="ecran-cle-api">
    <div>
      <h1 class="ecran-cle-api__titre">Clé API</h1>
      <p class="ecran-cle-api__sous-titre">Nécessaire pour modifier les règles du référentiel.</p>
    </div>

    <BandeauMessage v-if="messageAction" type="succes" :message="messageAction" />

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
