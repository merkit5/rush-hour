import random
import heapq
import os
import time
from collections import defaultdict, deque
from multiprocessing import Pool, Lock
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Конфигурация размеров поля
FIELD_SIZES = {
    '5x5': {
        'width': 5, 'height': 5, 'red_row': 2,
        'thresholds': {'EASY_MIN': 6, 'EASY_MAX': 10, 'MEDIUM_MIN': 11, 'MEDIUM_MAX': 15, 'HARD_MIN': 16}
    },
    '6x6': {
        'width': 6, 'height': 6, 'red_row': 2,
        'thresholds': {'EASY_MIN': 10, 'EASY_MAX': 14, 'MEDIUM_MIN': 15, 'MEDIUM_MAX': 20, 'HARD_MIN': 21}
    },
    '7x7': {
        'width': 7, 'height': 7, 'red_row': 3,
        'thresholds': {'EASY_MIN': 12, 'EASY_MAX': 16, 'MEDIUM_MIN': 17, 'MEDIUM_MAX': 22, 'HARD_MIN': 23}
    }
}

RED_LENGTH = 2
MAX_CARS = 21
MAX_ATTEMPTS = 5000000
WALL_PROBABILITY = 0.15

file_lock = Lock()


class RushHourGenerator:
    def __init__(self, size):
        self.size = size
        self.size_params = FIELD_SIZES[size]
        self.thresholds = self.size_params['thresholds']
        self.easy_count = 0
        self.medium_count = 0
        self.hard_count = 0
        self.seen_configs = set()
        self.unsolvable_configs = set()
        self.cache = {}
        self.total_generated = 0
        self.start_time = time.time()
        self.load_existing_levels()

    def get_thresholds(self):
        return self.thresholds

    def get_output_files(self):
        return {
            'easy': f"../frontend/src/levels/easy_{self.size}.js",
            'medium': f"../frontend/src/levels/medium_{self.size}.js",
            'hard': f"../frontend/src/levels/hard_{self.size}.js"
        }

    def load_existing_levels(self):
        files = self.get_output_files()
        for fname in files.values():
            try:
                with open(fname, 'r') as f:
                    content = f.read()
                    start = content.find('[') + 1
                    end = content.find(']', start)
                    levels_str = content[start:end]
                    for line in levels_str.split('\n'):
                        line = line.strip()
                        if line.startswith('"') and line.endswith('"'):
                            config = line[1:-1]
                            self.seen_configs.add(config)
            except FileNotFoundError:
                continue

    def generate_smart_config(self, difficulty=None):
        attempts = 0
        max_attempts = 1000
        width = self.size_params['width']
        height = self.size_params['height']
        red_row = self.size_params['red_row']

        while attempts < max_attempts:
            attempts += 1
            self.total_generated += 1
            field = ['o'] * (width * height)

            if difficulty == 'hard':
                for i in range(width * height):
                    if random.random() < WALL_PROBABILITY:
                        if not (i // width == red_row and i % width >= RED_LENGTH):
                            field[i] = 'x'

            red_x = random.choices(
                range(width - RED_LENGTH),
                weights=[(x + 1) * (width - x - RED_LENGTH) for x in range(width - RED_LENGTH)],
                k=1
            )[0]
            pos1 = red_row * width + red_x
            pos2 = pos1 + 1
            if field[pos1] != 'o' or field[pos2] != 'o':
                continue

            field[pos1] = 'A'
            field[pos2] = 'A'

            cars_placed = 1
            car_chars = 'BCDEFGHIJKLMNOPQRSTUVWXYZ'[:MAX_CARS - 1]

            for c in car_chars:
                if difficulty == 'hard':
                    orientation = random.choices(['v', 'h'], weights=[7, 3], k=1)[0]
                    length = random.choices([2, 3], weights=[5, 5], k=1)[0]
                else:
                    orientation = random.choices(['v', 'h'], weights=[6, 4], k=1)[0]
                    length = random.choices([2, 3], weights=[6, 4], k=1)[0]

                positions = self.find_valid_car_position(field, length, orientation)
                if positions:
                    for p in positions:
                        field[p] = c
                    cars_placed += 1

            config = ''.join(field)

            if (config not in self.seen_configs and
                    config not in self.unsolvable_configs and
                    cars_placed >= 6):
                self.seen_configs.add(config)
                return config, attempts

        return None, attempts

    def find_valid_car_position(self, field, length, orientation):
        """Находит валидную позицию для машины"""
        attempts = 0
        max_attempts = 100
        width = self.size_params['width']
        height = self.size_params['height']
        red_row = self.size_params['red_row']

        while attempts < max_attempts:
            attempts += 1

            if orientation == 'h':
                x = random.randint(0, width - length)
                y = random.randint(0, height - 1)
                if y == red_row: continue
                positions = [y * width + x + i for i in range(length)]
            else:
                x = random.randint(0, width - 1)
                y = random.randint(0, height - length)
                positions = [(y + i) * width + x for i in range(length)]

            if all(field[p] == 'o' for p in positions):
                if orientation == 'h' and y == red_row:
                    red_pos = field.index('A')
                    red_x = red_pos % width
                    exit_path = range(red_x + RED_LENGTH, width)
                    car_x_start = positions[0] % width
                    car_x_end = positions[-1] % width
                    if any(car_x_start <= x <= car_x_end for x in exit_path):
                        continue
                return positions

        return None

    def solve_and_classify(self, config):
        """Классифицирует уровень по сложности"""
        if config in self.unsolvable_configs:
            return None

        if config in self.cache:
            steps = self.cache[config]
        else:
            steps = self.solve_with_astar(config)
            self.cache[config] = steps

        if steps is None:
            self.unsolvable_configs.add(config)
            return None

        t = self.get_thresholds()
        if t['EASY_MIN'] <= steps <= t['EASY_MAX']:
            return ('easy', steps)
        elif t['MEDIUM_MIN'] <= steps <= t['MEDIUM_MAX']:
            return ('medium', steps)
        elif steps >= t['HARD_MIN']:
            return ('hard', steps)
        return None

    def solve_with_astar(self, config):
        """Решает уровень с помощью A* с унифицированной эвристикой"""
        grid = self.convert_to_grid(config)
        cars = self.parse_grid(grid)
        width = self.size_params['width']
        height = self.size_params['height']
        exit_row = self.size_params['red_row']
        exit_col = width

        open_set = []
        heapq.heappush(open_set, (0, 0, grid, cars, []))

        visited = set()
        g_scores = {}
        initial_key = self.get_state_key(grid)
        g_scores[initial_key] = 0

        while open_set:
            _, g_score, current_grid, cars, path = heapq.heappop(open_set)
            current_key = self.get_state_key(current_grid)

            if current_key in visited:
                continue
            visited.add(current_key)

            if self.is_solved(cars):
                return len(path)

            for move in self.get_possible_moves(current_grid, cars, width, height, exit_row):
                new_grid, new_cars = self.apply_move(current_grid, cars, move, width, height)
                new_key = self.get_state_key(new_grid)

                new_g = g_score + 1
                if new_key not in g_scores or new_g < g_scores[new_key]:
                    g_scores[new_key] = new_g
                    h = self.heuristic(new_grid, new_cars, exit_row, exit_col)
                    f = new_g + h
                    heapq.heappush(open_set, (f, new_g, new_grid, new_cars, path + [move]))

        return None

    def convert_to_grid(self, config):
        """Конвертирует строку уровня в сетку"""
        width = self.size_params['width']
        height = self.size_params['height']
        red_row = self.size_params['red_row']
        
        grid = [[0 for _ in range(width + 1)] for _ in range(height)]
        char_to_id = {'A': 1}
        next_id = 2

        for i, c in enumerate(config):
            row, col = divmod(i, width)
            if c == 'o':
                grid[row][col] = 0
            elif c == 'x':
                grid[row][col] = -1
            else:
                if c not in char_to_id:
                    char_to_id[c] = next_id
                    next_id += 1
                grid[row][col] = char_to_id[c]

        grid[red_row][width] = 99
        return grid

    def parse_grid(self, grid):
        """Парсит сетку в список машин"""
        width = self.size_params['width']
        height = self.size_params['height']
        cars = []
        car_ids = set()

        for row in range(height):
            for col in range(width):
                cell = grid[row][col]
                if cell > 0 and cell != 99:
                    car_ids.add(cell)

        for car_id in car_ids:
            positions = []
            for row in range(height):
                for col in range(width):
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

    def get_state_key(self, grid):
        """Создает ключ состояния сетки"""
        width = self.size_params['width']
        return tuple(tuple(row[:width]) for row in grid)

    def is_solved(self, cars):
        """Проверяет, решен ли уровень"""
        width = self.size_params['width']
        red_row = self.size_params['red_row']
        
        for car in cars:
            if car['id'] == 1:
                return (car['orientation'] == 'h' and
                        car['row'] == red_row and
                        car['col'] + car['length'] == width)
        return False

    def heuristic(self, grid, cars, exit_row, exit_col):
        """Унифицированная эвристика: количество машин на пути"""
        red_car = next((car for car in cars if car['id'] == 1), None)
        if not red_car:
            return float('inf')

        if red_car['orientation'] != 'h' or red_car['row'] != exit_row:
            return float('inf')

        blocking = 0
        exit_col_red = red_car['col'] + red_car['length']
        
        for col in range(exit_col_red, exit_col):
            if grid[exit_row][col] != 0 and grid[exit_row][col] != 99:
                blocking += 1

        return blocking

    def get_possible_moves(self, grid, cars, width, height, exit_row):
        """Генерирует все возможные ходы"""
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
                    if new_col < width:
                        if grid[car['row']][new_col] == 0:
                            right_move = dist
                        else:
                            break
                    elif new_col == width and car['id'] == 1:
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

    def apply_move(self, grid, cars, move, width, height):
        """Применяет ход к сетке"""
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

    def save_config(self, config, difficulty, steps):
        """Сохраняет конфигурацию в файл"""
        filename = f"../frontend/src/levels/{difficulty}_{self.size}.js"
        
        with file_lock:
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
            except FileNotFoundError:
                content = f"export const {difficulty.capitalize()}Levels = [\n]"

            if "export const" not in content:
                content = f"export const {difficulty.capitalize()}Levels = [\n]"

            if content.endswith("]"):
                content = content[:-1]
            
            if not content.endswith("[\n"):
                content += ",\n"
            content += f'"{config}"\n]'

            with open(filename, 'w') as f:
                f.write(content)

    def run(self):
        print(f"Старт генерации {self.size}...", flush=True)
        attempt_id = 0  # <- глобальный счётчик попыток генерации

        while (self.easy_count < 15 or self.medium_count < 15 or self.hard_count < 15):
            attempt_id += 1  # Увеличиваем каждый раз, когда пробуем сгенерировать
            if self.hard_count < 15:
                difficulty_target = 'hard'
            elif self.medium_count < 15:
                difficulty_target = 'medium'
            else:
                difficulty_target = 'easy'

            config, _ = self.generate_smart_config(difficulty_target)
            if not config:
                continue

            result = self.solve_and_classify(config)
            if not result:
                continue

            difficulty, steps = result

            if difficulty == 'easy' and self.easy_count >= 15:
                continue
            elif difficulty == 'medium' and self.medium_count >= 15:
                continue
            elif difficulty == 'hard' and self.hard_count >= 15:
                continue

            self.save_config(config, difficulty, steps)

            if difficulty == 'easy':
                self.easy_count += 1
            elif difficulty == 'medium':
                self.medium_count += 1
            else:
                self.hard_count += 1

            print(
                f"{self.size}: {difficulty.upper()} ({steps} шагов, найден на попытке #{attempt_id}) | "
                f"Easy: {self.easy_count}/15, Medium: {self.medium_count}/15, Hard: {self.hard_count}/15",
                flush=True
            )



def generate_for_size(size):
    generator = RushHourGenerator(size)
    generator.run()


if __name__ == "__main__":
    print("Запуск параллельной генерации...", flush=True)
    start_time = time.time()

    with Pool(processes=3) as pool:
        pool.map(generate_for_size, ['5x5', '6x6', '7x7'])

    total_time = time.time() - start_time
    print(f"Все уровни сгенерированы за {total_time:.1f} секунд", flush=True)