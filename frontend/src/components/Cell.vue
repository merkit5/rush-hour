<!-- Cell.vue -->
<template>
  <div
    class="cell"
    :class="{
      'empty': cell === 0,
      'wall': cell === -1,
      'car': cell > 0 && cell !== 99,
      'exit': cell === 99,
      'hidden': colIndex === gridWidth && cell !== 99,
      'hint-move': isHintMoveCell,
      'hint-car': isHintCarCell
    }"
    :style="{
      backgroundColor: cell > 0 && cell !== 99 ? getCarColor(cell) : '',
      width: `${cellSize}px`,
      height: `${cellSize}px`
    }"
    @mousedown="$emit('mousedown', $event)"
    @mousemove="$emit('mousemove', $event)"
    @mouseup="$emit('mouseup')"
  >
    <span v-if="isHintCarCell" class="hint-arrow">
      {{ hintArrow }}
    </span>
  </div>
</template>

<script setup>
const props = defineProps({
  cell: {
    type: Number,
    required: true
  },
  rowIndex: {
    type: Number,
    required: true
  },
  colIndex: {
    type: Number,
    required: true
  },
  cellSize: {
    type: Number,
    required: true
  },
  isHintMoveCell: {
    type: Boolean,
    default: false
  },
  isHintCarCell: {
    type: Boolean,
    default: false
  },
  hintArrow: {
    type: String,
    default: '→'
  },
  gridWidth: {
    type: Number,
    required: true
  }
})

const getCarColor = (carId) => {
  if (carId === -1) return "#000000"
  if (carId === 1) return "#f00"

  const hue = ((carId - 2) * 137) % 360
  return `hsl(${hue}, 70%, 60%)`
}

</script>