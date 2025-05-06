<template>
  <div class="game-container">
    <!-- Difficulty Selection -->
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

    <!-- Game Board -->
    <div v-if="levelLoaded" class="game-board" ref="gameBoardRef">
      <div class="grid">
        <div v-for="(row, rowIndex) in grid" :key="rowIndex" class="row">
          <div
            v-for="(cell, colIndex) in row"
            :key="colIndex"
            class="cell"
            :class="{
              'empty': cell === 0,
              'wall': cell === -1,
              'car': cell > 0 && cell !== 99,
              'exit': cell === 99,
              'hidden': colIndex === 6 && cell !== 99,
              'hint-move': isHintMoveCell(rowIndex, colIndex),
              'hint-car': isHintCarCell(rowIndex, colIndex)
            }"
            :style="cell > 0 && cell !== 99 ? { backgroundColor: getCarColor(cell) } : {}"
            @mousedown="startDrag($event, rowIndex, colIndex)"
            @mousemove="dragOver($event)"
            @mouseup="endDrag"
          >
            <span v-if="isHintCarCell(rowIndex, colIndex)" class="hint-arrow">
              {{ hintArrow }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Control Buttons -->
      <div class="control-buttons">
        <button @click="undoMove" :disabled="moveHistory.length === 0">Ход назад</button>
        <button @click="showHint" :disabled="isHintCalculating">
          {{ isHintCalculating ? 'Вычисляем...' : 'Подсказка' }}
        </button>
        <button @click="restartGame">Начать заново</button>
      </div>
    </div>

    <!-- Win Screen -->
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
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { easyLevels } from '../levels/easy'
import { mediumLevels } from '../levels/medium'
import { hardLevels } from '../levels/hard'

// Game state
const levelLoaded = ref(false)
const currentDifficulty = ref('')
const currentLevelIndex = ref(0)
const grid = ref([])
const isWin = ref(false)
const moveHistory = ref([])
const isHintCalculating = ref(false)

// Hint state
const currentHint = ref(null)
const hintMoveCells = ref([])
const hintCarCells = ref([])
const hintArrow = ref('→')

// DOM reference
const gameBoardRef = ref(null)

// Car colors
const colors = [
  "#4ecdc4", // бирюзовый
  "#ffe66d", // светло-желтый
  "#ff7b00", // оранжевый
  "#54a0ff", // небесно-синий
  "#5f27cd", // фиолетовый
  "#10ac84", // морская волна
  "#f368e0", // розовый 
  "#346194", // стальной синий
  "#037f7f", // темный бирюзовый
  "#ffcc29", // золотисто-желтый
  "#2ed573", // салатовый
  "#3742fa", // насыщенный синий
  "#8c7ae6", // лавандовый
  "#44bd32", // травяной зеленый
  "#40739e", // серо-синий
  "#D980FA", // сиреневый
  "#A3CB38", // лаймово-зеленый
  "#1289A7"  // голубовато-синий
];


// Drag state
const selectedCar = ref(null)
let isDragging = false
let dragStartPosition = { x: 0, y: 0 }

// Computed properties
const currentLevels = computed(() => {
  switch (currentDifficulty.value) {
    case 'easy': return easyLevels
    case 'medium': return mediumLevels
    case 'hard': return hardLevels
    default: return easyLevels
  }
})

const hasNextLevel = computed(() => 
  currentLevelIndex.value < currentLevels.value.length - 1
)

// Helper functions
const isHintMoveCell = (row, col) => {
  return hintMoveCells.value.some(c => c.row === row && c.col === col)
}

const isHintCarCell = (row, col) => {
  return hintCarCells.value.some(c => c.row === row && c.col === col)
}

const clearHint = () => {
  currentHint.value = null
  hintMoveCells.value = []
  hintCarCells.value = []
}

// Level parsing
const parseStringLevel = (levelStr) => {
  const grid = Array(6).fill().map(() => Array(7).fill(0))
  grid[2][6] = 99 // Exit position
  
  const chars = levelStr.split('')
  let charIndex = 0
  
  for (let row = 0; row < 6; row++) {
    for (let col = 0; col < 6; col++) {
      if (charIndex >= chars.length) continue
      
      const char = chars[charIndex++]
      switch (char) {
        case 'o': grid[row][col] = 0; break
        case 'x': grid[row][col] = -1; break
        case 'A': grid[row][col] = 1; break
        default:
          if (char >= 'B' && char <= 'Z') {
            grid[row][col] = char.charCodeAt(0) - 64 + 1
          }
          break
      }
    }
  }
  
  return grid
}

const getCarColor = (carId) => {
  if (carId === -1) return "#000000"
  if (carId === 1) return "#f00"
  return colors[(carId - 2) % colors.length]
}

// Game control
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
    levelData = parseStringLevel(levelData)
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
  isWin.value = grid.value[2]?.[6] === 1
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

  if (carId === -1) return false

  if (carDirection === 'horizontal') {
    if (direction === 'left') {
      if (col === 6 && carId !== 1) return false
      return col > 0 && grid.value[row][col - 1] <= 0 && grid.value[row][col - 1] !== -1
    }
    if (direction === 'right') {
      const rightEdge = col + carLength - 1
      if (rightEdge + 1 === 6 && carId === 1 && row === 2) {
        return grid.value[2][6] === 99
      }
      if (rightEdge + 1 >= 6 && carId !== 1) return false
      if (rightEdge + 1 >= 7) return false
      return grid.value[row][rightEdge + 1] <= 0 && grid.value[row][rightEdge + 1] !== -1
    }
  } else if (carDirection === 'vertical') {
    if (col === 6) return false
    if (direction === 'up') {
      return row > 0 && grid.value[row - 1][col] <= 0 && grid.value[row - 1][col] !== -1
    }
    if (direction === 'down') {
      const bottomEdge = row + carLength - 1
      return bottomEdge + 1 < grid.value.length && 
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

  if (direction === 'right' && lastCell.col === 5 && id !== 1) return

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
// Hint system (A* algorithm)
const parseGrid = (grid) => {
  const cars = []
  const rows = grid.length
  const cols = grid[0].length - 1
  const carIds = new Set()

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const cell = grid[row][col]
      if (cell > 0 && cell !== 99) {
        carIds.add(cell)
      }
    }
  }

  carIds.forEach(carId => {
    const positions = []
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        if (grid[row][col] === carId) {
          positions.push({ row, col })
        }
      }
    }

    if (positions.length === 0) return

    positions.sort((a, b) => a.row === b.row ? a.col - b.col : a.row - b.row)

    let orientation, length
    if (positions.length > 1) {
      orientation = positions[0].row === positions[1].row ? 'h' : 'v'
    } else {
      const canMoveRight = positions[0].col < cols - 1 && grid[positions[0].row][positions[0].col + 1] <= 0
      const canMoveLeft = positions[0].col > 0 && grid[positions[0].row][positions[0].col - 1] <= 0
      orientation = canMoveRight || canMoveLeft ? 'h' : 'v'
    }

    if (orientation === 'h') {
      length = positions[positions.length - 1].col - positions[0].col + 1
    } else {
      length = positions[positions.length - 1].row - positions[0].row + 1
    }

    cars.push({
      id: carId,
      orientation,
      length,
      row: positions[0].row,
      col: positions[0].col
    })
  })

  return cars
}

const isGoalState = (cars) => {
  const redCar = cars.find(car => car.id === 1)
  return redCar && redCar.orientation === 'h' && redCar.row === 2 && 
         redCar.col + redCar.length === 6
}

const heuristic = (grid, cars) => {
  let blocking = 0
  const redCar = cars.find(car => car.id === 1)

  if (!redCar || redCar.orientation !== 'h' || redCar.row !== 2) {
    return Infinity
  }

  const exitCol = redCar.col + redCar.length
  for (let col = exitCol; col < 6; col++) {
    if (grid[2][col] > 0 && grid[2][col] !== 99) {
      blocking++
    }
  }

  return blocking
}

const getPossibleMoves = (grid, cars) => {
  const moves = [];
  cars.forEach((car, i) => {
    if (car.orientation === 'h') {
      // Left
      let maxMove = 0;
      for (let dist = 1; dist <= car.col; dist++) {
        const cell = grid[car.row][car.col - dist];
        if (cell <= 0 && cell !== -1) { // Пусто или не стена
          maxMove = dist;
        } else {
          break;
        }
      }
      if (maxMove > 0) moves.push([i, 'left', maxMove]);

      // Right
      maxMove = 0;
      if (car.id === 1) {
        const maxPossible = 6 - (car.col + car.length);
        for (let dist = 1; dist <= maxPossible; dist++) {
          const cell = grid[car.row][car.col + car.length - 1 + dist];
          if (car.col + car.length - 1 + dist < 6) {
            if (cell <= 0 && cell !== -1) {
              maxMove = dist;
            } else {
              break;
            }
          } else if (car.col + car.length - 1 + dist === 6) {
            maxMove = dist;
            break;
          }
        }
      } else {
        for (let dist = 1; dist <= 6 - (car.col + car.length); dist++) {
          const cell = grid[car.row][car.col + car.length - 1 + dist];
          if (cell <= 0 && cell !== -1) {
            maxMove = dist;
          } else {
            break;
          }
        }
      }
      if (maxMove > 0) moves.push([i, 'right', maxMove]);
    } else {
      // Up
      let maxMove = 0;
      for (let dist = 1; dist <= car.row; dist++) {
        const cell = grid[car.row - dist][car.col];
        if (cell <= 0 && cell !== -1) {
          maxMove = dist;
        } else {
          break;
        }
      }
      if (maxMove > 0) moves.push([i, 'up', maxMove]);

      // Down
      maxMove = 0;
      for (let dist = 1; dist <= 6 - (car.row + car.length); dist++) {
        const cell = grid[car.row + car.length - 1 + dist][car.col];
        if (cell <= 0 && cell !== -1) {
          maxMove = dist;
        } else {
          break;
        }
      }
      if (maxMove > 0) moves.push([i, 'down', maxMove]);
    }
  });

  return moves;
};

const applyMove = (grid, cars, move) => {
  const [carIdx, direction, distance] = move
  const car = cars[carIdx]
  const newGrid = grid.map(row => [...row])
  const newCars = cars.map(c => ({ ...c }))

  for (let i = 0; i < car.length; i++) {
    if (car.orientation === 'h') {
      newGrid[car.row][car.col + i] = 0
    } else {
      newGrid[car.row + i][car.col] = 0
    }
  }

  if (direction === 'left') {
    newCars[carIdx].col -= distance
  } else if (direction === 'right') {
    newCars[carIdx].col += distance
  } else if (direction === 'up') {
    newCars[carIdx].row -= distance
  } else if (direction === 'down') {
    newCars[carIdx].row += distance
  }

  for (let i = 0; i < newCars[carIdx].length; i++) {
    if (newCars[carIdx].orientation === 'h') {
      const col = newCars[carIdx].col + i
      if (col < 6) {
        newGrid[newCars[carIdx].row][col] = car.id
      }
    } else {
      newGrid[newCars[carIdx].row + i][newCars[carIdx].col] = car.id
    }
  }

  return [newGrid, newCars]
}

const solveRushHourAStar = (initialGrid) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      try {
        const initialCars = parseGrid(initialGrid)
        
        if (isGoalState(initialCars)) {
          resolve([])
          return
        }

        const openSet = []
        openSet.push({ 
          fScore: 0,
          gScore: 0,
          grid: initialGrid,
          cars: initialCars,
          path: []
        })

        const visited = new Map()
        const initialStateKey = gridToKey(initialGrid)
        visited.set(initialStateKey, 0)

        const MAX_ITERATIONS = 20000
        let iterations = 0

        while (openSet.length > 0 && iterations < MAX_ITERATIONS) {
          iterations++
          
          if (openSet.length > 1) {
            openSet.sort((a, b) => a.fScore - b.fScore)
          }
          const current = openSet.shift()
          
          const currentKey = gridToKey(current.grid)
          if (visited.has(currentKey)) {
            const bestGScore = visited.get(currentKey)
            if (current.gScore > bestGScore) {
              continue
            }
          }

          if (isGoalState(current.cars)) {
            resolve(current.path)
            return
          }

          const moves = getPossibleMoves(current.grid, current.cars)
          for (const move of moves) {
            const [newGrid, newCars] = applyMove(current.grid, current.cars, move)
            const newKey = gridToKey(newGrid)
            
            const tentativeGScore = current.gScore + 1
            
            if (!visited.has(newKey) || tentativeGScore < visited.get(newKey)) {
              visited.set(newKey, tentativeGScore)
              
              const hScore = heuristic(newGrid, newCars)
              const fScore = tentativeGScore + hScore
              
              openSet.push({
                fScore,
                gScore: tentativeGScore,
                grid: newGrid,
                cars: newCars,
                path: [...current.path, move]
              })
            }
          }
        }
        
        console.log(`A* завершен за ${iterations} итераций`)
        resolve(null)
      } catch (error) {
        console.error('Ошибка в A*:', error)
        resolve(null)
      }
    }, 0)
  })
}

const gridToKey = (grid) => {
  return grid.map(row => row.slice(0, 6).join(',')).join('|')
}

const showHint = async () => {
  if (isHintCalculating.value) return
  
  clearHint()
  isHintCalculating.value = true
  
  try {
    const solution = await solveRushHourAStar(grid.value)
    
    if (solution && solution.length > 0) {
      currentHint.value = solution[0]
      const cars = parseGrid(grid.value)
      const car = cars[currentHint.value[0]]
      const direction = currentHint.value[1]
      const distance = currentHint.value[2]
      
      switch(direction) {
        case 'left': hintArrow.value = '←'; break
        case 'right': hintArrow.value = '→'; break
        case 'up': hintArrow.value = '↑'; break
        case 'down': hintArrow.value = '↓'; break
      }
      
      hintCarCells.value = []
      for (let i = 0; i < car.length; i++) {
        if (car.orientation === 'h') {
          hintCarCells.value.push({ row: car.row, col: car.col + i })
        } else {
          hintCarCells.value.push({ row: car.row + i, col: car.col })
        }
      }
      
      hintMoveCells.value = []
      if (car.orientation === 'h') {
        const newCol = direction === 'left' ? car.col - distance : car.col + distance
        for (let i = 0; i < car.length; i++) {
          hintMoveCells.value.push({ row: car.row, col: newCol + i })
        }
      } else {
        const newRow = direction === 'up' ? car.row - distance : car.row + distance
        for (let i = 0; i < car.length; i++) {
          hintMoveCells.value.push({ row: newRow + i, col: car.col })
        }
      }
    } else {
      alert('Решение не найдено или вы уже у цели!')
    }
  } catch (error) {
    console.error('Ошибка при вычислении подсказки:', error)
    alert('Не удалось вычислить подсказку')
  } finally {
    isHintCalculating.value = false
  }
}
</script>

<style scoped>
/* Add these styles for walls and empty cells */
.cell.wall {
  background-color: #333;
  position: relative;
  overflow: hidden;
}

.cell.wall::before,
.cell.wall::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom right, transparent 45%, #ff0000 45%, #ff0000 55%, transparent 55%);
}

.cell.wall::after {
  background: linear-gradient(to top right, transparent 45%, #ff0000 45%, #ff0000 55%, transparent 55%);
}

/* Rest of your existing styles... */
</style>