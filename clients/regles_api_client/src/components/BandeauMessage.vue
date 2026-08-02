<script setup>
const props = defineProps({
  type: { type: String, required: true }, // 'succes' | 'erreur' | 'avertissement'
  message: { type: String, required: true },
})

const ICONES = {
  succes: 'bi-check-circle',
  erreur: 'bi-exclamation-circle',
  avertissement: 'bi-exclamation-triangle',
}
</script>

<template>
  <div class="bandeau-message" :class="`bandeau-message--${type}`" :role="type === 'erreur' ? 'alert' : 'status'">
    <i class="bi" :class="ICONES[props.type] ?? ICONES.succes"></i>
    {{ message }}
  </div>
</template>
