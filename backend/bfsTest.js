import { performance } from 'perf_hooks';

class Node {
  constructor(grid, moves = 0, parent = null, moveDescription = '') {
    this.grid = JSON.parse(JSON.stringify(grid));
    this.moves = moves;
    this.parent = parent;
    this.moveDescription = moveDescription;
  }

  isGoal() {
    // Красная машина (1) должна быть на выходе (99)
    return this.grid[2][5] === 1 && this.grid[2][6] === 99;
  }

  getCarInfo() {
    const cars = {};
    for (let row = 0; row < this.grid.length; row++) {
      for (let col = 0; col < this.grid[row].length; col++) {
        const carId = this.grid[row][col];
        if (carId > 0 && carId !== 99 && !cars[carId]) {
          let direction = null;
          let length = 1;

          // Проверяем горизонтальное направление
          if (col + 1 < this.grid[row].length && this.grid[row][col + 1] === carId) {
            direction = 'horizontal';
            while (col + length < this.grid[row].length && this.grid[row][col + length] === carId) {
              length++;
            }
          }
          // Проверяем вертикальное направление
          else if (row + 1 < this.grid.length && this.grid[row + 1][col] === carId) {
            direction = 'vertical';
            while (row + length < this.grid.length && this.grid[row + length][col] === carId) {
              length++;
            }
          }

          if (direction) {
            cars[carId] = { row, col, direction, length };
          }
        }
      }
    }
    return cars;
  }

  getNeighbors() {
    const neighbors = [];
    const cars = this.getCarInfo();

    for (const [carId, car] of Object.entries(cars)) {
      const { row, col, direction, length } = car;
      const id = parseInt(carId);

      if (direction === 'horizontal') {
        // Движение влево
        if (col > 0 && this.grid[row][col - 1] === 0) {
          const newGrid = this.moveCar(id, row, col, 'left', length);
          if (newGrid) {
            neighbors.push(new Node(newGrid, this.moves + 1, this, `Move car ${id} left`));
          }
        }
        // Движение вправо (особый случай для красной машины)
        if (col + length < this.grid[0].length &&
            (this.grid[row][col + length] === 0 ||
             (id === 1 && row === 2 && col + length === 5 && this.grid[row][col + length + 1] === 99))) {
          const newGrid = this.moveCar(id, row, col, 'right', length);
          if (newGrid) {
            neighbors.push(new Node(newGrid, this.moves + 1, this, `Move car ${id} right`));
          }
        }
      } else { // vertical
        // Движение вверх
        if (row > 0 && this.grid[row - 1][col] === 0) {
          const newGrid = this.moveCar(id, row, col, 'up', length);
          if (newGrid) {
            neighbors.push(new Node(newGrid, this.moves + 1, this, `Move car ${id} up`));
          }
        }
        // Движение вниз
        if (row + length < this.grid.length && this.grid[row + length][col] === 0) {
          const newGrid = this.moveCar(id, row, col, 'down', length);
          if (newGrid) {
            neighbors.push(new Node(newGrid, this.moves + 1, this, `Move car ${id} down`));
          }
        }
      }
    }

    return neighbors;
  }

  moveCar(carId, row, col, direction, length) {
    const newGrid = JSON.parse(JSON.stringify(this.grid));

    if (direction === 'left') {
      for (let i = 0; i < length; i++) {
        newGrid[row][col - 1 + i] = carId;
        newGrid[row][col + length - 1 - i] = 0;
      }
    } else if (direction === 'right') {
      // Особый случай для красной машины на выходе
      if (carId === 1 && row === 2 && col + length === 5 && newGrid[row][col + length + 1] === 99) {
        for (let i = 0; i < length; i++) {
          newGrid[row][col + length - i] = carId;
          newGrid[row][col + i] = 0;
        }
      } else if (newGrid[row][col + length] === 0) {
        for (let i = 0; i < length; i++) {
          newGrid[row][col + length - i] = carId;
          newGrid[row][col + i] = 0;
        }
      } else {
        return null;
      }
    } else if (direction === 'up') {
      for (let i = 0; i < length; i++) {
        newGrid[row - 1 + i][col] = carId;
        newGrid[row + length - 1 - i][col] = 0;
      }
    } else if (direction === 'down') {
      for (let i = 0; i < length; i++) {
        newGrid[row + length - i][col] = carId;
        newGrid[row + i][col] = 0;
      }
    }

    // Проверка целостности машины
    let carCells = 0;
    for (let r = 0; r < newGrid.length; r++) {
      for (let c = 0; c < newGrid[r].length; c++) {
        if (newGrid[r][c] === carId) carCells++;
      }
    }
    if (carCells !== length) return null;

    return newGrid;
  }
}

function bfs(initialGrid, maxSteps = 50000) {
  const startNode = new Node(initialGrid);
  const queue = [startNode];
  const visited = new Set();
  visited.add(JSON.stringify(startNode.grid));

  let steps = 0;

  while (queue.length > 0 && steps < maxSteps) {
    steps++;
    const currentNode = queue.shift();

    if (currentNode.isGoal()) {
      console.log(`Total steps processed: ${steps}`);
      return currentNode;
    }

    const neighbors = currentNode.getNeighbors();
    for (const neighbor of neighbors) {
      const neighborStr = JSON.stringify(neighbor.grid);
      if (!visited.has(neighborStr)) {
        visited.add(neighborStr);
        queue.push(neighbor);
      }
    }
  }

  console.log(`Stopped after ${steps} steps without finding solution`);
  return null;
}

function printSolutionPath(node) {
  const path = [];
  let currentNode = node;

  while (currentNode !== null) {
    path.unshift(currentNode);
    currentNode = currentNode.parent;
  }

  console.log('\nSolution path:');
  path.forEach((node, index) => {
    if (index === 0) {
      console.log('Initial state:');
    } else {
      console.log(`Step ${index}: ${node.moveDescription}`);
    }

    console.log('+---------------------+');
    node.grid.forEach(row => {
      console.log('| ' + row.map(cell => {
        if (cell === 0) return ' ';
        if (cell === 99) return 'E';
        return cell.toString().padEnd(2);
      }).join(' ') + ' |');
    });
    console.log('+---------------------+\n');
  });
}

function testBFS(initialGrid) {
  console.log('Starting BFS solver...');
  const startTime = performance.now();
  const startMemory = process.memoryUsage().heapUsed;

  const solution = bfs(initialGrid);

  const endTime = performance.now();
  const endMemory = process.memoryUsage().heapUsed;

  console.log(`\nTime taken: ${(endTime - startTime).toFixed(2)} ms`);
  console.log(`Memory used: ${((endMemory - startMemory) / (1024 * 1024)).toFixed(2)} MB`);

  if (solution) {
    console.log(`\nSolution found in ${solution.moves} moves!`);
    printSolutionPath(solution);
  } else {
    console.log('\nNo solution found for this level.');
  }
}

// Тестовый уровень (красная машина может выйти за 1 ход)
const initialGrid = [
  [2, 2, 2, 0, 0, 3, 0],
  [5, 0, 4, 4, 0, 3, 0],
  [5, 0, 1, 1, 0, 3, 99],  // Красная машина (1) может сдвинуться вправо на выход
  [6, 0, 9, 10, 11, 11, 0],
  [6, 0, 9, 10, 0, 0, 0],
  [6, 7, 7, 8, 8, 8, 0]
];

testBFS(initialGrid);
