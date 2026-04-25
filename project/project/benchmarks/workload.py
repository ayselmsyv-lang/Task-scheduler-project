"""
workload.py — Test tapşırıqlarını generasiya edir.

Demo üçün müxtəlif iş yükü profilləri.
"""

import random
import time
from typing import List
from scheduler.task import Task


def generate_mixed(
    num_fast: int = 40,
    num_slow: int = 10,
    fast_range: tuple = (0.005, 0.010),
    slow_range: tuple = (0.050, 0.100),
    shuffle: bool = True,
) -> List[Task]:
    """
    Qarışıq iş yükü: sürətli + yavaş tapşırıqlar.
    Work stealing-in effektini ən yaxşı göstərən profil.
    """
    tasks = []
    task_id = 0

    for _ in range(num_fast):
        tasks.append(Task(
            task_id=task_id,
            duration=random.uniform(*fast_range),
        ))
        task_id += 1

    for _ in range(num_slow):
        tasks.append(Task(
            task_id=task_id,
            duration=random.uniform(*slow_range),
        ))
        task_id += 1

    if shuffle:
        random.shuffle(tasks)

    return tasks


def generate_uniform(
    count: int = 50,
    duration: float = 0.020,
    jitter: float = 0.005,
) -> List[Task]:
    """Hamısı təxminən eyni müddətli tapşırıqlar"""
    return [
        Task(task_id=i, duration=max(0.001, duration + random.uniform(-jitter, jitter)))
        for i in range(count)
    ]


def generate_burst(
    count: int = 50,
    fast_ratio: float = 0.9,
) -> List[Task]:
    """Əksəriyyəti çox sürətli, bəziləri çox yavaş (ən pis hal)"""
    tasks = []
    for i in range(count):
        if random.random() < fast_ratio:
            dur = random.uniform(0.001, 0.005)
        else:
            dur = random.uniform(0.100, 0.200)
        tasks.append(Task(task_id=i, duration=dur))
    random.shuffle(tasks)
    return tasks
