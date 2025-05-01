export function generateSolvableLevel() {
    const HEIGHT = 6, WIDTH = 7;
    const MAX_ID = 20;
    
    const emptyGrid = () => Array.from({ length: HEIGHT }, () => Array(WIDTH).fill(0));
    const grid = emptyGrid();
  
    // 1. Сначала размещаем выход и красную машину ДАЛЕКО от выхода
    grid[2][6] = 99; // Выход
    
    // Размещаем красную машину (ID=1) в случайной позиции слева (но не слишком близко к выходу)
    let redCarCol;
    do {
      redCarCol = Math.floor(Math.random() * 3); // 0, 1 или 2 (чтобы было минимум 3 шага до выхода)
    } while (redCarCol < 0); // Дополнительные проверки при необходимости
    
    grid[2][redCarCol] = 1;
    grid[2][redCarCol + 1] = 1;
  
    const cars = [
      { id: 1, row: 2, col: redCarCol, len: 2, dir: 'horizontal' }
    ];
  
    let nextId = 2;
  
    // 2. Размещаем случайные машины (больше вертикальных для сложности)
    for (let i = 0; i < 10; i++) {
      const preferVertical = Math.random() > 0.6; // 40% вертикальных машин
      const car = placeRandomCar(grid, nextId++, preferVertical);
      if (car) cars.push(car);
    }
  
    // 3. "Перемешиваем" уровень, делая обратные ходы
    let steps = 0;
    const minSteps = 15 + Math.floor(Math.random() * 10); // 15-25 шагов
    const maxSteps = 50;
    
    while (steps < minSteps && steps < maxSteps) {
      const movableCars = cars.filter(car => canMove(grid, car, 'backward'));
      if (movableCars.length === 0) break;
  
      const car = movableCars[Math.floor(Math.random() * movableCars.length)];
      moveCar(grid, car, 'backward');
      steps++;
    }
  
    // 4. Дополнительная проверка сложности
    if (isTooEasy(grid, redCarCol)) {
      return generateSolvableLevel(); // Рекурсивно генерируем заново
    }
  
    return grid;
  }
  
  // Помощник для размещения машин с предпочтением направления
  function placeRandomCar(grid, id, preferVertical = false) {
    const HEIGHT = grid.length, WIDTH = grid[0].length;
    const dir = preferVertical || Math.random() < 0.4 ? 'vertical' : 'horizontal';
    const len = Math.random() < 0.7 ? 2 : 3;
  
    for (let attempts = 0; attempts < 100; attempts++) {
      const row = Math.floor(Math.random() * HEIGHT);
      const col = Math.floor(Math.random() * WIDTH);
  
      // Не размещаем машины в ряду красной машины (усложняем)
      if (row === 2 && dir === 'horizontal') continue;
  
      const positions = [];
      for (let i = 0; i < len; i++) {
        const r = dir === 'vertical' ? row + i : row;
        const c = dir === 'horizontal' ? col + i : col;
        if (r >= HEIGHT || c >= WIDTH || grid[r][c] !== 0) {
          break;
        }
        positions.push({ r, c });
      }
  
      if (positions.length === len) {
        positions.forEach(p => grid[p.r][p.c] = id);
        return { id, row, col, len, dir };
      }
    }
  
    return null;
  }
  
  // Проверка, что уровень не слишком простой
  function isTooEasy(grid, redCarCol) {
    // Если красная машина ближе чем 3 клетки к выходу
    if (redCarCol >= 3) return true;
    
    // Проверяем, нет ли свободного пути для красной машины
    let hasClearPath = true;
    for (let c = redCarCol + 2; c < 6; c++) {
      if (grid[2][c] !== 0) {
        hasClearPath = false;
        break;
      }
    }
    
    return hasClearPath;
  }
  
  function canMove(grid, car, mode) {
    const dr = car.dir === 'vertical' ? (mode === 'backward' ? -1 : 1) : 0;
    const dc = car.dir === 'horizontal' ? (mode === 'backward' ? -1 : 1) : 0;
  
    const { row, col, len } = car;
    const checkR = row + (dr < 0 ? -1 : dr * len);
    const checkC = col + (dc < 0 ? -1 : dc * len);
  
    if (
      checkR < 0 || checkR >= grid.length ||
      checkC < 0 || checkC >= grid[0].length
    ) return false;
  
    return grid[checkR]?.[checkC] === 0;
  }
  
  function moveCar(grid, car, mode) {
    const dr = car.dir === 'vertical' ? (mode === 'backward' ? -1 : 1) : 0;
    const dc = car.dir === 'horizontal' ? (mode === 'backward' ? -1 : 1) : 0;
  
    const cells = [];
    for (let i = 0; i < car.len; i++) {
      const r = car.row + (car.dir === 'vertical' ? i : 0);
      const c = car.col + (car.dir === 'horizontal' ? i : 0);
      cells.push({ r, c });
    }
  
    cells.forEach(p => grid[p.r][p.c] = 0);
  
    car.row += dr;
    car.col += dc;
  
    for (let i = 0; i < car.len; i++) {
      const r = car.row + (car.dir === 'vertical' ? i : 0);
      const c = car.col + (car.dir === 'horizontal' ? i : 0);
      grid[r][c] = car.id;
    }
  }
  