<!-- GameBoard.vue -->
<template>
  <div class="game-board" ref="gameBoardRef">
    <div class="grid">
      <div v-for="(row, rowIndex) in grid" :key="rowIndex" class="row">
        <Cell
          v-for="(cell, colIndex) in row"
          :key="colIndex"
          :cell="cell"
          :rowIndex="rowIndex"
          :colIndex="colIndex"
          :cellSize="cellSize"
          :gridWidth="gridWidth"
          :isHintMoveCell="isHintMoveCell(rowIndex, colIndex)"
          :isHintCarCell="isHintCarCell(rowIndex, colIndex)"
          :hintArrow="hintArrow"
          @mousedown="$emit('start-drag', { event: $event, row: rowIndex, col: colIndex })"
          @mousemove="$emit('drag-over', $event)"
          @mouseup="$emit('end-drag')"
        />
      </div>
    </div>
    
    <ControlButtons
      :moveHistory="moveHistory"
      :isHintCalculating="isHintCalculating"
      @undo="$emit('undo-move')"
      @hint="$emit('show-hint')"
      @restart="$emit('restart-game')"
    />
  </div>
</template>

<script setup>
import Cell from './Cell.vue'
import ControlButtons from './ControlButtons.vue'

const props = defineProps({
  grid: {
    type: Array,
    required: true
  },
  moveHistory: {
    type: Array,
    required: true
  },
  isHintCalculating: {
    type: Boolean,
    required: true
  },
  cellSize: {
    type: Number,
    required: true
  },
  exitRow: {
    type: Number,
    required: true
  },
  gridWidth: {
    type: Number,
    required: true
  },
  hintMoveCells: {
    type: Array,
    required: true
  },
  hintCarCells: {
    type: Array,
    required: true
  },
  hintArrow: {
    type: String,
    required: true
  }
})

const isHintMoveCell = (row, col) => {
  return props.hintMoveCells.some(c => c.row === row && c.col === col)
}

const isHintCarCell = (row, col) => {
  return props.hintCarCells.some(c => c.row === row && c.col === col)
}
</script>