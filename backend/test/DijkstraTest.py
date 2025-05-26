import heapq
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_grid_params(level_str):
    """Определяет параметры поля по длине строки уровня"""
    length = len(level_str)
    if length == 25:  # 5x5
        return (5, 5, 2, 5)  # rows, cols, exit_row, exit_col
    elif length == 36:  # 6x6
        return (6, 6, 2, 6)
    elif length == 49:  # 7x7
        return (7, 7, 3, 7)
    else:
        raise ValueError(f"Неподдерживаемый размер поля: длина строки {length}")

def convert_level_string_to_grid(level_str):
    """Конвертирует строку уровня в числовую сетку"""
    rows, cols, exit_row, exit_col = get_grid_params(level_str)
    grid = [[0 for _ in range(cols + 1)] for _ in range(rows)]  # +1 для выхода
    char_to_id = {'A': 1}  # Красная машина всегда имеет id 1
    next_id = 2
    
    for i, char in enumerate(level_str):
        row = i // cols
        col = i % cols
        if char == 'o':
            grid[row][col] = 0  # Пустая клетка
        elif char == 'x':
            grid[row][col] = -1  # Стена
        else:
            if char not in char_to_id:
                char_to_id[char] = next_id
                next_id += 1
            grid[row][col] = char_to_id[char]
    
    # Добавляем выход для красной машины
    grid[exit_row][exit_col] = 99
    return grid

def parse_grid(grid):
    """Анализирует сетку и возвращает список машин"""
    cars = []
    rows, cols = len(grid), len(grid[0]) - 1  # Игнорируем последний столбец (выход)
    car_ids = set()

    for row in range(rows):
        for col in range(cols):
            cell = grid[row][col]
            if cell > 0:  # 0 - пусто, -1 - стена, >0 - машины
                car_ids.add(cell)

    for car_id in car_ids:
        positions = [(row, col) 
                    for row in range(rows) 
                    for col in range(cols) 
                    if grid[row][col] == car_id]

        if len(positions) < 2:
            continue

        positions.sort()
        if positions[0][0] == positions[1][0]:
            orientation = 'h'
            length = positions[-1][1] - positions[0][1] + 1
        else:
            orientation = 'v'
            length = positions[-1][0] - positions[0][0] + 1

        cars.append({
            'id': car_id,
            'orientation': orientation,
            'length': length,
            'row': positions[0][0],
            'col': positions[0][1]
        })

    return cars

def is_goal_state(cars, exit_row, exit_col):
    """Проверяет, достигнуто ли целевое состояние"""
    for car in cars:
        if car['id'] == 1:  # Красная машина
            return (car['orientation'] == 'h' and 
                    car['row'] == exit_row and 
                    car['col'] + car['length'] == exit_col)
    return False

def get_possible_moves(grid, cars):
    """Генерирует все возможные ходы"""
    moves = []
    rows, cols = len(grid), len(grid[0]) - 1
    
    for i, car in enumerate(cars):
        row, col, length = car['row'], car['col'], car['length']
        
        if car['orientation'] == 'h':
            # Движение влево
            for dist in range(1, col + 1):
                if grid[row][col - dist] == 0:
                    moves.append((i, 'left', dist))
                else:
                    break
            
            # Движение вправо
            for dist in range(1, cols + 1 - (col + length)):
                end_col = col + length - 1 + dist
                if end_col == cols and car['id'] == 1:  # Выход для красной машины
                    moves.append((i, 'right', dist))
                    break
                if end_col < cols and grid[row][end_col] == 0:
                    moves.append((i, 'right', dist))
                else:
                    break
        else:
            # Движение вверх
            for dist in range(1, row + 1):
                if grid[row - dist][col] == 0:
                    moves.append((i, 'up', dist))
                else:
                    break
            
            # Движение вниз
            for dist in range(1, rows - (row + length) + 1):
                if grid[row + length - 1 + dist][col] == 0:
                    moves.append((i, 'down', dist))
                else:
                    break
    return moves

def apply_move(grid, cars, move):
    """Применяет ход и возвращает новое состояние"""
    car_idx, direction, distance = move
    car = cars[car_idx]
    rows, cols = len(grid), len(grid[0]) - 1
    new_grid = [row.copy() for row in grid]
    new_cars = [c.copy() for c in cars]

    # Очистить старую позицию
    for i in range(car['length']):
        if car['orientation'] == 'h':
            new_grid[car['row']][car['col'] + i] = 0
        else:
            new_grid[car['row'] + i][car['col']] = 0

    # Обновить координаты
    if direction == 'left':
        new_cars[car_idx]['col'] -= distance
    elif direction == 'right':
        new_cars[car_idx]['col'] += distance
    elif direction == 'up':
        new_cars[car_idx]['row'] -= distance
    elif direction == 'down':
        new_cars[car_idx]['row'] += distance

    # Заполнить новую позицию
    for i in range(new_cars[car_idx]['length']):
        if new_cars[car_idx]['orientation'] == 'h':
            col = new_cars[car_idx]['col'] + i
            if col < cols:  # Не записываем в столбец выхода
                new_grid[new_cars[car_idx]['row']][col] = car['id']
        else:
            new_grid[new_cars[car_idx]['row'] + i][new_cars[car_idx]['col']] = car['id']

    return new_grid, new_cars

def dijkstra(level_str):
    """Решает уровень Rush Hour с использованием алгоритма Дейкстры"""
    initial_grid = convert_level_string_to_grid(level_str)
    initial_cars = parse_grid(initial_grid)
    rows, cols, exit_row, exit_col = get_grid_params(level_str)
    
    start_state = (tuple(tuple(row[:cols]) for row in initial_grid), [])
    queue = [(0, start_state)]
    visited = set()

    while queue:
        cost, (grid_state, path) = heapq.heappop(queue)
        if grid_state in visited:
            continue
        visited.add(grid_state)

        grid = [list(row) + [initial_grid[i][cols]] for i, row in enumerate(grid_state)]
        cars = parse_grid(grid)
        if is_goal_state(cars, exit_row, exit_col):
            return path

        for move in get_possible_moves(grid, cars):
            new_grid, new_cars = apply_move(grid, cars, move)
            new_state = tuple(tuple(row[:cols]) for row in new_grid)
            if new_state not in visited:
                heapq.heappush(queue, (cost + 1, (new_state, path + [move])))

    return None

def print_solution(solution, level_str):
    """Выводит решение в удобном формате"""
    if not solution:
        print("Решение не найдено.")
        return

    grid = convert_level_string_to_grid(level_str)
    cars = parse_grid(grid)
    car_ids = {i: car['id'] for i, car in enumerate(cars)}
    
    print(f"Dijkstra нашёл решение за {len(solution)} шагов:")
    for step, (car_idx, direction, distance) in enumerate(solution, 1):
        print(f"Шаг {step}: Машина {car_ids[car_idx]} → {direction} на {distance}")

def test_level(level_str):
    """Тестирует решение для одного уровня"""
    print(f"\nТестируем уровень: {level_str}")
    
    tracemalloc.start()
    start_time = time.time()
    
    solution = dijkstra(level_str)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print_solution(solution, level_str)
    print(f"Время выполнения: {end_time - start_time:.4f} сек")
    print(f"Пиковая память: {peak / 1024:.2f} KB")

# Примеры использования для разных размеров
if __name__ == "__main__":
    
    # 7x7 уровень
    test_level("QUoMMooQUDDooGBBPoHIGAAPoHIEoKCCJxExKRRJoExoFFJoo")