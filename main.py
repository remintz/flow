
import time
from typing import List
from dataclasses import dataclass
import random

import blessed

@dataclass
class Task:
    name: str
    time_left: int
    current_column: int
    waiting: bool
    finished: bool

@dataclass
class Column:
    name: str
    waiting: bool
    number: int
    tasks: List[Task]

class Game:
    def __init__(self, terminal, stages, cycle_time, min_time, max_time):
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

        col_number = 0
        for i in range(stages):

            column = Column(f'DOING {i}', False, col_number, [])
            self._columns.append(column)
            col_number += 1

            column = Column(f'DONE {i}', True, col_number, [])
            self._columns.append(column)
            col_number += 1

    def start(self):
        self._running = True
        while self._running:
            self._wait()
            self._tick()
            self._redraw()

    def _gen_task_name(self):
        self._number_of_tasks += 1
        return f'TASK #{self._number_of_tasks}'

    def _wait(self):
        if self._cycle_time > 0:
            time.sleep(self._cycle_time)
        else:
            self._print_xy(0, 30, '')
            input('->')

    def _choose_time(self):
        if self._min_time == self._max_time:
            return self._min_time
        else:
            return random.randrange(self._min_time, self._max_time)

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

    def _draw_vertical_line(self, column, height, char):
        for i in range(height):
            print(self._term.move_xy(column, i) + char)

    def _draw_task(self, column, height, task: Task):
        top = height * 4 + 2
        left = column * 15 + 3
        self._draw_square(left, top, 10, 3)
        self._print_xy(left + 1, top + 1, str(task.name))
        self._print_xy(left + 1, top + 2, str(task.time_left))

    def _draw_empty_columns(self, number, height):
        for i in range(1, number):
            self._draw_vertical_line(i * 15, height, '|')

    def _draw_col_title(self, col_number, column: Column):
        self._print_xy(col_number * 15 + 4, 0, column.name)

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

    def _tick(self):
        # update tasks on each column in reverse order
        col_number = self._stages * 2 - 1
        while col_number >= 0:
            column = self._columns[col_number]

            is_this_column_empty = len(column.tasks) == 0

            if column.waiting:
                # this is a waiting column. The next one is an action column
                if col_number < len(self._columns)-1:

                    # not the last column... check if the next column - action column - is empty
                    is_next_column_empty = len(self._columns[col_number+1].tasks) == 0
                    if  is_next_column_empty and not is_this_column_empty:
                        top_task = column.tasks[0]
                        top_task.current_column += 1
                        top_task.time_left = self._choose_time()
                        self._columns[col_number+1].tasks.append(top_task)
                        column.tasks.remove(top_task)
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
                column.tasks = column_tasks
            col_number -= 1

        first_column = self._columns[0]
        if len(first_column.tasks) == 0:
            # create new task
            task = Task(self._gen_task_name(), self._choose_time(), 0, False, False)
            first_column.tasks.append(task)

if __name__ == "__main__":
    term = blessed.Terminal()
    game = Game(term, 3, 0, 2, 15)
    game.start()


