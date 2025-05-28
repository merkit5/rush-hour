<!-- ControlButtons.vue -->
<template>
  <div class="control-buttons">
    <button @click="$emit('undo')" :disabled="moveHistory.length === 0">Ход назад</button>
    <button @click="$emit('hint')" :disabled="isHintCalculating">
      {{ isHintCalculating ? 'Вычисляем...' : 'Подсказка' }}
    </button>
    <button @click="$emit('restart')">Начать заново</button>
  </div>
</template>

<script setup>
defineProps({
  moveHistory: {
    type: Array,
    required: true
  },
  isHintCalculating: {
    type: Boolean,
    required: true
  }
})
</script>