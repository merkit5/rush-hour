import heapq
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_level_string_to_grid(level_str):
    """Конвертирует строку уровня в числовую сетку"""
    grid = [[0 for _ in range(7)] for _ in range(6)]  # 6x6 поле + выход в 7-м столбце
    char_to_id = {'A': 1}  # Красная машина всегда имеет id 1
    next_id = 2
    
    for i, char in enumerate(level_str):
        row = i // 6
        col = i % 6
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
    grid[2][6] = 99
    return grid

def parse_grid(grid):
    """Анализирует сетку и возвращает список машин"""
    cars = []
    rows, cols = 6, 6  # Поле строго 6x6
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

        if positions[0][0] == positions[1][0]:
            orientation = 'h'
            length = max(col for (row, col) in positions) - positions[0][1] + 1
        else:
            orientation = 'v'
            length = max(row for (row, col) in positions) - positions[0][0] + 1

        cars.append({
            'id': car_id,
            'orientation': orientation,
            'length': length,
            'row': positions[0][0],
            'col': positions[0][1]
        })

    return cars

def is_goal_state(cars):
    """Проверяет, достигнуто ли целевое состояние"""
    for car in cars:
        if car['id'] == 1:  # Красная машина
            return car['orientation'] == 'h' and car['row'] == 2 and car['col'] + car['length'] == 6
    return False

def get_possible_moves(grid, cars):
    """Генерирует все возможные ходы"""
    moves = []
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
            for dist in range(1, 7 - (col + length) + 1):
                end_col = col + length - 1 + dist
                if end_col == 6:
                    if car['id'] == 1 and grid[row][5] == 0:  # 6 — выход
                        moves.append((i, 'right', dist))
                    break
                if end_col < 6 and grid[row][end_col] == 0:
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
            for dist in range(1, 6 - (row + length) + 1):
                if grid[row + length - 1 + dist][col] == 0:
                    moves.append((i, 'down', dist))
                else:
                    break
    return moves

def apply_move(grid, cars, move):
    """Применяет ход и возвращает новое состояние"""
    car_idx, direction, distance = move
    car = cars[car_idx]
    new_grid = [row[:6] for row in grid[:6]]
    new_grid = [row.copy() for row in new_grid]
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
            if col < 6:
                new_grid[new_cars[car_idx]['row']][col] = car['id']
        else:
            new_grid[new_cars[car_idx]['row'] + i][new_cars[car_idx]['col']] = car['id']

    return new_grid, new_cars

def dijkstra(level_str):
    """Решает уровень Rush Hour с использованием алгоритма Дейкстры"""
    initial_grid = convert_level_string_to_grid(level_str)
    initial_cars = parse_grid(initial_grid)
    
    start_state = (tuple(tuple(row[:6]) for row in initial_grid), [])
    queue = [(0, start_state)]
    visited = set()

    while queue:
        cost, (grid_state, path) = heapq.heappop(queue)
        if grid_state in visited:
            continue
        visited.add(grid_state)

        grid = [list(row) + [initial_grid[i][6]] for i, row in enumerate(grid_state)]
        cars = parse_grid(grid)
        if is_goal_state(cars):
            return path

        for move in get_possible_moves(grid, cars):
            new_grid, new_cars = apply_move(grid, cars, move)
            new_state = tuple(tuple(row[:6]) for row in new_grid)
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

# Примеры использования
if __name__ == "__main__":
    # Простой уровень
    test_level("BBBooCIoDDoCIoAAoCFoXVNNFoXVooFMMQQQ")