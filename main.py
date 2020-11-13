
import time
from typing import List
from dataclasses import dataclass


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
    def __init__(self, stages, cycle_time):
        self._tasks = []
        self._cycle_time = cycle_time
        self._running = False
        self._columns: List[Column] = []
        self._stages = stages

        col_number = 0
        for i in range(stages):

            column = Column('A', False, col_number, [])
            self._columns.append(column)
            col_number += 1

            column = Column('A', True, col_number, [])
            self._columns.append(column)
            col_number += 1


    def start(self):
        self._running = True
        while self._running:
            time.sleep(self._cycle_time)
            self._tick()

    def _choose_time(self):
        return 5

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
            task = Task('A', self._choose_time(), 0, False, False)
            first_column.tasks.append(task)

if __name__ == "__main__":
    game = Game(2, 1)
    game.start()


