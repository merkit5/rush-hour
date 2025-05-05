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
      
      <!-- Кнопки управления -->
      <div class="control-buttons">
        <button @click="undoMove" :disabled="moveHistory.length === 0">Ход назад</button>
        <button @click="showHint" :disabled="isHintCalculating">
          {{ isHintCalculating ? 'Вычисляем...' : 'Подсказка' }}
        </button>
        <button @click="restartGame">Начать заново</button>
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

// Состояние игры
const levelLoaded = ref(false)
const currentDifficulty = ref('')
const currentLevelIndex = ref(0)
const grid = ref([])
const isWin = ref(false)
const moveHistory = ref([])
const isHintCalculating = ref(false)

// Состояние подсказки
const currentHint = ref(null)
const hintMoveCells = ref([])
const hintCarCells = ref([])
const hintArrow = ref('→')

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

// Функции для работы с подсказками
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

// Основные функции игры
const getCarColor = (carId) => {
  if (carId === 1) return "#ff6b6b"
  return colors[(carId - 2) % colors.length]
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

  const levelData = JSON.parse(JSON.stringify(currentLevels.value[currentLevelIndex.value]))

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

const getCarLength = (carId) => 
  grid.value.flat().filter(cell => cell === carId).length

const getCarDirection = (row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99) return null

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

// Функции для работы с перетаскиванием
const startDrag = (event, row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99 || isDragging) return

  // Скрываем подсказку, если начали перемещать машину
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

const endDrag = () => {
  if (!isDragging) return
  document.querySelectorAll('.cell.active').forEach(el => el.classList.remove('active'))
  isDragging = false
  selectedCar.value = null
}

// Алгоритм A* для подсказок
const parseGrid = (grid) => {
  const cars = []
  const rows = grid.length
  const cols = grid[0].length - 1
  const carIds = new Set()

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const cell = grid[row][col]
      if (cell !== 0 && cell !== 99) {
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
      const canMoveRight = positions[0].col < cols - 1 && grid[positions[0].row][positions[0].col + 1] === 0
      const canMoveLeft = positions[0].col > 0 && grid[positions[0].row][positions[0].col - 1] === 0
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
    if (grid[2][col] !== 0 && grid[2][col] !== 99) {
      blocking++
    }
  }

  return blocking
}

const getPossibleMoves = (grid, cars) => {
  const moves = []
  cars.forEach((car, i) => {
    if (car.orientation === 'h') {
      // Left
      let maxMove = 0
      for (let dist = 1; dist <= car.col; dist++) {
        if (grid[car.row][car.col - dist] === 0) {
          maxMove = dist
        } else {
          break
        }
      }
      if (maxMove > 0) moves.push([i, 'left', maxMove])

      // Right
      maxMove = 0
      if (car.id === 1) {
        const maxPossible = 6 - (car.col + car.length)
        for (let dist = 1; dist <= maxPossible; dist++) {
          if (car.col + car.length - 1 + dist < 6) {
            if (grid[car.row][car.col + car.length - 1 + dist] === 0) {
              maxMove = dist
            } else {
              break
            }
          } else if (car.col + car.length - 1 + dist === 6) {
            maxMove = dist
            break
          }
        }
      } else {
        for (let dist = 1; dist <= 6 - (car.col + car.length); dist++) {
          if (grid[car.row][car.col + car.length - 1 + dist] === 0) {
            maxMove = dist
          } else {
            break
          }
        }
      }
      if (maxMove > 0) moves.push([i, 'right', maxMove])
    } else {
      // Up
      let maxMove = 0
      for (let dist = 1; dist <= car.row; dist++) {
        if (grid[car.row - dist][car.col] === 0) {
          maxMove = dist
        } else {
          break
        }
      }
      if (maxMove > 0) moves.push([i, 'up', maxMove])

      // Down
      maxMove = 0
      for (let dist = 1; dist <= 6 - (car.row + car.length); dist++) {
        if (grid[car.row + car.length - 1 + dist][car.col] === 0) {
          maxMove = dist
        } else {
          break
        }
      }
      if (maxMove > 0) moves.push([i, 'down', maxMove])
    }
  })

  return moves
}

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
      
      // Определяем стрелку направления
      switch(direction) {
        case 'left': hintArrow.value = '←'; break
        case 'right': hintArrow.value = '→'; break
        case 'up': hintArrow.value = '↑'; break
        case 'down': hintArrow.value = '↓'; break
      }
      
      // Клетки машины
      hintCarCells.value = []
      for (let i = 0; i < car.length; i++) {
        if (car.orientation === 'h') {
          hintCarCells.value.push({ row: car.row, col: car.col + i })
        } else {
          hintCarCells.value.push({ row: car.row + i, col: car.col })
        }
      }
      
      // Клетки назначения
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
      
      // Не устанавливаем таймер автоматического скрытия
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