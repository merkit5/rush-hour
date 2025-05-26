from functools import lru_cache
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class RushHourIDAStar:
    def __init__(self, level_str):
        """Инициализация решателя Rush Hour с заданным уровнем"""
        self.level_str = level_str
        self.char_to_id = {'A': 1}  # Красная машина всегда имеет id 1
        self.id_to_char = {1: 'A'}
        self.grid_params = self.get_grid_params()
        self.rows, self.cols, self.target_row, self.exit_col = self.grid_params
        self.grid = self.convert_level_to_grid()
        self.cars = self.parse_cars()
        self.nodes_expanded = 0
        self.memory_cache = {}
        self.best_solution = None
        self.solution_found = False
        
    def get_grid_params(self):
        """Определяет параметры поля по длине строки уровня"""
        length = len(self.level_str)
        if length == 25:  # 5x5
            return (5, 5, 2, 5)  # rows, cols, exit_row, exit_col
        elif length == 36:  # 6x6
            return (6, 6, 2, 6)
        elif length == 49:  # 7x7
            return (7, 7, 3, 7)
        else:
            raise ValueError(f"Неподдерживаемый размер поля: длина строки {length}")

    def convert_level_to_grid(self):
        """Конвертирует строку уровня в числовую сетку"""
        grid = [[0 for _ in range(self.cols + 1)] for _ in range(self.rows)]  # +1 для выхода
        next_id = 2  # Начинаем с 2, так как 1 уже занята красной машиной

        for i, char in enumerate(self.level_str):
            row = i // self.cols
            col = i % self.cols
            if char == 'o':
                grid[row][col] = 0  # Пустая клетка
            elif char == 'x':
                grid[row][col] = -1  # Стена
            else:
                if char not in self.char_to_id:
                    self.char_to_id[char] = next_id
                    self.id_to_char[next_id] = char
                    next_id += 1
                grid[row][col] = self.char_to_id[char]

        # Добавляем выход для красной машины
        grid[self.target_row][self.exit_col] = 99
        return grid

    def parse_cars(self):
        """Анализирует сетку и возвращает словарь машин"""
        cars = {}
        positions = {}

        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]
                if cell > 0:  # 0 - пусто, -1 - стена, >0 - машины
                    positions.setdefault(cell, []).append((row, col))

        for car_id, pos_list in positions.items():
            pos_list.sort()
            # Определяем ориентацию (горизонтальная/вертикальная)
            is_horizontal = pos_list[0][0] == pos_list[-1][0]
            length = len(pos_list)
            cars[car_id] = {
                'id': car_id,
                'orientation': 'h' if is_horizontal else 'v',
                'row': pos_list[0][0],
                'col': pos_list[0][1],
                'length': length
            }

        return cars

    def is_goal(self, cars):
        """Проверяет, достигнуто ли целевое состояние"""
        red_car = cars.get(1)  # Красная машина всегда имеет id 1
        if not red_car:
            return False
        return (red_car['orientation'] == 'h' and 
                red_car['row'] == self.target_row and 
                red_car['col'] + red_car['length'] == self.exit_col)

    def heuristic(self, cars):
        """Продвинутая эвристика: количество блокирующих машин + невозможность их сдвига"""
        red_car = cars.get(1)
        if not red_car or red_car['orientation'] != 'h' or red_car['row'] != self.target_row:
            return float('inf')

        # Временная сетка
        grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for car in cars.values():
            if car['orientation'] == 'h':
                for i in range(car['length']):
                    if 0 <= car['col'] + i < self.cols:
                        grid[car['row']][car['col'] + i] = car['id']
            else:
                for i in range(car['length']):
                    if 0 <= car['row'] + i < self.rows:
                        grid[car['row'] + i][car['col']] = car['id']

        blocking_ids = set()
        red_exit_col = red_car['col'] + red_car['length']
        for col in range(red_exit_col, self.cols):
            cell = grid[self.target_row][col]
            if cell > 0 and cell != 1:
                blocking_ids.add(cell)

        heuristic_score = 0
        for block_id in blocking_ids:
            heuristic_score += 1
            blocker = cars[block_id]
            if blocker['orientation'] == 'v':
                # Проверяем, может ли вертикальная машина сдвинуться вверх или вниз
                row, col = blocker['row'], blocker['col']
                can_move = False
                # вверх
                if row > 0 and grid[row - 1][col] == 0 and self.grid[row - 1][col] != -1:
                    can_move = True
                # вниз
                if row + blocker['length'] < self.rows and grid[row + blocker['length']][col] == 0 and self.grid[row + blocker['length']][col] != -1:
                    can_move = True
                if not can_move:
                    heuristic_score += 1  # Удваиваем, если не может сдвинуться

        # Добавим расстояние от хвоста красной машины до выхода
        heuristic_score += (self.exit_col - (red_car['col'] + red_car['length']))
        return heuristic_score

    def get_moves(self, cars):
        """Генерирует все возможные ходы для текущего состояния"""
        if self.solution_found:
            return []

        # Создаем временную сетку для проверки перемещений
        grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for car in cars.values():
            if car['orientation'] == 'h':
                for i in range(car['length']):
                    if car['col'] + i < self.cols:
                        grid[car['row']][car['col'] + i] = car['id']
            else:
                for i in range(car['length']):
                    grid[car['row'] + i][car['col']] = car['id']

        moves = []
        for car_id, car in cars.items():
            if car['orientation'] == 'h':
                # Движение влево
                move_dist = 0
                while (car['col'] - move_dist - 1 >= 0 and 
                    grid[car['row']][car['col'] - move_dist - 1] <= 0):  # Проверяем <= 0 (пусто или стена)
                    if grid[car['row']][car['col'] - move_dist - 1] == -1:  # Если стена - прерываем
                        break
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'left', move_dist))

                # Движение вправо
                move_dist = 0
                while (car['col'] + car['length'] + move_dist < self.cols and 
                    grid[car['row']][car['col'] + car['length'] + move_dist] <= 0):
                    if grid[car['row']][car['col'] + car['length'] + move_dist] == -1:
                        break
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'right', move_dist))
                # Особый случай для красной машины и выхода
                if (car_id == 1 and 
                    car['col'] + car['length'] + move_dist == self.cols):
                    moves.append((car_id, 'right', move_dist + 1))
            else:
                # Движение вверх
                move_dist = 0
                while (car['row'] - move_dist - 1 >= 0 and 
                    grid[car['row'] - move_dist - 1][car['col']] <= 0):
                    if grid[car['row'] - move_dist - 1][car['col']] == -1:
                        break
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'up', move_dist))

                # Движение вниз
                move_dist = 0
                while (car['row'] + car['length'] + move_dist < self.rows and 
                    grid[car['row'] + car['length'] + move_dist][car['col']] <= 0):
                    if grid[car['row'] + car['length'] + move_dist][car['col']] == -1:
                        break
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'down', move_dist))

        return moves

    def apply_move(self, cars, move):
        """Применяет ход и возвращает новое состояние машин"""
        car_id, direction, dist = move
        new_cars = {cid: {**car} for cid, car in cars.items()}
        car = new_cars[car_id]

        # Проверяем, нет ли стен на пути
        if direction == 'left':
            for d in range(1, dist+1):
                if self.grid[car['row']][car['col'] - d] == -1:
                    return None  # Недопустимый ход - стена на пути
        elif direction == 'right':
            for d in range(1, dist+1):
                if car['col'] + car['length'] - 1 + d >= self.cols:
                    continue  # Выход за пределы - допустимо для красной машины
                if self.grid[car['row']][car['col'] + car['length'] - 1 + d] == -1:
                    return None
        elif direction == 'up':
            for d in range(1, dist+1):
                if self.grid[car['row'] - d][car['col']] == -1:
                    return None
        elif direction == 'down':
            for d in range(1, dist+1):
                if self.grid[car['row'] + car['length'] - 1 + d][car['col']] == -1:
                    return None

        # Применяем ход, если он допустим
        if direction == 'left':
            car['col'] -= dist
        elif direction == 'right':
            car['col'] += dist
        elif direction == 'up':
            car['row'] -= dist
        elif direction == 'down':
            car['row'] += dist

        return new_cars

    def solve(self):
        """Основной метод решения с использованием IDA*"""
        initial_cars = {car['id']: car for car in self.cars.values()}
        threshold = self.heuristic(initial_cars)
        
        while not self.solution_found:
            self.memory_cache = {}  # Очищаем кеш для новой итерации
            result = self.ida_star(initial_cars, [], 0, threshold)
            if self.solution_found:
                return self.best_solution
            if result == float('inf'):
                return None  # Решение не найдено
            threshold = result  # Увеличиваем порог для следующей итерации

    def ida_star(self, cars, path, g, threshold):
        """Рекурсивная функция поиска с итеративным углублением"""
        if self.solution_found:
            return float('inf')

        self.nodes_expanded += 1
        h = self.heuristic(cars)
        f = g + h

        if f > threshold:
            return f
        if self.is_goal(cars):
            self.solution_found = True
            self.best_solution = path.copy()
            return "FOUND"

        # Создаем ключ состояния для кеширования
        state_key = tuple((cid, car['orientation'], car['row'], car['col']) 
                    for cid, car in sorted(cars.items()))
        
        # Проверяем, не посещали ли мы это состояние с лучшим или равным g
        if state_key in self.memory_cache:
            if self.memory_cache[state_key] <= g:
                return float('inf')
        self.memory_cache[state_key] = g

        min_threshold = float('inf')
        moves = self.get_moves(cars)
        # Сортируем ходы по улучшению эвристики, фильтруя недопустимые
        moves.sort(key=lambda move: self.heuristic(self.apply_move(cars, move)) 
                if self.apply_move(cars, move) is not None else float('inf'))

        for move in moves:
            new_cars = self.apply_move(cars, move)
            if new_cars is None:  # Пропускаем недопустимые ходы
                continue
            result = self.ida_star(new_cars, path + [move], g + 1, threshold)
            
            if self.solution_found:
                return "FOUND"
            if result < min_threshold:
                min_threshold = result

        return min_threshold

    def print_solution(self, solution):
        """Выводит решение в удобочитаемом формате"""
        if not solution:
            print("Решение не найдено.")
            return
        
        # Проверяем, когда действительно достигнуто целевое состояние
        cars = {car['id']: car for car in self.cars.values()}
        optimal_path = []
        
        for i, move in enumerate(solution):
            cars = self.apply_move(cars, move)
            optimal_path.append(move)
            if self.is_goal(cars):
                print(f"Найдено оптимальное решение за {len(optimal_path)} шагов (рассмотрено {self.nodes_expanded} состояний):")
                for step, (cid, dir, dist) in enumerate(optimal_path, 1):
                    print(f"Шаг {step}: Машина {self.id_to_char.get(cid, str(cid))} → {dir} на {dist}")
                return
        
        print(f"Найдено решение за {len(solution)} шагов (рассмотрено {self.nodes_expanded} состояний):")
        for i, (cid, dir, dist) in enumerate(solution, 1):
            print(f"Шаг {i}: Машина {self.id_to_char.get(cid, str(cid))} → {dir} на {dist}")

def test_level(level_str):
    """Тестирует решение для одного уровня"""
    print(f"\nТестируем уровень: {level_str}")
    
    tracemalloc.start()
    start_time = time.time()
    
    solver = RushHourIDAStar(level_str)
    solution = solver.solve()
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    solver.print_solution(solution)
    print(f"Время выполнения: {end_time - start_time:.4f} сек")
    print(f"Пиковая память: {peak / 1024:.2f} KB")


if __name__ == "__main__":

    test_level("oooBNNNCGGBLLoCIxEEoJoIAAOFJoIDoOFoHoDoxFPHxoKKKP")

    test_level("GoxoxoHGLLLoxHGoKooEHAAKMFENoCCMFoNxDDMBBooJJoIII")

    test_level("oNoBKJJxNoBKooIFFBKLGIAAooLGCooDDDGCHHHooooooxEEx")

    test_level("OHDoCCoOHDooKoBxDJMKIBAAJMKIooLoMEINFLxoEPNFLGGxP")

    test_level("EoBoNNNECBxGIJxCBxGIJoCAAGKoFooxxKxFxHHHKLFooDDDL")

    test_level("oCMoHDDxCMxHGOoxxxHGOAAoooGBoFFFEEBxxooPooxxooPLL")

    test_level("oKCCCooEKMOOOFEKMLLLFNHMAAIFNHxoJIooHoDJPPGGoDoBB")

    test_level("LLLxxxNDxxoCCNDOoIIGNJOAAKGFJEEHKGFJooHoMMoxBBooo")

    test_level("DDDoLLLCCCFGGooooFoBoEIAAHBNEIMoHJNEoMoHJxooMKKJo")

    test_level("GGJBBoHCxJoDDHCxooFKHCoAAFKooIIIFKxxooNNNxxooxEEE")

    test_level("QoGNNKKQHGFFFMIHGoxEMIHAAoEMoJJJxoBDRLOCCBDRLOooo")

    test_level("EEooBGGIoJDBOOIxJDoCHIooAACHFFFooCooQRRxoxoQoxoSS")