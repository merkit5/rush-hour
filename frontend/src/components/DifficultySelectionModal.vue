<!-- DifficultySelectionModal.vue -->
<template>
  <div class="modal-overlay">
    <div class="modal">
      <h2>Выберите сложность</h2>
      <div class="difficulty-buttons">
        <button @click="startGame('easy')">Легкий</button>
        <button @click="startGame('medium')">Средний</button>
        <button @click="startGame('hard')">Сложный</button>
      </div>
      <button class="back-button" @click="goBack">← Назад</button>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['start-game', 'go-back'])

const startGame = (difficulty) => {
  emit('start-game', difficulty)
}

const goBack = () => {
  emit('go-back')
}
</script>