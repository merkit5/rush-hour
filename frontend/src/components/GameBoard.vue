<template>
  <div class="game-container">
    <!-- Size Selection -->
    <div v-if="!sizeSelected" class="modal-overlay">
      <div class="modal">
        <h2>Выберите размер доски</h2>
        <div class="size-buttons">
          <button @click="selectSize('5x5')">5×5</button>
          <button @click="selectSize('6x6')">6×6</button>
          <button @click="selectSize('7x7')">7×7</button>
        </div>
      </div>
    </div>

    <!-- Difficulty Selection -->
    <div v-if="sizeSelected && !levelLoaded" class="modal-overlay">
      <div class="modal">
        <h2>Выберите сложность</h2>
        <div class="difficulty-buttons">
          <button @click="startGame('easy')">Легкий</button>
          <button @click="startGame('medium')">Средний</button>
          <button @click="startGame('hard')">Сложный</button>
        </div>
        <button class="back-button" @click="sizeSelected = false">← Назад</button>
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
              'hidden': colIndex === grid[0].length-1 && cell !== 99,
              'hint-move': isHintMoveCell(rowIndex, colIndex),
              'hint-car': isHintCarCell(rowIndex, colIndex)
            }"
            :style="{
              backgroundColor: cell > 0 && cell !== 99 ? getCarColor(cell) : '',
              width: `${cellSize}px`,
              height: `${cellSize}px`
            }"
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
import { easyLevels_5x5 } from '../levels/easy_5x5'
import { mediumLevels_5x5 } from '../levels/medium_5x5'
import { hardLevels_5x5 } from '../levels/hard_5x5'
import { easyLevels_6x6 } from '../levels/easy_6x6'
import { mediumLevels_6x6 } from '../levels/medium_6x6'
import { hardLevels_6x6 } from '../levels/hard_6x6'
import { easyLevels_7x7 } from '../levels/easy_7x7'
import { mediumLevels_7x7 } from '../levels/medium_7x7'
import { hardLevels_7x7 } from '../levels/hard_7x7'

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

// Hint state
const currentHint = ref(null)
const hintMoveCells = ref([])
const hintCarCells = ref([])
const hintArrow = ref('→')

// DOM reference
const gameBoardRef = ref(null)

// Car colors
const colors = [
  "#4ecdc4", "#ffe66d", "#ff7b00", "#54a0ff", 
  "#5f27cd", "#10ac84", "#f368e0", "#346194",
  "#037f7f", "#ffcc29", "#2ed573", "#3742fa",
  "#8c7ae6", "#44bd32", "#40739e", "#D980FA",
  "#A3CB38", "#1289A7"
];

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
const currentLevels = computed(() => {
  if (selectedSize.value === '5x5') {
    switch (currentDifficulty.value) {
      case 'easy': return easyLevels_5x5
      case 'medium': return mediumLevels_5x5
      case 'hard': return hardLevels_5x5
      default: return easyLevels_5x5
    }
  } else if (selectedSize.value === '7x7') {
    switch (currentDifficulty.value) {
      case 'easy': return easyLevels_7x7
      case 'medium': return mediumLevels_7x7
      case 'hard': return hardLevels_7x7
      default: return easyLevels_7x7
    }
  } else { // 6x6 по умолчанию
    switch (currentDifficulty.value) {
      case 'easy': return easyLevels_6x6
      case 'medium': return mediumLevels_6x6
      case 'hard': return hardLevels_6x6
      default: return easyLevels_6x6
    }
  }
})

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
  const width = gridWidth.value
  const height = gridHeight.value
  
  const grid = Array(height).fill().map(() => Array(width + 1).fill(0))
  
  // Set exit position
  grid[exitRow.value][width] = 99
  
  const chars = levelStr.split('')
  let charIndex = 0
  
  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
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
const selectSize = (size) => {
  selectedSize.value = size
  sizeSelected.value = true
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

const isGoalState = (cars, exitRow, exitCol) => {
  const redCar = cars.find(car => car.id === 1);
  return redCar && 
         redCar.orientation === 'h' && 
         redCar.row === exitRow && 
         redCar.col + redCar.length === exitCol;
};

const heuristic = (grid, cars, exitRow, exitCol) => {
  const redCar = cars.find(car => car.id === 1);
  if (!redCar || redCar.orientation !== 'h' || redCar.row !== exitRow) {
    return 1000;
  }

  let blocking = 0;
  const exitColRed = redCar.col + redCar.length;
  
  for (let col = exitColRed; col < exitCol; col++) {
    if (grid[exitRow][col] > 0 && grid[exitRow][col] !== 99) {
      blocking++;
    }
  }

  return blocking;
};

const getPossibleMoves = (grid, cars, width, height, exitRow) => {
  const moves = [];
  
  cars.forEach((car, i) => {
    if (car.orientation === 'h') {
      // Left moves
      let leftMove = 0;
      for (let dist = 1; dist <= car.col; dist++) {
        if (grid[car.row][car.col - dist] === 0) {
          leftMove = dist;
        } else {
          break;
        }
      }
      if (leftMove > 0) moves.push([i, 'left', leftMove]);

      // Right moves
      let rightMove = 0;
      for (let dist = 1; dist <= (width - (car.col + car.length)); dist++) {
        const newCol = car.col + car.length - 1 + dist;
        if (newCol < width) {
          if (grid[car.row][newCol] === 0) {
            rightMove = dist;
          } else {
            break;
          }
        } else if (newCol === width && car.id === 1) {
          rightMove = dist;
          break;
        }
      }
      if (rightMove > 0) moves.push([i, 'right', rightMove]);
    } else {
      // Up moves
      let upMove = 0;
      for (let dist = 1; dist <= car.row; dist++) {
        if (grid[car.row - dist][car.col] === 0) {
          upMove = dist;
        } else {
          break;
        }
      }
      if (upMove > 0) moves.push([i, 'up', upMove]);

      // Down moves
      let downMove = 0;
      for (let dist = 1; dist <= (height - (car.row + car.length)); dist++) {
        if (grid[car.row + car.length - 1 + dist][car.col] === 0) {
          downMove = dist;
        } else {
          break;
        }
      }
      if (downMove > 0) moves.push([i, 'down', downMove]);
    }
  });

  return moves;
};

const applyMove = (grid, cars, move, width, height) => {
  const [carIdx, direction, distance] = move;
  const car = cars[carIdx];
  const newGrid = grid.map(row => [...row]);
  const newCars = cars.map(c => ({ ...c }));

  // Clear old position
  for (let i = 0; i < car.length; i++) {
    if (car.orientation === 'h') {
      newGrid[car.row][car.col + i] = 0;
    } else {
      newGrid[car.row + i][car.col] = 0;
    }
  }

  // Update position
  if (direction === 'left') {
    newCars[carIdx].col -= distance;
  } else if (direction === 'right') {
    newCars[carIdx].col += distance;
  } else if (direction === 'up') {
    newCars[carIdx].row -= distance;
  } else if (direction === 'down') {
    newCars[carIdx].row += distance;
  }

  // Fill new position
  for (let i = 0; i < newCars[carIdx].length; i++) {
    if (newCars[carIdx].orientation === 'h') {
      const col = newCars[carIdx].col + i;
      if (col < width) {
        newGrid[newCars[carIdx].row][col] = car.id;
      }
    } else {
      newGrid[newCars[carIdx].row + i][newCars[carIdx].col] = car.id;
    }
  }

  return [newGrid, newCars];
};

const solveRushHourAStar = (initialGrid) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      try {
        const initialCars = parseGrid(initialGrid);
        const width = gridWidth.value;
        const height = gridHeight.value;
        const exitRowValue = exitRow.value;
        const exitCol = width;
        
        if (isGoalState(initialCars, exitRowValue, exitCol)) {
          resolve([]);
          return;
        }

        const openSet = new PriorityQueue((a, b) => a.fScore - b.fScore);
        openSet.push({
          fScore: 0,
          gScore: 0,
          grid: initialGrid,
          cars: initialCars,
          path: []
        });

        const visited = new Map();
        const initialStateKey = gridToKey(initialGrid);
        visited.set(initialStateKey, 0);

        while (!openSet.isEmpty()) {
          const current = openSet.pop();
          
          if (isGoalState(current.cars, exitRowValue, exitCol)) {
            resolve(current.path);
            return;
          }

          const moves = getPossibleMoves(current.grid, current.cars, width, height, exitRowValue);
          for (const move of moves) {
            const [newGrid, newCars] = applyMove(current.grid, current.cars, move, width, height);
            const newKey = gridToKey(newGrid);
            
            const newG = current.gScore + 1;
            
            if (!visited.has(newKey) || newG < visited.get(newKey)) {
              visited.set(newKey, newG);
              
              const h = heuristic(newGrid, newCars, exitRowValue, exitCol);
              const f = newG + h;
              
              openSet.push({
                fScore: f,
                gScore: newG,
                grid: newGrid,
                cars: newCars,
                path: [...current.path, move]
              });
            }
          }
        }
        
        resolve(null);
      } catch (error) {
        console.error('A* error:', error);
        resolve(null);
      }
    }, 0);
  });
};

// Простая реализация PriorityQueue
class PriorityQueue {
  constructor(comparator = (a, b) => a - b) {
    this.elements = [];
    this.comparator = comparator;
  }

  push(element) {
    this.elements.push(element);
    this.elements.sort(this.comparator);
  }

  pop() {
    return this.elements.shift();
  }

  isEmpty() {
    return this.elements.length === 0;
  }
}

const gridToKey = (grid) => {
  const width = gridWidth.value
  return grid.map(row => row.slice(0, width).join(',')).join('|')
}

const showHint = async () => {
  if (isHintCalculating.value) return;
  
  clearHint();
  isHintCalculating.value = true;
  
  try {
    console.log("Начало вычисления подсказки...");
    const startTime = performance.now();
    const solution = await solveRushHourAStar(grid.value);
    const endTime = performance.now();
    
    console.log(`Вычисление заняло ${(endTime - startTime).toFixed(2)} мс`);
    
    if (solution && solution.length > 0) {
      console.log("Найденное решение:", solution[0]);
      currentHint.value = solution[0];
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