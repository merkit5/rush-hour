<template>
  <div id="app">
    <h1>Час пик</h1>
    <p class="hint">Выведите <strong>красную машину</strong> в выход (зеленая клетка)!</p>
    <GameBoard />
  </div>
</template>

<script setup>
import GameBoard from './components/GameBoard.vue'
</script>

<style src="./assets/style.css"></style>
