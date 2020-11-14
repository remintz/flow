
import time
from typing import List
from dataclasses import dataclass
import random

import blessed

@dataclass
class Task:
    def __init__(self, name: str, time_left: int, clock: int):
        self.name: str = name
        self.time_left: int = time_left
        self.current_column: int = 0
        self.waiting: bool = False
        self.started: int = clock
        self.finished: int = 0

@dataclass
class Column:
    name: str
    waiting: bool
    number: int
    tasks: List[Task]

class Game:
    def __init__(self, terminal, stages, cycle_time, min_time, max_time, wip, bottleneck_factor):
        self._tasks = []
        self._cycle_time = cycle_time
        self._running = False
        self._columns: List[Column] = []
        self._stages = stages
        self._term = terminal
        print(self._term.home + self._term.clear)
        self._number_of_tasks = 0
        self._next_task_name = 'A'
        self._min_time = min_time
        self._max_time = max_time
        self._clock = 0
        self._cfd = []
        self._avg_lead_time: float = 0.0
        self._avg_cycle_time: float = 0.0
        self._wip = wip
        self._finished_tasks = 0
        self._bottleneck_factor = bottleneck_factor

        col_number = 0
        for i in range(stages):

            column = Column(f'DOING {i}', False, col_number, [])
            self._columns.append(column)
            col_number += 1

            column = Column(f'DONE {i}', True, col_number, [])
            self._columns.append(column)
            col_number += 1

        self._bottleneck_column = len(self._columns) - 3

    def start(self):
        self._running = True
        while self._running:
            self._clock += 1
            self._wait()
            self._tick()
            self._redraw()

    def _calculate_cfd(self):
        # count # of tasks in each column
        count_col = [0] * len(self._columns)
        for task in self._tasks:
            count_col[task.current_column] += 1

    def _calculate_lead_time(self):
        sum_lead_times = 0
        count_tasks = 0
        for task in self._tasks:
            if task.finished != 0:
                sum_lead_times = sum_lead_times + (task.finished - task.started)
                count_tasks += 1
        self._avg_lead_time = 0.0 if count_tasks == 0 else sum_lead_times / count_tasks

    def _calculate_cycle_time(self):
        count_tasks = 0
        for task in self._tasks:
            if task.finished != 0:
                count_tasks += 1
        self._avg_cycle_time = 0.0 if count_tasks == 0 else self._clock / count_tasks

    def _calculate_finished_tasks(self):
        count_tasks = 0
        for task in self._tasks:
            if task.finished != 0:
                count_tasks += 1
        self._finished_tasks = count_tasks

    def _gen_task_name(self):
        self._number_of_tasks += 1
        return f'TASK #{self._number_of_tasks}'

    def _wait(self):
        if self._cycle_time > 0:
            time.sleep(self._cycle_time)
        else:
            self._print_xy(0, 30, '')
            input('->')

    def _choose_time(self, bottleneck_factor):
        if self._min_time == self._max_time:
            return int(self._min_time * bottleneck_factor)
        else:
            min_time = int(self._min_time * bottleneck_factor)
            max_time = int(self._max_time * bottleneck_factor)
            return random.randrange(min_time, max_time)

    def _print_xy(self, x, y, char):
        print(self._term.move_xy(x, y) + char)

    def _draw_square(self, left, top, width, height):
        self._print_xy(left, top, '+')
        self._print_xy(left + width, top, '+')
        self._print_xy(left, top + height, '+')
        self._print_xy(left + width, top + height, '+')
        for x in range(left + 1, left + width):
            self._print_xy(x, top, '-')
            self._print_xy(x, top + height, '-')
        for y in range(top + 1, top + height):
            self._print_xy(left, y, '|')
            self._print_xy(left + width, y, '|')

    def _draw_vertical_line(self, column, top, height, char):
        for i in range(height):
            print(self._term.move_xy(column, i + top) + char)

    def _draw_task(self, column, height, task: Task):
        top = height * 4 + 4
        left = column * 15 + 3
        self._draw_square(left, top, 10, 3)
        self._print_xy(left + 1, top + 1, str(task.name))
        self._print_xy(left + 1, top + 2, str(task.time_left))

    def _draw_empty_columns(self, number, height):
        for i in range(1, number):
            self._draw_vertical_line(i * 15, 2, height, '|')

    def _draw_col_title(self, col_number, column: Column):
        self._print_xy(col_number * 15 + 4, 2, column.name)

    def _draw_kpis(self, clock, avg_lead_time, avg_cycle_time, finished_tasks):
        self._print_xy(0, 0, f'Clock: {clock:4d} Lead Time: {avg_lead_time:5.2f} Cycle Time: {avg_cycle_time:5.2f} Finished: {finished_tasks:4d}')

    def _redraw(self):
        print(self._term.home + self._term.clear)
        self._draw_empty_columns(self._stages * 2, 20)
        col_number = 0
        for col in self._columns:
            self._draw_col_title(col_number, col)
            line_number = 0
            for task in col.tasks:
                if line_number < 7:
                    self._draw_task(col_number, line_number, task)
                line_number += 1
            col_number += 1
        self._draw_kpis(self._clock, self._avg_lead_time, self._avg_cycle_time, self._finished_tasks)

    def _can_move_to_next_action(self, col_number):
        # not the last column... check if wip for next stage is ok
        is_next_stage_last = col_number >= len(self._columns) - 3
        if is_next_stage_last:
            # do not consider tasks finished
            num_tasks_next_stage = len(self._columns[col_number + 1].tasks)
        else:
            num_tasks_next_stage = len(self._columns[col_number + 1].tasks) + len(self._columns[col_number + 2].tasks)
        num_tasks_next_action = len(self._columns[col_number + 1].tasks)
        wip_ok = (num_tasks_next_stage < self._wip) or (self._wip == 0)
        move_ok =  wip_ok and (num_tasks_next_action == 0)
        return move_ok

    def _move_task_to_next_action(self, col_number):
        column = self._columns[col_number]
        top_task = column.tasks[0]
        top_task.current_column += 1
        bottleneck_factor = 1.0 if col_number != self._bottleneck_column else self._bottleneck_factor
        top_task.time_left = self._choose_time(bottleneck_factor)
        self._columns[col_number+1].tasks.append(top_task)
        column.tasks.remove(top_task)

    def _tick(self):
        # update tasks on each column in reverse order
        col_number = self._stages * 2 - 1
        while col_number >= 0:
            column = self._columns[col_number]

            is_this_column_empty = len(column.tasks) == 0

            if is_this_column_empty:
                col_number -= 1
                continue

            if column.waiting:
                # this is a waiting column. The next one is an action column
                is_last_column = col_number == len(self._columns) - 1
                if not is_last_column:
                    # not the last column... check if wip for next stage is ok
                    if self._can_move_to_next_action(col_number):
                        self._move_task_to_next_action(col_number)
            else:
                # this is an action column. The next one is a waiting column

                # count time
                column_tasks = column.tasks.copy()
                for task in column.tasks:
                    task.time_left = task.time_left - 1
                    if task.time_left <= 0:

                        # task should move to the next column.. a waiting column
                        task.current_column = task.current_column + 1
                        self._columns[col_number+1].tasks.append(task)
                        column_tasks.remove(task)

                        is_last_action = col_number == len(self._columns) - 2
                        if is_last_action:
                            task.finished = self._clock
                        elif self._can_move_to_next_action(col_number + 1):
                            self._move_task_to_next_action(col_number + 1)
                column.tasks = column_tasks
            col_number -= 1

        self._calculate_cfd()
        self._calculate_lead_time()
        self._calculate_cycle_time()
        self._calculate_finished_tasks()

        first_action_empty = len(self._columns[0].tasks) == 0
        num_tasks_first_stage = len(self._columns[0].tasks) + len(self._columns[1].tasks)
        wip_ok = (num_tasks_first_stage < self._wip) or (self._wip == 0)
        if wip_ok and first_action_empty:
            # create new task
            task = Task(self._gen_task_name(), self._choose_time(1.0), self._clock)
            self._columns[0].tasks.append(task)
            self._tasks.append(task)

if __name__ == "__main__":
    term = blessed.Terminal()
    game = Game(term, 3, 0, 5, 8, 0, 1.5)
    game.start()


