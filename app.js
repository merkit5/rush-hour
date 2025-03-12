const { createApp, ref, computed, onMounted, onUnmounted } = Vue;

createApp({
    setup() {
        const grid = ref([
            [0, 0, 0, 2, 0, 0], 
            [0, 0, 0, 2, 0, 0],
            [0, 1, 1, 0, 0, 0], 
            [0, 0, 0, 0, 0, 0],
            [0, 0, 3, 3, 0, 0], 
            [0, 0, 0, 0, 0, 0]
        ]);

        const selectedCar = ref(null);
        let isDragging = false;
        let dragStartPosition = { x: 0, y: 0 };

        const isWin = computed(() => grid.value[2][5] === 1);

        const isExit = (row, col) => {
            return row === 2 && col === 5; 
        };

        const findCarCells = (row, col) => {
            const carId = grid.value[row][col];
            if (carId === 0) return [];

            const cells = [];
            for (let i = 0; i < grid.value.length; i++) {
                for (let j = 0; j < grid.value[i].length; j++) {
                    if (grid.value[i][j] === carId) {
                        cells.push({ row: i, col: j });
                    }
                }
            }
            return cells;
        };

        const getCarDirection = (row, col) => {
            const carId = grid.value[row][col];
            if (carId === 0) return null;

            if (col + 1 < grid.value[0].length && grid.value[row][col + 1] === carId) {
                return 'horizontal';
            }
            if (row + 1 < grid.value.length && grid.value[row + 1][col] === carId) {
                return 'vertical';
            }
            return null;
        };

        const canMove = (row, col, direction, carId, carDirection) => {
            if (carDirection === 'horizontal') {
                if (direction === 'left') {
                    return col > 0 && grid.value[row][col - 1] === 0;
                } else if (direction === 'right') {
                    return col + 2 < grid.value[0].length && grid.value[row][col + 2] === 0;
                }
            } else if (carDirection === 'vertical') {
                if (direction === 'up') {
                    return row > 0 && grid.value[row - 1][col] === 0;
                } else if (direction === 'down') {
                    return row + 2 < grid.value.length && grid.value[row + 2][col] === 0;
                }
            }
            return false;
        };

        const selectCar = (row, col) => {
            const carId = grid.value[row][col];
            if (carId !== 0) {
                const cells = findCarCells(row, col);
                if (cells.length > 0) {
                    selectedCar.value = {
                        cells,
                        id: carId,
                        direction: getCarDirection(row, col)
                    };
                }
            }
        };

        const moveCar = (direction) => {
            if (!selectedCar.value) return;
        
            const { cells, id, direction: carDirection } = selectedCar.value;
            console.log("Пытаемся передвинуть:", id, "в направлении", direction);
        
            const firstCell = cells[0];
        
            if (canMove(firstCell.row, firstCell.col, direction, id, carDirection)) {
                console.log("Двигаем машину:", id, direction);
        
                cells.forEach(cell => {
                    grid.value[cell.row][cell.col] = 0;
                });
        
                const newCells = cells.map(cell => {
                    let newRow = cell.row;
                    let newCol = cell.col;
        
                    if (direction === 'up') newRow--;
                    if (direction === 'down') newRow++;
                    if (direction === 'left') newCol--;
                    if (direction === 'right') newCol++;
        
                    return { row: newRow, col: newCol };
                });
        
                newCells.forEach(cell => {
                    grid.value[cell.row][cell.col] = id;
                });
        
                selectedCar.value.cells = newCells;
                console.log("Обновленные клетки машины:", selectedCar.value.cells);
            } else {
                console.log("Нельзя двигаться в этом направлении!");
            }
        };
        
        const startDrag = (event, row, col) => {
            if (event.buttons !== 1) return;
        
            console.log("Попытка выбрать машину:", row, col);
        
            isDragging = false;
            selectedCar.value = null;
        
            const carCells = findCarCells(row, col);
        
            if (carCells.length > 0) {
                console.log("Машина найдена, выбираем:", carCells);
                selectCar(carCells[0].row, carCells[0].col);
                isDragging = true;
                dragStartPosition = { x: event.clientX, y: event.clientY };
            } else {
                console.log("Машина не найдена!");
            }
        };
        
        const dragOver = (event) => {
            if (isDragging && selectedCar.value && event.buttons === 1) {
                console.log("Двигаем машину:", selectedCar.value);
        
                const { direction } = selectedCar.value;
                const deltaX = event.clientX - dragStartPosition.x;
                const deltaY = event.clientY - dragStartPosition.y;
        
                if (direction === 'horizontal') {
                    if (deltaX < -50) {
                        moveCar('left');
                        dragStartPosition.x = event.clientX;
                    } else if (deltaX > 50) {
                        moveCar('right');
                        dragStartPosition.x = event.clientX;
                    }
                } else if (direction === 'vertical') {
                    if (deltaY < -50) {
                        moveCar('up');
                        dragStartPosition.y = event.clientY;
                    } else if (deltaY > 50) {
                        moveCar('down');
                        dragStartPosition.y = event.clientY;
                    }
                }
            }
        };
        
        const endDrag = () => {
            if (isDragging) {
                console.log("Отпустили мышь, сохраняем новое положение машины и сбрасываем параметры захвата");
                isDragging = false;
                selectedCar.value = null; // Сбрасываем выбранную машину
                dragStartPosition = { x: 0, y: 0 };
            }
        };
        
        onMounted(() => {
            document.addEventListener("mouseup", endDrag);
        });
        
        onUnmounted(() => {
            document.removeEventListener("mouseup", endDrag);
        });
        
        return {
            grid,
            selectedCar,
            isWin,
            isExit,
            selectCar,
            moveCar,
            startDrag,
            dragOver,
            
            endDrag
        };
    }
}).mount('#app');