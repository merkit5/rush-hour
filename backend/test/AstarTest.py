from collections import deque
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
    rows, cols = len(grid), len(grid[0]) - 1  # Игнорируем последний столбец (выход)
    car_ids = set()

    for row in range(rows):
        for col in range(cols):
            cell = grid[row][col]
            if cell > 0:  # 0 - пусто, -1 - стена, >0 - машины
                car_ids.add(cell)

    for car_id in car_ids:
        positions = []
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] == car_id:
                    positions.append((row, col))

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

def heuristic(grid, cars):
    """Эвристика для A*: количество машин, блокирующих путь красной машины"""
    blocking = 0
    red_car = next(car for car in cars if car['id'] == 1)

    if red_car['orientation'] != 'h' or red_car['row'] != 2:
        return float('inf')

    exit_col = red_car['col'] + red_car['length']
    for col in range(exit_col, 6):
        if grid[2][col] != 0 and grid[2][col] != 99:
            blocking += 1

    return blocking * 3  # Увеличиваем вес для более точной эвристики

def get_possible_moves(grid, cars):
    """Генерирует все возможные ходы"""
    moves = []
    for i, car in enumerate(cars):
        if car['orientation'] == 'h':
            # Движение влево
            max_move = 0
            for dist in range(1, car['col'] + 1):
                if grid[car['row']][car['col'] - dist] == 0:
                    max_move = dist
                else:
                    break
            if max_move > 0:
                moves.append((i, 'left', max_move))

            # Движение вправо
            max_move = 0
            if car['id'] == 1:  # Особый случай для красной машины
                max_possible = 6 - (car['col'] + car['length'])
                for dist in range(1, max_possible + 1):
                    if car['col'] + car['length'] - 1 + dist < 6:
                        if grid[car['row']][car['col'] + car['length'] - 1 + dist] == 0:
                            max_move = dist
                        else:
                            break
                    elif car['col'] + car['length'] - 1 + dist == 6:  # Выход
                        max_move = dist
                        break
            else:
                for dist in range(1, 6 - (car['col'] + car['length']) + 1):
                    if grid[car['row']][car['col'] + car['length'] - 1 + dist] == 0:
                        max_move = dist
                    else:
                        break
            if max_move > 0:
                moves.append((i, 'right', max_move))

        else:  # Вертикальные машины
            # Движение вверх
            max_move = 0
            for dist in range(1, car['row'] + 1):
                if grid[car['row'] - dist][car['col']] == 0:
                    max_move = dist
                else:
                    break
            if max_move > 0:
                moves.append((i, 'up', max_move))

            # Движение вниз
            max_move = 0
            for dist in range(1, 6 - (car['row'] + car['length']) + 1):
                if grid[car['row'] + car['length'] - 1 + dist][car['col']] == 0:
                    max_move = dist
                else:
                    break
            if max_move > 0:
                moves.append((i, 'down', max_move))

    return moves

def apply_move(grid, cars, move):
    """Применяет ход и возвращает новое состояние"""
    car_idx, direction, distance = move
    car = cars[car_idx]
    new_grid = [row.copy() for row in grid]
    new_cars = [c.copy() for c in cars]

    # Очищаем старую позицию
    for i in range(car['length']):
        if car['orientation'] == 'h':
            new_grid[car['row']][car['col'] + i] = 0
        else:
            new_grid[car['row'] + i][car['col']] = 0

    # Обновляем позицию
    if direction == 'left':
        new_cars[car_idx]['col'] -= distance
    elif direction == 'right':
        new_cars[car_idx]['col'] += distance
    elif direction == 'up':
        new_cars[car_idx]['row'] -= distance
    elif direction == 'down':
        new_cars[car_idx]['row'] += distance

    # Заполняем новую позицию
    for i in range(new_cars[car_idx]['length']):
        if new_cars[car_idx]['orientation'] == 'h':
            col = new_cars[car_idx]['col'] + i
            if col < 6:
                new_grid[new_cars[car_idx]['row']][col] = car['id']
        else:
            new_grid[new_cars[car_idx]['row'] + i][new_cars[car_idx]['col']] = car['id']

    return new_grid, new_cars

def solve_rush_hour_astar(level_str):
    """Решает уровень Rush Hour с использованием A*"""
    grid = convert_level_string_to_grid(level_str)
    initial_cars = parse_grid(grid)

    open_set = []
    heapq.heappush(open_set, (0, 0, grid, initial_cars, []))

    visited = set()
    g_scores = {}

    initial_state_key = tuple(tuple(row[:6]) for row in grid)
    g_scores[initial_state_key] = 0

    while open_set:
        _, g_score, current_grid, cars, path = heapq.heappop(open_set)
        current_state_key = tuple(tuple(row[:6]) for row in current_grid)

        if current_state_key in visited:
            continue
        visited.add(current_state_key)

        if is_goal_state(cars):
            return path

        for move in get_possible_moves(current_grid, cars):
            new_grid, new_cars = apply_move(current_grid, cars, move)
            new_state_key = tuple(tuple(row[:6]) for row in new_grid)

            tentative_g_score = g_score + 1

            if new_state_key not in g_scores or tentative_g_score < g_scores[new_state_key]:
                g_scores[new_state_key] = tentative_g_score
                h_score = heuristic(new_grid, new_cars)
                f_score = tentative_g_score + h_score
                heapq.heappush(open_set, (f_score, tentative_g_score, new_grid, new_cars, path + [move]))

    return None

def print_solution(solution, level_str):
    """Выводит решение в удобном формате"""
    if not solution:
        print("Решение не найдено.")
        return

    grid = convert_level_string_to_grid(level_str)
    cars = parse_grid(grid)
    car_ids = {i: car['id'] for i, car in enumerate(cars)}
    
    print(f"Найдено решение за {len(solution)} шагов:")
    for step, (car_idx, direction, distance) in enumerate(solution, 1):
        print(f"Шаг {step}: Машина {car_ids[car_idx]} → {direction} на {distance}")

def test_level(level_str):
    """Тестирует решение для одного уровня"""
    print(f"\nТестируем уровень: {level_str}")
    
    tracemalloc.start()
    start_time = time.time()
    
    solution = solve_rush_hour_astar(level_str)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print_solution(solution, level_str)
    print(f"Время выполнения: {end_time - start_time:.4f} сек")
    print(f"Пиковая память: {peak / 1024:.2f} KB")

# Примеры использования
if __name__ == "__main__":
    # Простой уровень
    test_level("FJoDDDFJoHHHAACMooEoCMoGELBIIGELBKKo")
