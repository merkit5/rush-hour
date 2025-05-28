<!-- SizeSelectionModal.vue -->
<template>
  <div class="modal-overlay">
    <div class="modal">
      <h2>Выберите размер игрового поля</h2>
      <div class="size-buttons">
        <button @click="selectSize('5x5')">5×5</button>
        <button @click="selectSize('6x6')">6×6</button>
        <button @click="selectSize('7x7')">7×7</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['select-size'])

const selectSize = (size) => {
  emit('select-size', size)
}
</script>