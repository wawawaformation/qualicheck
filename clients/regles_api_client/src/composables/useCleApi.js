import { ref, computed } from 'vue'

const STORAGE_KEY = 'qualicheck_regles_api_key'

const cle = ref(localStorage.getItem(STORAGE_KEY))

export function useCleApi() {
  const hasKey = computed(() => cle.value !== null && cle.value !== '')

  function setKey(valeur) {
    localStorage.setItem(STORAGE_KEY, valeur)
    cle.value = valeur
  }

  function clearKey() {
    localStorage.removeItem(STORAGE_KEY)
    cle.value = null
  }

  return { cle, hasKey, setKey, clearKey }
}
