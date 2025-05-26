from collections import deque
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_grid_params(level_str):
    """Определяет параметры поля на основе длины строки уровня"""
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
        positions = []
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] == car_id:
                    positions.append((row, col))

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
    """Возвращает все возможные ходы для текущего состояния"""
    moves = []
    rows = len(grid)
    cols = len(grid[0]) - 1  # Игнорируем выход
    
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
            max_possible = cols - (car['col'] + car['length'])
            for dist in range(1, max_possible + 1):
                new_col = car['col'] + car['length'] - 1 + dist
                if new_col < cols:  # Обычная клетка
                    if grid[car['row']][new_col] == 0:
                        right_move = dist
                    else:
                        break
                elif new_col == cols and car['id'] == 1:  # Выход (только для красной машины)
                    right_move = dist
                    break

            if right_move > 0:
                moves.append((i, 'right', right_move))

        else:  # Вертикальные машины
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
            max_possible = rows - (car['row'] + car['length'])
            for dist in range(1, max_possible + 1):
                if grid[car['row'] + car['length'] - 1 + dist][car['col']] == 0:
                    down_move = dist
                else:
                    break
            if down_move > 0:
                moves.append((i, 'down', down_move))

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
            if col < len(new_grid[0]) - 1:  # Не записываем в столбец выхода
                new_grid[new_cars[car_idx]['row']][col] = car['id']
        else:
            new_grid[new_cars[car_idx]['row'] + i][new_cars[car_idx]['col']] = car['id']

    return new_grid, new_cars

def solve_rush_hour(level_str):
    """Решает уровень Rush Hour, представленный в виде строки"""
    grid = convert_level_string_to_grid(level_str)
    initial_cars = parse_grid(grid)
    _, _, exit_row, exit_col = get_grid_params(level_str)
    
    queue = deque([(grid, initial_cars, [])])
    visited = set()

    while queue:
        current_grid, cars, path = queue.popleft()
        state_key = tuple(tuple(row[:len(grid[0])-1]) for row in current_grid)  # Исключаем столбец выхода
        
        if state_key in visited:
            continue
        visited.add(state_key)

        if is_goal_state(cars, exit_row, exit_col):
            return path

        for move in get_possible_moves(current_grid, cars):
            new_grid, new_cars = apply_move(current_grid, cars, move)
            queue.append((new_grid, new_cars, path + [move]))

    return None

def print_solution(solution, level_str):
    """Выводит решение в удобочитаемом формате"""
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
    
    solution = solve_rush_hour(level_str)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print_solution(solution, level_str)
    print(f"Время выполнения: {end_time - start_time:.4f} сек")
    print(f"Пиковая память: {peak / 1024:.2f} KB")

# Примеры использования для разных размеров
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