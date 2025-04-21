<template>
  <div>
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

    <div v-if="isWin" class="modal-overlay">
      <div class="modal">
        <h2>Поздравляем! 🎉</h2>
        <p>Вы выиграли!</p>
        <button @click="restartGame">Начать заново</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const initialGrid = () => [
  [0, 0, 0, 4, 4, 4, 0],
  [0, 0, 0, 2, 0, 0, 0],
  [0, 1, 1, 2, 3, 0, 99],
  [0, 0, 0, 0, 3, 0, 0],
  [0, 0, 0, 0, 5, 5, 0],
  [0, 0, 0, 0, 0, 0, 0]
]

const grid = ref(initialGrid())

const colors = [
  "#4ecdc4", "#ffe66d", "#ff9f43", "#54a0ff",
  "#5f27cd", "#10ac84", "#f368e0", "#222f3e", "#01a3a4",
  "#ffcc29", "#ff4757", "#2ed573", "#3742fa", "#8c7ae6",
  "#e84118", "#44bd32", "#40739e", "#b71540", "#6D214F",
  "#D980FA", "#ED4C67", "#A3CB38", "#1289A7"
]

const getCarColor = (carId) => {
  if (carId === 1) return "#ff6b6b"
  return colors[(carId - 2) % colors.length]
}

const selectedCar = ref(null)
let isDragging = false
let dragStartPosition = { x: 0, y: 0 }

const isWin = computed(() => grid.value[2][6] === 1)

const getCarLength = (carId) =>
  grid.value.flat().filter(cell => cell === carId).length

const findCarCells = (row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99) return []
  return grid.value.flatMap((r, i) =>
    r.map((c, j) => (c === carId ? { row: i, col: j } : null))
  ).filter(Boolean)
}

const getCarDirection = (row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99) return null
  if (col + 1 < grid.value[0].length && grid.value[row][col + 1] === carId) return 'horizontal'
  if (row + 1 < grid.value.length && grid.value[row + 1][col] === carId) return 'vertical'
  return null
}

const canMove = (row, col, direction, carDirection) => {
  const carId = grid.value[row][col];
  const carLength = getCarLength(carId);

  if (carDirection === 'horizontal') {
    if (direction === 'left') {
      // Запрещаем движение влево из 7-го столбца (кроме красной машины)
      if (col === 6 && carId !== 1) return false;
      return col > 0 && grid.value[row][col - 1] === 0;
    }
    if (direction === 'right') {
      const rightEdge = col + carLength - 1;

      // Красная машина может заехать только в [2][6]
      if (rightEdge + 1 === 6 && carId === 1 && row === 2) {
        return grid.value[2][6] === 99; // Проверяем, что это выход
      }

      // Блокируем всем машинам (кроме красной) подход к 7-му столбцу
      if (rightEdge + 1 >= 6 && carId !== 1) return false;

      // Стандартная проверка для других случаев
      if (rightEdge + 1 >= 7) return false;
      return grid.value[row][rightEdge + 1] === 0;
    }
  } else if (carDirection === 'vertical') {
    // Полностью блокируем вертикальное движение в 7-м столбце
    if (col === 6) return false;

    if (direction === 'up') {
      return row > 0 && grid.value[row - 1][col] === 0;
    }
    if (direction === 'down') {
      const bottomEdge = row + carLength - 1;
      return bottomEdge + 1 < grid.value.length && grid.value[bottomEdge + 1][col] === 0;
    }
  }
  return false;
};

const moveCar = (direction) => {
  if (!selectedCar.value) return;

  const { cells, id, direction: carDirection } = selectedCar.value;
  const firstCell = cells[0];
  const lastCell = cells[cells.length - 1];

  // Дополнительная проверка для 7-го столбца
  if (direction === 'right' && lastCell.col === 5 && id !== 1) {
    // Не даем другим машинам подъезжать вплотную к выходу
    return;
  }

  if (canMove(firstCell.row, firstCell.col, direction, carDirection)) {
    cells.forEach(cell => grid.value[cell.row][cell.col] = 0);
    const newCells = cells.map(cell => {
      let newRow = cell.row, newCol = cell.col;
      if (direction === 'up') newRow--;
      if (direction === 'down') newRow++;
      if (direction === 'left') newCol--;
      if (direction === 'right') newCol++;
      return { row: newRow, col: newCol };
    });
    newCells.forEach(cell => grid.value[cell.row][cell.col] = id);
    selectedCar.value.cells = newCells;
  }
};

const startDrag = (event, row, col) => {
  const carId = grid.value[row][col]
  if (carId === 0 || carId === 99 || isDragging) return
  
  isDragging = true
  dragStartPosition = { x: event.clientX, y: event.clientY }
  
  // Находим все клетки, принадлежащие этой машине
  const carCells = []
  grid.value.forEach((r, i) => {
    r.forEach((c, j) => {
      if (c === carId) {
        carCells.push({ row: i, col: j })
      }
    })
  })

  if (carCells.length > 0) {
    selectedCar.value = {
      cells: carCells,
      id: carId,
      direction: getCarDirection(row, col)
    }
    
    // Добавляем класс active всем клеткам машины
    carCells.forEach(cell => {
      const cellElement = document.querySelector(`.row:nth-child(${cell.row + 1}) .cell:nth-child(${cell.col + 1})`)
      cellElement?.classList.add('active')
    })
  }
}

const dragOver = (event) => {
  if (!isDragging || !selectedCar.value) return

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
  
  // Удаляем класс active со всех клеток
  document.querySelectorAll('.cell.active').forEach(el => {
    el.classList.remove('active')
  })
  
  isDragging = false
  selectedCar.value = null
}

const restartGame = () => {
  grid.value = initialGrid()
}

onMounted(() => document.addEventListener('mouseup', endDrag))
onUnmounted(() => document.removeEventListener('mouseup', endDrag))
</script>
