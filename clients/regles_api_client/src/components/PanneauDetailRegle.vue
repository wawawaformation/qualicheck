<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { libelleStatut } from '../utils/statutRevue.js'
import { useCleApi } from '../composables/useCleApi.js'

const props = defineProps({
  regle: { type: Object, required: true },
})
const emit = defineEmits(['annoter'])

const router = useRouter()
const { hasKey } = useCleApi()

const statutForm = ref(props.regle.review_status ?? 'aucun')
const noteForm = ref(props.regle.review_note ?? '')

watch(
  () => props.regle.numero,
  () => {
    statutForm.value = props.regle.review_status ?? 'aucun'
    noteForm.value = props.regle.review_note ?? ''
  }
)

watch(statutForm, (valeur) => {
  if (valeur === 'aucun') noteForm.value = ''
})

const peutEnregistrer = computed(
  () => hasKey.value && (statutForm.value !== 'a_revoir' || noteForm.value.trim() !== '')
)

// Vérifie la clé API dès l'intention de vraiment annoter (choix de "À
// revoir" ou "Validée"), pas à "Non revue" : plus tôt que le clic sur
// "Enregistrer", pour ne pas laisser l'utilisateur rédiger une note qui
// serait perdue à la redirection. Sur @change, pas sur un watch(statutForm) :
// un watch se déclencherait aussi quand le changement de règle réinitialise
// statutForm par programmation, pas seulement sur un vrai clic utilisateur.
function verifierCleAvantAnnotation() {
  if (!hasKey.value) {
    router.push({ path: '/cle-api', query: { retour: props.regle.numero } })
  }
}

const badge = computed(() => libelleStatut(props.regle.review_status))

const horodatage = computed(() => {
  if (!props.regle.reviewed_at) return 'Jamais revue'
  const date = new Date(props.regle.reviewed_at)
  return `Dernière revue : ${date.toLocaleDateString('fr-FR')} ${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
})

function enregistrer() {
  if (statutForm.value === 'aucun') {
    emit('annoter', { reviewStatus: null, reviewNote: null })
  } else {
    emit('annoter', { reviewStatus: statutForm.value, reviewNote: noteForm.value })
  }
}
</script>

<template>
  <article class="panneau-detail-regle">
    <p class="panneau-detail-regle__eyebrow">Règle n°{{ regle.numero }} · {{ regle.theme }}</p>
    <div class="panneau-detail-regle__entete">
      <h2 class="panneau-detail-regle__titre">{{ regle.intitule }}</h2>
      <span class="badge-statut" :class="badge.classe">{{ badge.texte }}</span>
    </div>
    <div class="panneau-detail-regle__meta">
      <span class="tag-outil" v-for="outil in regle.outils" :key="outil">{{ outil }}</span>
      <span class="tag-meta" v-for="tag in regle.tags" :key="tag">{{ tag }}</span>
      <span class="tag-meta" v-for="phase in regle.phases" :key="phase">{{ phase }}</span>
    </div>

    <section class="panneau-detail-regle__section">
      <h3>Contexte</h3>
      <p>{{ regle.contexte ?? 'Non renseigné.' }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Solution</h3>
      <p>{{ regle.solution }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Contrôle</h3>
      <p>{{ regle.controle }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Guide d'analyse</h3>
      <p>{{ regle.guide_analyse }}</p>
      <p v-if="regle.strategie_justification" class="panneau-detail-regle__justification">
        <strong>Justification —</strong> {{ regle.strategie_justification }}
      </p>
    </section>

    <dl class="bloc-provenance">
      <div class="bloc-provenance__item"><dt>Stratégie</dt><dd>{{ regle.strategie_analyse }}</dd></div>
      <div class="bloc-provenance__item"><dt>Version du prompt</dt><dd>{{ regle.prompt_version ?? '—' }}</dd></div>
      <div class="bloc-provenance__item"><dt>Modèle</dt><dd>{{ regle.llm_model ?? '—' }}</dd></div>
    </dl>

    <div class="panneau-detail-regle__annotation">
      <h3>Annotation de revue</h3>
      <fieldset class="segmented-statut">
        <legend>Statut de revue</legend>
        <label class="segmented-statut__option segmented-statut__option--neutre">
          <input type="radio" name="review_status" value="aucun" v-model="statutForm" />
          Non revue
        </label>
        <label class="segmented-statut__option segmented-statut__option--danger">
          <input
            type="radio"
            name="review_status"
            value="a_revoir"
            v-model="statutForm"
            @change="verifierCleAvantAnnotation"
          />
          À revoir
        </label>
        <label class="segmented-statut__option segmented-statut__option--succes">
          <input
            type="radio"
            name="review_status"
            value="valide"
            v-model="statutForm"
            @change="verifierCleAvantAnnotation"
          />
          Validée
        </label>
      </fieldset>

      <div class="champ-texte" v-if="statutForm !== 'aucun'">
        <label for="review-note">
          Note de revue
          <span v-if="statutForm === 'a_revoir'" style="color: var(--color-danger-background)"> — obligatoire</span>
        </label>
        <textarea id="review-note" rows="3" v-model="noteForm"></textarea>
        <p class="champ-texte__aide">
          Cette note est réinjectée telle quelle dans le prompt lors du prochain <code>make enrich-again</code>.
        </p>
      </div>

      <div class="panneau-detail-regle__pied">
        <span class="panneau-detail-regle__horodatage">{{ horodatage }}</span>
        <button class="bouton bouton--plein" type="button" :disabled="!peutEnregistrer" @click="enregistrer">
          {{ hasKey ? "Enregistrer l'annotation" : 'Il manque la clé API' }}
        </button>
      </div>
    </div>
  </article>
</template>
