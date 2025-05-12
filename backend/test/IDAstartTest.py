from functools import lru_cache
import time
import tracemalloc
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class RushHourIDAStar:
    def __init__(self, level_str):
        self.level_str = level_str
        self.grid = self.convert_level_to_grid()
        self.rows = 6
        self.cols = 6
        self.cars = self.parse_cars()
        self.target_row = 2
        self.exit_col = 6
        self.nodes_expanded = 0
        self.memory_cache = {}
        self.best_solution = None
        self.solution_found = False

    def convert_level_to_grid(self):
        grid = [[0 for _ in range(7)] for _ in range(6)]
        self.char_to_id = {'A': 1}
        self.id_to_char = {1: 'A'}
        next_id = 2

        for i, char in enumerate(self.level_str):
            row = i // 6
            col = i % 6
            if char == 'o':
                grid[row][col] = 0
            elif char == 'x':
                grid[row][col] = -1
            else:
                if char not in self.char_to_id:
                    self.char_to_id[char] = next_id
                    self.id_to_char[next_id] = char
                    next_id += 1
                grid[row][col] = self.char_to_id[char]

        grid[2][6] = 99  # Exit position
        return grid

    def parse_cars(self):
        cars = {}
        positions = {}

        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]
                if cell > 0:
                    positions.setdefault(cell, []).append((row, col))

        for car_id, pos_list in positions.items():
            pos_list.sort()
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
        red_car = cars.get(1)
        if not red_car:
            return False
        return (red_car['orientation'] == 'h' and 
            red_car['row'] == self.target_row and 
            red_car['col'] + red_car['length'] > self.cols - 1)


    def heuristic(self, cars):
        red_car = cars.get(1)
        if not red_car or red_car['orientation'] != 'h' or red_car['row'] != self.target_row:
            return float('inf')

        exit_pos = red_car['col'] + red_car['length']
        if exit_pos == self.exit_col:
            return 0

        grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for car in cars.values():
            if car['orientation'] == 'h':
                for i in range(car['length']):
                    if car['col'] + i < self.cols:
                        grid[car['row']][car['col'] + i] = car['id']
            else:
                for i in range(car['length']):
                    grid[car['row'] + i][car['col']] = car['id']

        blocking = 0
        for col in range(exit_pos, self.cols):
            if grid[self.target_row][col] != 0:
                blocking += 1
                blocking_car = cars.get(grid[self.target_row][col])
                if blocking_car and blocking_car['orientation'] == 'v':
                    blocking += 2

        return blocking + (self.exit_col - exit_pos)

    def get_moves(self, cars):
        if self.solution_found:
            return []

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
                # Left moves
                move_dist = 0
                while (car['col'] - move_dist - 1 >= 0 and 
                       grid[car['row']][car['col'] - move_dist - 1] == 0):
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'left', move_dist))

                # Right moves
                move_dist = 0
                while (car['col'] + car['length'] + move_dist < self.cols and 
                       grid[car['row']][car['col'] + car['length'] + move_dist] == 0):
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'right', move_dist))
                if car_id == 1 and car['col'] + car['length'] + move_dist == self.cols:
                    moves.append((car_id, 'right', move_dist + 1))
            else:
                # Up moves
                move_dist = 0
                while (car['row'] - move_dist - 1 >= 0 and 
                       grid[car['row'] - move_dist - 1][car['col']] == 0):
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'up', move_dist))

                # Down moves
                move_dist = 0
                while (car['row'] + car['length'] + move_dist < self.rows and 
                       grid[car['row'] + car['length'] + move_dist][car['col']] == 0):
                    move_dist += 1
                    if move_dist > 0:
                        moves.append((car_id, 'down', move_dist))

        return moves

    def apply_move(self, cars, move):
        car_id, direction, dist = move
        new_cars = {cid: {**car} for cid, car in cars.items()}
        car = new_cars[car_id]

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
        initial_cars = {car['id']: car for car in self.cars.values()}
        threshold = self.heuristic(initial_cars)
        
        while not self.solution_found:
            self.memory_cache = {}
            result = self.ida_star(initial_cars, [], 0, threshold)
            if self.solution_found:
                return self.best_solution
            if result == float('inf'):
                return None
            threshold = result

    def ida_star(self, cars, path, g, threshold):
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

        state_key = tuple((cid, car['orientation'], car['row'], car['col']) 
                         for cid, car in sorted(cars.items()))
        if state_key in self.memory_cache:
            if self.memory_cache[state_key] <= g:
                return float('inf')
        self.memory_cache[state_key] = g

        min_threshold = float('inf')
        moves = self.get_moves(cars)
        moves.sort(key=lambda move: self.heuristic(self.apply_move(cars, move)))

        for move in moves:
            new_cars = self.apply_move(cars, move)
            result = self.ida_star(new_cars, path + [move], g + 1, threshold)
            
            if self.solution_found:
                return "FOUND"
            if result < min_threshold:
                min_threshold = result

        return min_threshold

    def print_solution(self, solution):
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

if __name__ == "__main__":
    level_str = "FJoDDDFJoHHHAACMooEoCMoGELBIIGELBKKo"

    tracemalloc.start()
    start_time = time.time()

    solver = RushHourIDAStar(level_str)
    solution = solver.solve()

    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    solver.print_solution(solution)
    print(f"\nВремя выполнения: {end_time - start_time:.2f} сек")
    print(f"Пиковое использование памяти: {peak / 1024:.2f} KB")