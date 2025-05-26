from collections import deque
import heapq
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_grid_size(level_str):
    """Определяет размер поля на основе длины строки уровня"""
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
    rows, cols, exit_row, exit_col = get_grid_size(level_str)
    grid = [[0 for _ in range(cols + 1)] for _ in range(rows)]
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
        positions = []
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] == car_id:
                    positions.append((row, col))

        if len(positions) < 2:
            continue

        # Определяем ориентацию машины
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

def heuristic(grid, cars, exit_row, exit_col):
    """Унифицированная эвристика: количество машин на пути красной машины"""
    red_car = next((car for car in cars if car['id'] == 1), None)
    if not red_car:
        return float('inf')

    # Красная машина должна быть горизонтальной и в правильном ряду
    if red_car['orientation'] != 'h' or red_car['row'] != exit_row:
        return float('inf')

    blocking = 0
    exit_col_red = red_car['col'] + red_car['length']
    
    for col in range(exit_col_red, exit_col):
        if grid[exit_row][col] != 0 and grid[exit_row][col] != 99:
            blocking += 1

    return blocking

def get_possible_moves(grid, cars, width, height, exit_row):
    """Унифицированная генерация ходов"""
    moves = []
    
    for i, car in enumerate(cars):
        if car['orientation'] == 'h':
            # Движение влево
            left_move = 0
            for dist in range(1, car['col'] + 1):
                if grid[car['row']][car['col'] - dist] == 0:
                    left_move = dist
                else:
                    break
            if left_move > 0:
                moves.append((i, 'left', left_move))

            # Движение вправо
            right_move = 0
            for dist in range(1, (width - (car['col'] + car['length'])) + 1):
                new_col = car['col'] + car['length'] - 1 + dist
                if new_col < width:  # Обычная клетка
                    if grid[car['row']][new_col] == 0:
                        right_move = dist
                    else:
                        break
                elif new_col == width and car['id'] == 1:  # Выход для красной
                    right_move = dist
                    break

            if right_move > 0:
                moves.append((i, 'right', right_move))
        else:
            # Движение вверх
            up_move = 0
            for dist in range(1, car['row'] + 1):
                if grid[car['row'] - dist][car['col']] == 0:
                    up_move = dist
                else:
                    break
            if up_move > 0:
                moves.append((i, 'up', up_move))

            # Движение вниз
            down_move = 0
            for dist in range(1, (height - (car['row'] + car['length'])) + 1):
                if grid[car['row'] + car['length'] - 1 + dist][car['col']] == 0:
                    down_move = dist
                else:
                    break
            if down_move > 0:
                moves.append((i, 'down', down_move))

    return moves

def apply_move(grid, cars, move, width, height):
    """Унифицированное применение хода"""
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
            if col < width:
                new_grid[new_cars[car_idx]['row']][col] = car['id']
        else:
            row = new_cars[car_idx]['row'] + i
            new_grid[row][new_cars[car_idx]['col']] = car['id']

    return new_grid, new_cars

def solve_rush_hour_astar(level_str):
    """Решает уровень Rush Hour с использованием A*"""
    grid = convert_level_string_to_grid(level_str)
    initial_cars = parse_grid(grid)
    rows, cols, exit_row, exit_col = get_grid_size(level_str)

    open_set = []
    heapq.heappush(open_set, (0, 0, grid, initial_cars, []))

    visited = set()
    g_scores = {}

    initial_state_key = tuple(tuple(row[:cols]) for row in grid)
    g_scores[initial_state_key] = 0

    while open_set:
        _, g_score, current_grid, cars, path = heapq.heappop(open_set)
        current_state_key = tuple(tuple(row[:cols]) for row in current_grid)

        if current_state_key in visited:
            continue
        visited.add(current_state_key)

        if is_goal_state(cars, exit_row, exit_col):
            return path

        for move in get_possible_moves(current_grid, cars, cols, rows, exit_row):
            new_grid, new_cars = apply_move(current_grid, cars, move, cols, rows)
            new_state_key = tuple(tuple(row[:cols]) for row in new_grid)

            tentative_g_score = g_score + 1

            if new_state_key not in g_scores or tentative_g_score < g_scores[new_state_key]:
                g_scores[new_state_key] = tentative_g_score
                h_score = heuristic(new_grid, new_cars, exit_row, exit_col)
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
    # 5x5 уровень
    test_level("xFFCKoooNNCKBIxoECKBIAAEJoBIDoEJxSODxoJGSODoLLGHH")

    test_level("QUoMMooQUDDooGBBPoHIGAAPoHIEoKCCJxExKRRJoExoFFJoo")

    test_level("ooBooHHxJBCCCMoJoooxMLJAAEGMLTToEGFLKKKEoFoIIIDDF")

    test_level("CCoJJJoNKKEEoBNDRRMPBNDAAMPBLDQxMxFLOQHHIFoOGGoIo")

    test_level("oGPPJJHxGxoKoHFoCCKEHFAASKEoFRISxoLxRIDDxLoBBMMoL")

    test_level("UUOFFFPooOKKoPIIIoQxCJBAAQoCJBoDHHoJoGDEEoxoGDoox")

    test_level("JJJoxooOBGEEINOBGxRINooAARINCCooDxoHoFFDoKHLLoMMK")

    test_level("MLoBBxCMLOxooCMoOFGGGIAAFoooINNNHKEJJJoHKEoDDDHKo")

    test_level("oDJoEQQGDJIEHoGoJIEHBLAAICOBLMKoCOBLMKxCOPoMNNFFP")

    test_level("KKBRRLLDoBIISSDooGGGHoAAoMoHoCCFMJHxNoFMJUoNEEEJU")

    test_level("EEMIIoJooMSSKJHoMGDKJHAAGDKOHPoFFFORPoNLooRBBNLCC")

    test_level("EoIoGBBEoIoGxooJIxGHHKJAAooRKDoLLLRoDoCCCxoFFFMMx")

    test_level("ooIILxxoJGoLOODJGoLCBDJoAACBDKKoEoFMQQoEoFMHHHoxx")

    test_level("BBooKoooCCCKoxooIoxHJAAILoHJGMMLoFFGEELDooxPPPDoo")

    test_level("oKJJJoBGKCIIIBGoCEEMoGAADPMoxQQDPHOoNNoLHORRFFLHO")