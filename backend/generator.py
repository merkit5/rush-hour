import random
import heapq
import os
import time
from collections import defaultdict, deque

# Game constants
FIELD_WIDTH = 6
FIELD_HEIGHT = 6
FIELD_SIZE = FIELD_WIDTH * FIELD_HEIGHT
RED_ROW = 2  # 0-based index (3rd row)
RED_LENGTH = 2
MAX_CARS = 16
MAX_ATTEMPTS = 5000000
WALL_PROBABILITY = 0.15  # Вероятность появления стены в ячейке

# Difficulty thresholds
EASY_MIN = 10
EASY_MAX = 14
MEDIUM_MIN = 15
MEDIUM_MAX = 24
HARD_MIN = 25

# Output files
EASY_FILE = "../frontend/src/levels/easy.js"
MEDIUM_FILE = "../frontend/src/levels/medium.js"
HARD_FILE = "../frontend/src/levels/hard.js"


class RushHourGenerator:
    def __init__(self):
        self.easy_count = 0
        self.medium_count = 0
        self.hard_count = 0
        self.seen_configs = set()
        self.unsolvable_configs = set()
        self.start_time = time.time()
        self.load_existing_levels()
        self.cache = {}
        self.total_generated = 0

    def load_existing_levels(self):
        """Load existing levels from JS files only to avoid duplicates"""
        for fname in [EASY_FILE, MEDIUM_FILE, HARD_FILE]:
            try:
                with open(fname, 'r') as f:
                    content = f.read()
                    # Извлекаем уровни из JS-файла
                    start = content.find('[') + 1
                    end = content.find(']', start)
                    levels_str = content[start:end]
                    
                    # Обрабатываем каждый уровень
                    for line in levels_str.split('\n'):
                        line = line.strip()
                        if line.startswith('"') and line.endswith('"'):
                            config = line[1:-1]
                            self.seen_configs.add(config)
            except FileNotFoundError:
                continue

    def generate_smart_config(self, difficulty=None):
        """Smart configuration generation with walls and difficulty awareness"""
        attempts = 0
        max_attempts = 1000  # Лимит попыток генерации одной конфигурации

        while attempts < max_attempts:
            attempts += 1
            self.total_generated += 1
            field = ['o'] * FIELD_SIZE

            # Place walls first (only for hard levels)
            if difficulty == 'hard':
                for i in range(FIELD_SIZE):
                    if random.random() < WALL_PROBABILITY:
                        # Don't place walls in the red car's exit path
                        if not (i // FIELD_WIDTH == RED_ROW and i % FIELD_WIDTH >= RED_LENGTH):
                            field[i] = 'x'

            # Place red car with weighted distribution
            red_x = random.choices(
                range(FIELD_WIDTH - RED_LENGTH),
                weights=[(x + 1) * (FIELD_WIDTH - x - RED_LENGTH) for x in range(FIELD_WIDTH - RED_LENGTH)],
                k=1
            )[0]
            pos1 = RED_ROW * FIELD_WIDTH + red_x
            pos2 = pos1 + 1
            if field[pos1] != 'o' or field[pos2] != 'o':
                continue  # Try again if red car can't be placed

            field[pos1] = 'A'
            field[pos2] = 'A'

            # Place other cars
            cars_placed = 1
            car_chars = 'BCDEFGHIJKLMNOPQRSTUVWXYZ'[:MAX_CARS - 1]

            for c in car_chars:
                # For hard levels, increase chance of vertical and longer cars
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
                else:
                    # Если не удалось разместить машину, пропускаем её
                    continue

            config = ''.join(field)

            # Уменьшил минимальное количество машин с 8 до 6
            if (config not in self.seen_configs and
                    config not in self.unsolvable_configs and
                    cars_placed >= 6):  # Minimum 6 cars now
                self.seen_configs.add(config)
                return config

        # Если не удалось сгенерировать за max_attempts попыток
        print(f"Failed to generate config after {max_attempts} attempts")
        return None

    def find_valid_car_position(self, field, length, orientation):
        """Find valid position for a car considering walls"""
        attempts = 0
        max_attempts = 100

        while attempts < max_attempts:
            attempts += 1

            if orientation == 'h':
                x = random.randint(0, FIELD_WIDTH - length)
                y = random.randint(0, FIELD_HEIGHT - 1)
                if y == RED_ROW: continue  # Skip red car's row
                positions = [y * FIELD_WIDTH + x + i for i in range(length)]
            else:
                x = random.randint(0, FIELD_WIDTH - 1)
                y = random.randint(0, FIELD_HEIGHT - length)
                positions = [(y + i) * FIELD_WIDTH + x for i in range(length)]

            if all(field[p] == 'o' for p in positions):
                # Ослабил проверку на блокировку - теперь только проверяем, не блокирует ли выход
                if orientation == 'h' and y == RED_ROW:
                    # Проверяем, не блокирует ли выход красной машины
                    red_pos = field.index('A')
                    red_x = red_pos % FIELD_WIDTH
                    exit_path = range(red_x + RED_LENGTH, FIELD_WIDTH)
                    car_x_start = positions[0] % FIELD_WIDTH
                    car_x_end = positions[-1] % FIELD_WIDTH
                    if any(car_x_start <= x <= car_x_end for x in exit_path):
                        continue

                return positions

        return None

    def would_block_car_movement(self, field, positions, orientation):
        """Check if walls would completely block car's movement"""
        # For horizontal cars
        if orientation == 'h':
            y = positions[0] // FIELD_WIDTH
            x_left = positions[0] % FIELD_WIDTH - 1
            x_right = positions[-1] % FIELD_WIDTH + 1

            # Check if blocked on both sides
            left_blocked = x_left < 0 or field[y * FIELD_WIDTH + x_left] != 'o'
            right_blocked = x_right >= FIELD_WIDTH or field[y * FIELD_WIDTH + x_right] != 'o'
            return left_blocked and right_blocked

        # For vertical cars
        else:
            x = positions[0] % FIELD_WIDTH
            y_top = positions[0] // FIELD_WIDTH - 1
            y_bottom = positions[-1] // FIELD_WIDTH + 1

            # Check if blocked on both sides
            top_blocked = y_top < 0 or field[y_top * FIELD_WIDTH + x] != 'o'
            bottom_blocked = y_bottom >= FIELD_HEIGHT or field[y_bottom * FIELD_WIDTH + x] != 'o'
            return top_blocked and bottom_blocked

    def would_block_red_exit(self, field, positions, orientation):
        """Check if placing this car would block red car's exit path"""
        red_pos = field.index('A')
        red_x = red_pos % FIELD_WIDTH
        exit_path = range(red_x + RED_LENGTH, FIELD_WIDTH)

        if orientation == 'h' and positions[0] // FIELD_WIDTH == RED_ROW:
            car_x_start = positions[0] % FIELD_WIDTH
            car_x_end = positions[-1] % FIELD_WIDTH
            return any(car_x_start <= x <= car_x_end for x in exit_path)
        return False

    def solve_and_classify(self, config):
        """Solve configuration and classify by difficulty"""
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

        if EASY_MIN <= steps <= EASY_MAX:
            return ('easy', steps)
        elif MEDIUM_MIN <= steps <= MEDIUM_MAX:
            return ('medium', steps)
        elif steps >= HARD_MIN:
            return ('hard', steps)
        return None

    def solve_with_astar(self, config):
        """Optimized A* solver with heuristic"""
        grid = self.convert_to_grid(config)
        cars = self.parse_grid(grid)

        open_set = []
        heapq.heappush(open_set, (0, 0, grid, cars, []))

        visited = set()
        g_scores = {}
        initial_key = self.get_state_key(grid)
        g_scores[initial_key] = 0

        while open_set:
            _, g_score, grid, cars, path = heapq.heappop(open_set)
            current_key = self.get_state_key(grid)

            if current_key in visited:
                continue

            visited.add(current_key)

            if self.is_solved(cars):
                return len(path)

            for move in self.get_valid_moves(grid, cars):
                new_grid, new_cars = self.apply_move(grid, cars, move)
                new_key = self.get_state_key(new_grid)

                new_g = g_score + 1
                if new_key not in g_scores or new_g < g_scores[new_key]:
                    g_scores[new_key] = new_g
                    h = self.heuristic(new_grid, new_cars)
                    f = new_g + h
                    heapq.heappush(open_set, (f, new_g, new_grid, new_cars, path + [move]))

        return None

    def convert_to_grid(self, config):
        """Convert string config to grid representation with walls"""
        grid = [[0 for _ in range(7)] for _ in range(6)]
        char_to_id = {'A': 1}
        next_id = 2

        for i, c in enumerate(config):
            row, col = divmod(i, 6)
            if c == 'o':
                grid[row][col] = 0
            elif c == 'x':
                grid[row][col] = -1  # Wall
            else:
                if c not in char_to_id:
                    char_to_id[c] = next_id
                    next_id += 1
                grid[row][col] = char_to_id[c]

        grid[2][6] = 99  # Exit position
        return grid

    def parse_grid(self, grid):
        """Parse grid into car objects, ignoring walls"""
        cars = []
        car_ids = set()

        for row in range(6):
            for col in range(6):
                cell = grid[row][col]
                if cell > 0 and cell != 99:
                    car_ids.add(cell)

        for car_id in car_ids:
            positions = []
            for row in range(6):
                for col in range(6):
                    if grid[row][col] == car_id:
                        positions.append((row, col))

            if len(positions) < 2:
                continue  # Skip invalid cars

            if positions[0][0] == positions[1][0]:
                orientation = 'h'
                length = max(p[1] for p in positions) - positions[0][1] + 1
            else:
                orientation = 'v'
                length = max(p[0] for p in positions) - positions[0][0] + 1

            cars.append({
                'id': car_id,
                'orientation': orientation,
                'length': length,
                'row': positions[0][0],
                'col': positions[0][1]
            })

        return cars

    def get_state_key(self, grid):
        """Create unique key for grid state"""
        return tuple(tuple(row[:6]) for row in grid)

    def is_solved(self, cars):
        """Check if red car is at exit"""
        for car in cars:
            if car['id'] == 1:  # Red car
                return (car['orientation'] == 'h' and
                        car['row'] == 2 and
                        car['col'] + car['length'] == 6)
        return False

    def heuristic(self, grid, cars):
        """Optimized heuristic for A* considering walls"""
        blocking = 0
        red_car = next(car for car in cars if car['id'] == 1)

        if red_car['orientation'] != 'h' or red_car['row'] != 2:
            return float('inf')

        exit_col = red_car['col'] + red_car['length']

        # Check exit path for cars and walls
        for col in range(exit_col, 6):
            if grid[2][col] != 0 and grid[2][col] != 99:
                blocking += 1
            elif grid[2][col] == -1:  # Wall in exit path
                return float('inf')

        # Additional penalty for cars blocking the blocking cars
        for col in range(exit_col, 6):
            if grid[2][col] > 0:  # There's a car here
                # Check if this car is vertically oriented and can be moved
                car_id = grid[2][col]
                car = next(c for c in cars if c['id'] == car_id)
                if car['orientation'] == 'v':
                    # Check if there are walls above or below
                    up_blocked = car['row'] == 0 or grid[car['row'] - 1][col] == -1
                    down_blocked = (car['row'] + car['length'] >= 6 or
                                    grid[car['row'] + car['length']][col] == -1)
                    if up_blocked and down_blocked:
                        blocking += 1  # This car is stuck due to walls

        return blocking * 3  # Increased weight for harder levels

    def get_valid_moves(self, grid, cars):
        """Generate all valid moves considering walls"""
        moves = []

        for i, car in enumerate(cars):
            if car['orientation'] == 'h':
                # Left moves
                max_left = 0
                for dist in range(1, car['col'] + 1):
                    if grid[car['row']][car['col'] - dist] == 0:
                        max_left = dist
                    elif grid[car['row']][car['col'] - dist] == -1:  # Wall
                        break
                    else:
                        break
                if max_left > 0:
                    moves.append((i, 'left', max_left))

                # Right moves
                max_right = 0
                for dist in range(1, 6 - (car['col'] + car['length']) + 1):
                    target = car['col'] + car['length'] - 1 + dist
                    if target < 6:
                        if grid[car['row']][target] == 0:
                            max_right = dist
                        elif grid[car['row']][target] == -1:  # Wall
                            break
                        else:
                            break
                    elif target == 6 and car['id'] == 1:  # Red car exiting
                        max_right = dist
                        break
                if max_right > 0:
                    moves.append((i, 'right', max_right))
            else:
                # Up moves
                max_up = 0
                for dist in range(1, car['row'] + 1):
                    if grid[car['row'] - dist][car['col']] == 0:
                        max_up = dist
                    elif grid[car['row'] - dist][car['col']] == -1:  # Wall
                        break
                    else:
                        break
                if max_up > 0:
                    moves.append((i, 'up', max_up))

                # Down moves
                max_down = 0
                for dist in range(1, 6 - (car['row'] + car['length']) + 1):
                    if grid[car['row'] + car['length'] - 1 + dist][car['col']] == 0:
                        max_down = dist
                    elif grid[car['row'] + car['length'] - 1 + dist][car['col']] == -1:  # Wall
                        break
                    else:
                        break
                if max_down > 0:
                    moves.append((i, 'down', max_down))

        return moves

    def apply_move(self, grid, cars, move):
        """Apply move to grid and cars, considering walls"""
        car_idx, direction, distance = move
        car = cars[car_idx]

        new_grid = [row.copy() for row in grid]
        new_cars = [c.copy() for c in cars]

        # Clear old positions
        for i in range(car['length']):
            if car['orientation'] == 'h':
                new_grid[car['row']][car['col'] + i] = 0
            else:
                new_grid[car['row'] + i][car['col']] = 0

        # Update position
        if direction == 'left':
            new_cars[car_idx]['col'] -= distance
        elif direction == 'right':
            new_cars[car_idx]['col'] += distance
        elif direction == 'up':
            new_cars[car_idx]['row'] -= distance
        elif direction == 'down':
            new_cars[car_idx]['row'] += distance

        # Place in new positions
        for i in range(new_cars[car_idx]['length']):
            if new_cars[car_idx]['orientation'] == 'h':
                col = new_cars[car_idx]['col'] + i
                if col < 6:
                    new_grid[new_cars[car_idx]['row']][col] = car['id']
            else:
                new_grid[new_cars[car_idx]['row'] + i][new_cars[car_idx]['col']] = car['id']

        return new_grid, new_cars

    def save_config(self, config, difficulty, steps):
        """Save configuration to appropriate file in JS format"""
        filename = {
            'easy': EASY_FILE,
            'medium': MEDIUM_FILE,
            'hard': HARD_FILE
        }[difficulty]

        # Читаем текущее содержимое файла
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = "export const {}Levels = [\n]".format(difficulty)

        # Если файл пустой или не содержит массива, инициализируем его
        if "export const" not in content:
            content = "export const {}Levels = [\n]".format(difficulty)

        # Удаляем последнюю скобку и новую строку
        if content.endswith("]"):
            content = content[:-1]
        
        # Добавляем новую конфигурацию
        if not content.endswith("[\n"):
            content += ",\n"
        content += f'"{config}"\n]'

        # Записываем обратно в файл
        with open(filename, 'w') as f:
            f.write(content)

    def print_progress(self):
        """Print current generation progress"""
        elapsed = time.time() - self.start_time
        print(f"\n--- Progress after {elapsed:.1f} seconds ---")
        print(f"Easy levels generated: {self.easy_count}/15")
        print(f"Medium levels generated: {self.medium_count}/15")
        print(f"Hard levels generated: {self.hard_count}/15")
        print("-----------------------------\n")

    def run(self):
        """Main generation loop - generates exactly 15 levels of each difficulty"""
        print("Starting level generator...")
        print(f"Target: 15 easy, 15 medium, 15 hard levels")

        # Сбрасываем счетчики
        self.easy_count = 0
        self.medium_count = 0
        self.hard_count = 0
        
        attempt = 0
        last_print = 0

        while (self.easy_count < 15 or 
            self.medium_count < 15 or 
            self.hard_count < 15) and attempt < MAX_ATTEMPTS:
            
            attempt += 1
            
            # Выбираем целевую сложность
            if self.hard_count < 15 and random.random() < 0.5:
                difficulty_target = 'hard'
            elif self.medium_count < 15 and random.random() < 0.5:
                difficulty_target = 'medium'
            else:
                difficulty_target = 'easy'

            config = self.generate_smart_config(difficulty=difficulty_target)
            
            if not config:
                continue

            result = self.solve_and_classify(config)
            
            if not result:
                continue
                
            difficulty, steps = result
            
            # Сохраняем только если это нужная сложность
            if (difficulty == 'easy' and self.easy_count < 15) or \
            (difficulty == 'medium' and self.medium_count < 15) or \
            (difficulty == 'hard' and self.hard_count < 15):
                
                self.save_config(config, difficulty, steps)
                
                if difficulty == 'easy':
                    self.easy_count += 1
                elif difficulty == 'medium':
                    self.medium_count += 1
                else:
                    self.hard_count += 1
                    
                print(f"Generated {difficulty} level with {steps} steps")
            
            if time.time() - last_print > 10:
                self.print_progress()
                last_print = time.time()

        self.print_progress()
        print("\nGeneration complete!")
        print(f"Total attempts: {attempt}")
        print(f"Total generated configs: {self.total_generated}")
        print(f"Total unique configurations: {len(self.seen_configs)}")
        print(f"Total unsolvable configurations: {len(self.unsolvable_configs)}")

        
if __name__ == "__main__":
    generator = RushHourGenerator()
    generator.run()