<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCleApi } from './composables/useCleApi.js'
import { useToast } from './composables/useToast.js'

const route = useRoute()
const { hasKey } = useCleApi()
const { message: toastMessage } = useToast()

const liensNav = computed(() => {
  if (hasKey.value) {
    return [{ texte: 'Modifier ma clé API', actif: false }, { texte: 'Supprimer ma clé API', actif: false }]
  }
  return [{ texte: 'Renseigner ma clé API', actif: route.name === 'cle-api' }]
})
</script>

<template>
  <header class="entete">
    <router-link class="entete__logo" to="/revue">
      <span class="entete__logo-icone"><i class="bi bi-check-lg"></i></span>
      QualiCheck
    </router-link>
    <nav class="entete__nav">
      <router-link
        v-for="lien in liensNav"
        :key="lien.texte"
        to="/cle-api"
        :aria-current="lien.actif ? 'page' : undefined"
      >
        {{ lien.texte }}
      </router-link>
    </nav>
  </header>

  <Transition name="toast">
    <div v-if="toastMessage" class="toast-succes" role="status">
      <i class="bi bi-check-circle"></i> {{ toastMessage }}
    </div>
  </Transition>

  <router-view />

  <footer class="pied-de-page">
    <div class="pied-de-page__haut">
      <div>
        <a class="pied-de-page__logo" href="#">
          <i class="bi bi-check-lg"></i> QualiCheck
        </a>
        <p class="pied-de-page__tagline">Assistant d'aide à l'audit qualité web basé sur les règles Opquast</p>
      </div>
      <nav class="pied-de-page__nav">
        <router-link to="/le-projet"><i class="bi bi-book"></i> Le projet</router-link>
        <router-link to="/mentions-legales"><i class="bi bi-bank"></i> Mentions légales</router-link>
        <router-link to="/politique-des-donnees"><i class="bi bi-shield-lock"></i> Politique des données</router-link>
      </nav>
    </div>
    <div class="pied-de-page__bas">
      <p>🄯 Copyleft 2026, vous trouverez le projet sur <a href="#">GitHub</a></p>
      <p class="pied-de-page__mention">QualiCheck n'est pas un outil officiel Opquast et ne remplace pas l'expertise d'un auditeur</p>
    </div>
  </footer>
</template>
