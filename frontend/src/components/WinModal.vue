<!-- WinModal.vue -->
<template>
  <div class="modal-overlay">
    <div class="modal">
      <h2>Поздравляем! 🎉</h2>
      <p>Вы выиграли уровень {{ levelNumber }}!</p>
      <div class="win-buttons">
        <button 
          v-if="hasNextLevel" 
          @click="nextLevel"
        >
          Следующий уровень
        </button>
        <button @click="restart">Повторить уровень</button>
        <button @click="changeDifficulty">Выбрать другую сложность</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  levelNumber: {
    type: Number,
    required: true
  },
  hasNextLevel: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['next-level', 'restart', 'change-difficulty'])

const nextLevel = () => {
  emit('next-level')
}

const restart = () => {
  emit('restart')
}

const changeDifficulty = () => {
  emit('change-difficulty')
}
</script>