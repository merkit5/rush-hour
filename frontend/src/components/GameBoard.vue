<template>
  <div class="game-container">
    <!-- Окно выбора сложности -->
    <div v-if="!levelLoaded" class="modal-overlay">
      <div class="modal">
        <h2>Выберите сложность</h2>
        <div class="difficulty-buttons">
          <button @click="startGame('easy')">Легкий</button>
          <button @click="startGame('medium')">Средний</button>
          <button @click="startGame('hard')">Сложный</button>
        </div>
      </div>
    </div>

    <!-- Игровое поле -->
    <div v-if="levelLoaded" class="game-board">
      <div class="grid">
        <div v-for="(row, rowIndex) in grid" :key="rowIndex" class="row">
          <div
            v-for="(cell, colIndex) in row"
            :key="colIndex"
            class="cell"
            :class="{
              'car': cell > 0 && cell !== 99,
              'exit': cell === 99,
              'hidden': colIndex === 6 && cell !== 99
            }"
            :style="cell > 0 && cell !== 99 ? { backgroundColor: getCarColor(cell) } : {}"
            @mousedown="startDrag($event, rowIndex, colIndex)"
            @mousemove="dragOver($event)"
            @mouseup="endDrag"
          ></div>
        </div>
      </div>
    </div>

    <!-- Окно победы -->
    <div v-if="isWin" class="modal-overlay">
      <div class="modal">
        <h2>Поздравляем! 🎉</h2>
        <p>Вы выиграли уровень {{ currentLevelIndex + 1 }}!</p>
        <div class="win-buttons">
          <button @click="nextLevel" v-if="hasNextLevel">Следующий уровень</button>
          <button @click="restartGame">Повторить уровень</button>
          <button @click="changeDifficulty">Выбрать другую сложность</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { easyLevels } from '../levels/easy'
import { mediumLevels } from '../levels/medium'
import { hardLevels } from '../levels/hard'

const levelLoaded = ref(false)
const currentDifficulty = ref('')
const currentLevelIndex = ref(0)
const grid = ref([])
const isWin = ref(false)

const currentLevels = computed(() => {
  switch (currentDifficulty.value) {
    case 'easy': return easyLevels
    case 'medium': return mediumLevels
    case 'hard': return hardLevels
    default: return easyLevels
  }
})

const checkWin = () => {
  isWin.value = grid.value[2]?.[6] === 1
}

const hasNextLevel = computed(() =>
  currentLevelIndex.value < currentLevels.value.length - 1
)

// Цвета машин
const colors = [
  "#4ecdc4", "#ffe66d", "#ff9f43", "#54a0ff",
  "#5f27cd", "#10ac84", "#f368e0", "#222f3e", "#01a3a4",
  "#ffcc29", "#ff4757", "#2ed573", "#3742fa", "#8c7ae6",
  "#e84118", "#44bd32", "#40739e", "#b71540", "#6D214F",
  "#D980FA", "#ED4C67", "#A3CB38", "#1289A7"
]

const selectedCar = ref(null)
let isDragging = false
let dragStartPosition = { x: 0, y: 0 }

const getCarColor = (carId) => {
  if (carId === 1) return "#ff6b6b"
  return colors[(carId - 2) % colors.length]
}

const startGame = (difficulty) => {
  currentDifficulty.value = difficulty
  currentLevelIndex.value = 0
  selectedCar.value = null
  isDragging = false
  loadLevel()
  levelLoaded.value = true
  isWin.value = false
}

const loadLevel = () => {
  selectedCar.value = null
  isDragging = false

  const levelData = JSON.parse(JSON.stringify(currentLevels.value[currentLevelIndex.value]))

  // Небольшая задержка (опционально)
  setTimeout(() => {
    grid.value = levelData
    isWin.value = false
    checkWin()
  }, 50)
}

const restartGame = () => {
  selectedCar.value = null
  isDragging = false
  loadLevel()
}

const nextLevel = () => {
  if (hasNextLevel.value) {
    currentLevelIndex.value++
    selectedCar.value = null
    isDragging = false
    loadLevel()
  } else {
    changeDifficulty()
  }
}

const changeDifficulty = () => {
  levelLoaded.value = false
  currentLevelIndex.value = 0
  isWin.value = false
  selectedCar.value = null
  isDragging = false
}

const getCarLength = (carId) =>
  grid.value.flat().filter(cell => cell === carId).length

const getCarDirection = (row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99) return null

  if (
    (col + 1 < grid.value[0].length && grid.value[row][col + 1] === carId) ||
    (col - 1 >= 0 && grid.value[row][col - 1] === carId)
  ) return 'horizontal'

  if (
    (row + 1 < grid.value.length && grid.value[row + 1][col] === carId) ||
    (row - 1 >= 0 && grid.value[row - 1][col] === carId)
  ) return 'vertical'

  return null
}

const canMove = (row, col, direction, carDirection) => {
  const carId = grid.value[row][col]
  const carLength = getCarLength(carId)

  if (carDirection === 'horizontal') {
    if (direction === 'left') {
      if (col === 6 && carId !== 1) return false
      return col > 0 && grid.value[row][col - 1] === 0
    }
    if (direction === 'right') {
      const rightEdge = col + carLength - 1
      if (rightEdge + 1 === 6 && carId === 1 && row === 2) {
        return grid.value[2][6] === 99
      }
      if (rightEdge + 1 >= 6 && carId !== 1) return false
      if (rightEdge + 1 >= 7) return false
      return grid.value[row][rightEdge + 1] === 0
    }
  } else if (carDirection === 'vertical') {
    if (col === 6) return false
    if (direction === 'up') {
      return row > 0 && grid.value[row - 1][col] === 0
    }
    if (direction === 'down') {
      const bottomEdge = row + carLength - 1
      return bottomEdge + 1 < grid.value.length && grid.value[bottomEdge + 1][col] === 0
    }
  }
  return false
}

const moveCar = (direction) => {
  if (!selectedCar.value) return

  const { cells, id, direction: carDirection } = selectedCar.value
  const firstCell = cells[0]
  const lastCell = cells[cells.length - 1]

  if (direction === 'right' && lastCell.col === 5 && id !== 1) return

  if (canMove(firstCell.row, firstCell.col, direction, carDirection)) {
    cells.forEach(cell => grid.value[cell.row][cell.col] = 0)
    const newCells = cells.map(cell => {
      let newRow = cell.row, newCol = cell.col
      if (direction === 'up') newRow--
      if (direction === 'down') newRow++
      if (direction === 'left') newCol--
      if (direction === 'right') newCol++
      return { row: newRow, col: newCol }
    })
    newCells.forEach(cell => grid.value[cell.row][cell.col] = id)
    selectedCar.value.cells = newCells
    checkWin()
  }
}

const startDrag = (event, row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99 || isDragging) return

  isDragging = true
  dragStartPosition = { x: event.clientX, y: event.clientY }

  const carCells = []
  grid.value.forEach((r, i) => {
    r.forEach((c, j) => {
      if (c === carId) carCells.push({ row: i, col: j })
    })
  })

  if (carCells.length > 0) {
    const direction = getCarDirection(row, col)

    carCells.sort((a, b) => {
      return direction === 'horizontal' ? a.col - b.col : a.row - b.row
    })

    selectedCar.value = {
      cells: carCells,
      id: carId,
      direction
    }

    carCells.forEach(cell => {
      const cellElement = document.querySelector(`.row:nth-child(${cell.row + 1}) .cell:nth-child(${cell.col + 1})`)
      cellElement?.classList.add('active')
    })
  }
}

const dragOver = (event) => {
  if (!isDragging || !selectedCar.value || !levelLoaded.value) return

  const deltaX = event.clientX - dragStartPosition.x
  const deltaY = event.clientY - dragStartPosition.y

  if (selectedCar.value.direction === 'horizontal') {
    if (deltaX < -50) {
      moveCar('left')
      dragStartPosition.x = event.clientX
    }
    if (deltaX > 50) {
      moveCar('right')
      dragStartPosition.x = event.clientX
    }
  } else if (selectedCar.value.direction === 'vertical') {
    if (deltaY < -50) {
      moveCar('up')
      dragStartPosition.y = event.clientY
    }
    if (deltaY > 50) {
      moveCar('down')
      dragStartPosition.y = event.clientY
    }
  }
}

const endDrag = () => {
  if (!isDragging) return
  document.querySelectorAll('.cell.active').forEach(el => el.classList.remove('active'))
  isDragging = false
  selectedCar.value = null
}
</script>
