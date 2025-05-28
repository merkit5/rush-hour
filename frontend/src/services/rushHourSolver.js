// src/services/rushHourSolver.js

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

export const parseGrid = (grid, width) => {
  const cars = [];
  const rows = grid.length;
  const cols = width;
  const carIds = new Set();

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const cell = grid[row][col];
      if (cell > 0 && cell !== 99) {
        carIds.add(cell);
      }
    }
  }

  carIds.forEach(carId => {
    const positions = [];
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        if (grid[row][col] === carId) {
          positions.push({ row, col });
        }
      }
    }

    if (positions.length === 0) return;

    positions.sort((a, b) => a.row === b.row ? a.col - b.col : a.row - b.row);

    let orientation, length;
    if (positions.length > 1) {
      orientation = positions[0].row === positions[1].row ? 'h' : 'v';
    } else {
      const canMoveRight = positions[0].col < cols - 1 && grid[positions[0].row][positions[0].col + 1] <= 0;
      const canMoveLeft = positions[0].col > 0 && grid[positions[0].row][positions[0].col - 1] <= 0;
      orientation = canMoveRight || canMoveLeft ? 'h' : 'v';
    }

    if (orientation === 'h') {
      length = positions[positions.length - 1].col - positions[0].col + 1;
    } else {
      length = positions[positions.length - 1].row - positions[0].row + 1;
    }

    cars.push({
      id: carId,
      orientation,
      length,
      row: positions[0].row,
      col: positions[0].col
    });
  });

  return cars;
};

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

const gridToKey = (grid, width) => {
  return grid.map(row => row.slice(0, width).join(',')).join('|');
};

export const solveRushHourAStar = (initialGrid, width, height, exitRow) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      try {
        const initialCars = parseGrid(initialGrid, width);
        const exitCol = width;
        
        if (isGoalState(initialCars, exitRow, exitCol)) {
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
        const initialStateKey = gridToKey(initialGrid, width);
        visited.set(initialStateKey, 0);

        while (!openSet.isEmpty()) {
          const current = openSet.pop();
          
          if (isGoalState(current.cars, exitRow, exitCol)) {
            resolve(current.path);
            return;
          }

          const moves = getPossibleMoves(current.grid, current.cars, width, height, exitRow);
          for (const move of moves) {
            const [newGrid, newCars] = applyMove(current.grid, current.cars, move, width, height);
            const newKey = gridToKey(newGrid, width);
            
            const newG = current.gScore + 1;
            
            if (!visited.has(newKey) || newG < visited.get(newKey)) {
              visited.set(newKey, newG);
              
              const h = heuristic(newGrid, newCars, exitRow, exitCol);
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