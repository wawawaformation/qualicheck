<script setup>
defineProps({
  themesDisponibles: { type: Array, default: () => [] },
  phasesDisponibles: { type: Array, default: () => [] },
  compteAffiche: { type: Number, required: true },
  compteTotal: { type: Number, required: true },
})

const recherche = defineModel('recherche', { default: '' })
const filtreTheme = defineModel('filtreTheme', { default: () => [] })
const filtrePhase = defineModel('filtrePhase', { default: () => [] })
const filtreOutil = defineModel('filtreOutil', { default: () => [] })
const filtreReviewStatus = defineModel('filtreReviewStatus', { default: () => [] })

const OUTILS = [
  { valeur: 'statique', libelle: 'Statique' },
  { valeur: 'playwright', libelle: 'Playwright' },
  { valeur: 'vision', libelle: 'Vision' },
  { valeur: 'manuel', libelle: 'Manuel' },
]
const STATUTS = [
  { valeur: 'aucun', libelle: 'Non revue' },
  { valeur: 'a_revoir', libelle: 'À revoir' },
  { valeur: 'valide', libelle: 'Validée' },
]

// Une règle n'a qu'un seul statut de revue à la fois : contrairement aux
// autres groupes (Thème, Phase, Outil), celui-ci est exclusif — choisir un
// statut désactive les autres. Cliquer sur le statut déjà actif l'enlève
// (retour à "aucun filtre sur la revue").
function basculerStatut(valeur) {
  filtreReviewStatus.value = filtreReviewStatus.value.includes(valeur) ? [] : [valeur]
}
</script>

<template>
  <div class="barre-filtres">
    <div class="barre-filtres__ligne-recherche">
      <div class="barre-filtres__recherche">
        <label for="recherche" class="visually-hidden">Rechercher dans l'intitulé des règles</label>
        <input type="search" id="recherche" v-model="recherche" placeholder="Rechercher dans l'intitulé…" />
      </div>
      <p class="barre-filtres__compte"><strong>{{ compteAffiche }}</strong> / {{ compteTotal }} règles affichées</p>
    </div>

    <details class="barre-filtres__filtres">
      <summary>Filtres <i class="bi bi-chevron-down"></i></summary>
      <div class="barre-filtres__groupes">
        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Thème</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Thème</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="theme in themesDisponibles" :key="theme">
              <input type="checkbox" :value="theme" v-model="filtreTheme" />{{ theme }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Phase</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Phase</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="phase in phasesDisponibles" :key="phase">
              <input type="checkbox" :value="phase" v-model="filtrePhase" />{{ phase }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Outil</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Outil</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="outil in OUTILS" :key="outil.valeur">
              <input type="checkbox" :value="outil.valeur" v-model="filtreOutil" />{{ outil.libelle }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Revue</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Revue</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="statut in STATUTS" :key="statut.valeur">
              <input
                type="checkbox"
                :value="statut.valeur"
                :checked="filtreReviewStatus.includes(statut.valeur)"
                @change="basculerStatut(statut.valeur)"
              />{{ statut.libelle }}
            </label>
          </div>
        </fieldset>
      </div>
    </details>
  </div>
</template>
