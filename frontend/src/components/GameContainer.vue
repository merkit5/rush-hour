<template>
  <div class="game-container">
    <!-- Size Selection -->
    <SizeSelectionModal 
      v-if="!sizeSelected" 
      @select-size="handleSizeSelect"
    />


    <!-- Difficulty Selection -->
    <DifficultySelectionModal
      v-if="sizeSelected && !levelLoaded"
      @start-game="startGame"
      @go-back="handleGoBack"
    />

    <!-- Game Board -->
     <GameBoard
        v-if="levelLoaded"
        :grid="grid"
        :moveHistory="moveHistory"
        :isHintCalculating="isHintCalculating"
        :cellSize="cellSize"
        :exitRow="exitRow"
        :gridWidth="gridWidth"
        :hintMoveCells="hintMoveCells"
        :hintCarCells="hintCarCells"
        :hintArrow="hintArrow"
        @start-drag="handleStartDrag"
        @drag-over="handleDragOver"
        @end-drag="handleEndDrag"
        @undo-move="undoMove"
        @show-hint="showHint"
        @restart-game="restartGame"
      />

    <!-- Win Screen -->
    <WinModal
      v-if="isWin"
      :level-number="currentLevelIndex + 1"
      :has-next-level="hasNextLevel"
      @next-level="nextLevel"
      @restart="restartGame"
      @change-difficulty="changeDifficulty"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import SizeSelectionModal from './SizeSelectionModal.vue'
import DifficultySelectionModal from './DifficultySelectionModal.vue'
import GameBoard from './GameBoard.vue'
import WinModal from './WinModal.vue'
import { getLevels, parseStringLevel } from '../services/levelService'
import { solveRushHourAStar, parseGrid  } from '../services/rushHourSolver'

// Game state
const sizeSelected = ref(false)
const selectedSize = ref('6x6')
const levelLoaded = ref(false)
const currentDifficulty = ref('')
const currentLevelIndex = ref(0)
const grid = ref([])
const isWin = ref(false)
const moveHistory = ref([])
const isHintCalculating = ref(false)

const handleSizeSelect = (size) => {
  selectedSize.value = size
  sizeSelected.value = true
}

const handleGoBack = () => {
  sizeSelected.value = false
}

const handleStartDrag = ({ event, row, col }) => {
  startDrag(event, row, col)
}

const handleDragOver = (event) => {
  dragOver(event)
}

const handleEndDrag = () => {
  endDrag()
}
// Hint state
const currentHint = ref(null)
const hintMoveCells = ref([])
const hintCarCells = ref([])
const hintArrow = ref('→')

// DOM reference
const gameBoardRef = ref(null)

// Drag state
const selectedCar = ref(null)
let isDragging = false
let dragStartPosition = { x: 0, y: 0 }

// В разделе computed свойств, добавьте:
const cellSize = computed(() => {
  switch(selectedSize.value) {
    case '5x5': return 70
    case '6x6': return 60
    case '7x7': return 50
    default: return 60
  }
})

// Computed properties
const currentLevels = computed(() => 
  getLevels(selectedSize.value, currentDifficulty.value)
)

const hasNextLevel = computed(() => 
  currentLevelIndex.value < currentLevels.value.length - 1
)

const gridWidth = computed(() => parseInt(selectedSize.value[0]))
const gridHeight = computed(() => parseInt(selectedSize.value[2]))
const exitRow = computed(() => {
  switch(selectedSize.value) {
    case '5x5': return 2
    case '6x6': return 2
    case '7x7': return 3
    default: return 2
  }
})

const clearHint = () => {
  currentHint.value = null
  hintMoveCells.value = []
  hintCarCells.value = []
}


const startGame = (difficulty) => {
  currentDifficulty.value = difficulty
  currentLevelIndex.value = 0
  selectedCar.value = null
  isDragging = false
  moveHistory.value = []
  clearHint()
  loadLevel()
  levelLoaded.value = true
  isWin.value = false
}

const loadLevel = () => {
  selectedCar.value = null
  isDragging = false
  moveHistory.value = []
  clearHint()

  let levelData = currentLevels.value[currentLevelIndex.value]
  
  if (typeof levelData === 'string') {
    levelData = parseStringLevel(
      levelData,
      gridWidth.value,
      gridHeight.value,
      exitRow.value
    )
  } else {
    levelData = JSON.parse(JSON.stringify(levelData))
  }

  setTimeout(() => {
    grid.value = levelData
    isWin.value = false
    checkWin()
  }, 50)
}

const checkWin = () => {
  isWin.value = grid.value[exitRow.value]?.[gridWidth.value] === 1
}

const restartGame = () => {
  selectedCar.value = null
  isDragging = false
  moveHistory.value = []
  clearHint()
  loadLevel()
}

const nextLevel = () => {
  if (hasNextLevel.value) {
    currentLevelIndex.value++
    selectedCar.value = null
    isDragging = false
    moveHistory.value = []
    clearHint()
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
  moveHistory.value = []
  clearHint()
}

// Car movement logic
const getCarLength = (carId) => 
  grid.value.flat().filter(cell => cell === carId).length

const getCarDirection = (row, col) => {
  const carId = grid.value[row][col]
  if (carId <= 0 || carId === 99) return null

  if ((col + 1 < grid.value[0].length && grid.value[row][col + 1] === carId) ||
      (col - 1 >= 0 && grid.value[row][col - 1] === carId)) {
    return 'horizontal'
  }

  if ((row + 1 < grid.value.length && grid.value[row + 1][col] === carId) ||
      (row - 1 >= 0 && grid.value[row - 1][col] === carId)) {
    return 'vertical'
  }

  return null
}

const canMove = (row, col, direction, carDirection) => {
  const carId = grid.value[row][col]
  const carLength = getCarLength(carId)
  const width = gridWidth.value
  const height = gridHeight.value

  if (carId <= 0 || carId === 99) return false

  if (carDirection === 'horizontal') {
    if (direction === 'left') {
      if (col === width && carId !== 1) return false
      return col > 0 && grid.value[row][col - 1] <= 0 && grid.value[row][col - 1] !== -1
    }
    if (direction === 'right') {
      const rightEdge = col + carLength - 1
      if (rightEdge + 1 === width && carId === 1 && row === exitRow.value) {
        return grid.value[exitRow.value][width] === 99
      }
      if (rightEdge + 1 >= width && carId !== 1) return false
      return grid.value[row][rightEdge + 1] <= 0 && grid.value[row][rightEdge + 1] !== -1
    }
  } else if (carDirection === 'vertical') {
    if (col === width) return false
    if (direction === 'up') {
      return row > 0 && grid.value[row - 1][col] <= 0 && grid.value[row - 1][col] !== -1
    }
    if (direction === 'down') {
      const bottomEdge = row + carLength - 1
      return bottomEdge + 1 < height && 
             grid.value[bottomEdge + 1][col] <= 0 && 
             grid.value[bottomEdge + 1][col] !== -1
    }
  }
  return false
}

const saveCurrentState = () => {
  moveHistory.value.push(JSON.parse(JSON.stringify(grid.value)))
  if (moveHistory.value.length > 50) {
    moveHistory.value.shift()
  }
}

const moveCar = (direction) => {
  if (!selectedCar.value) return

  const { cells, id, direction: carDirection } = selectedCar.value
  const firstCell = cells[0]
  const lastCell = cells[cells.length - 1]
  const width = gridWidth.value

  // Убрать проверку с жестко закодированным значением
  if (direction === 'right' && lastCell.col === width - 1 && id !== 1) return

  if (canMove(firstCell.row, firstCell.col, direction, carDirection)) {
    saveCurrentState()
    
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
    clearHint()
  }
}

const undoMove = () => {
  if (moveHistory.value.length === 0) return
  
  const previousState = moveHistory.value.pop()
  grid.value = JSON.parse(JSON.stringify(previousState))
  checkWin()
  clearHint()
}

// Drag and drop functionality
const startDrag = (event, row, col) => {
  const carId = grid.value[row][col]
  if (carId <= 0 || carId === 99 || isDragging) return

  event.preventDefault()

  if (currentHint.value && carId === currentHint.value[0]) {
    clearHint()
  }

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

const handleMouseUp = (event) => {
  if (isDragging) {
    endDrag()
  }
}

const handleMouseLeave = (event) => {
  if (isDragging && event.buttons === 0) {
    endDrag()
  }
}

const endDrag = () => {
  if (!isDragging) return
  
  document.querySelectorAll('.cell.active').forEach(el => {
    el.classList.remove('active')
  })
  
  isDragging = false
  selectedCar.value = null
  dragStartPosition = { x: 0, y: 0 }
}

// Event listeners setup
const setupEventListeners = () => {
  document.addEventListener('mouseup', handleMouseUp)
  if (gameBoardRef.value) {
    gameBoardRef.value.addEventListener('mouseleave', handleMouseLeave)
  }
}

const cleanupEventListeners = () => {
  document.removeEventListener('mouseup', handleMouseUp)
  if (gameBoardRef.value) {
    gameBoardRef.value.removeEventListener('mouseleave', handleMouseLeave)
  }
}

// Lifecycle hooks
onMounted(() => {
  setupEventListeners()
})

onBeforeUnmount(() => {
  cleanupEventListeners()
})

const showHint = async () => {
  if (isHintCalculating.value) return;
  
  clearHint();
  isHintCalculating.value = true;
  
  try {
    console.log("Начало вычисления подсказки...");
    const startTime = performance.now();
    const solution = await solveRushHourAStar(
      grid.value,
      gridWidth.value,
      gridHeight.value,
      exitRow.value
    );
    const endTime = performance.now();
    
    console.log(`Вычисление заняло ${(endTime - startTime).toFixed(2)} мс`);
    
    if (solution && solution.length > 0) {
      console.log("Найденное решение:", solution[0]);
      currentHint.value = solution[0];
      const cars = parseGrid(grid.value, gridWidth.value); // Оставляем только эту строку
      const car = cars[currentHint.value[0]];
      const direction = currentHint.value[1];
      const distance = currentHint.value[2];
      
      switch(direction) {
        case 'left': hintArrow.value = '←'; break;
        case 'right': hintArrow.value = '→'; break;
        case 'up': hintArrow.value = '↑'; break;
        case 'down': hintArrow.value = '↓'; break;
      }
      
      hintCarCells.value = [];
      for (let i = 0; i < car.length; i++) {
        if (car.orientation === 'h') {
          hintCarCells.value.push({ row: car.row, col: car.col + i });
        } else {
          hintCarCells.value.push({ row: car.row + i, col: car.col });
        }
      }
      
      hintMoveCells.value = [];
      if (car.orientation === 'h') {
        const newCol = direction === 'left' ? car.col - distance : car.col + distance;
        for (let i = 0; i < car.length; i++) {
          hintMoveCells.value.push({ row: car.row, col: newCol + i });
        }
      } else {
        const newRow = direction === 'up' ? car.row - distance : car.row + distance;
        for (let i = 0; i < car.length; i++) {
          hintMoveCells.value.push({ row: newRow + i, col: car.col });
        }
      }
    } else {
      console.log("Решение не найдено");
      alert('Решение не найдено или вы уже у цели!');
    }
  } catch (error) {
    console.error('Ошибка при вычислении подсказки:', error);
    alert('Не удалось вычислить подсказку');
  } finally {
    isHintCalculating.value = false;
  }
};
</script>