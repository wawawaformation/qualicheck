<script setup>
defineProps({
  type: { type: String, required: true },
  message: { type: String, required: true },
})
</script>

<template>
  <div class="bandeau-message" :class="`bandeau-message--${type}`" :role="type === 'erreur' ? 'alert' : 'status'">
    <i class="bi" :class="type === 'erreur' ? 'bi-exclamation-circle' : 'bi-check-circle'"></i>
    {{ message }}
  </div>
</template>
