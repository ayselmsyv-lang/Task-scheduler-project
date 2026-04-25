"""
BaseRuntime — hər iki rejimin ortaq məntiqi.
SharedQueueRuntime və WorkStealingRuntime bu sinifdən miras alır.
"""

import threading
import statistics
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from scheduler.task import Task


class BaseRuntime(ABC):
    """
    Soyut əsas sinif.
    Alt siniflər: submit(), run(), wait_for_completion() implement etməlidir.
    get_stats() isə burada — hər ikisi üçün eynidir.
    """

    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.completed_tasks: List[Task] = []
        self.worker_task_counts: List[int] = [0] * num_workers
        self._lock = threading.Lock()
        self._shutdown = threading.Event()
        self.workers: List[threading.Thread] = []

    @abstractmethod
    def submit(self, task: Task) -> None:
        """Növbəyə tapşırıq əlavə et"""
        ...

    @abstractmethod
    def run(self) -> None:
        """Worker thread-ləri başlat"""
        ...

    @abstractmethod
    def wait_for_completion(self) -> None:
        """Bütün tapşırıqlar bitənə qədər gözlə, sonra shutdown et"""
        ...

    def _record_completion(self, task: Task) -> None:
        """Tamamlanan tapşırığı thread-safe şəkildə qeyd et"""
        with self._lock:
            self.completed_tasks.append(task)
            if task.worker_id is not None:
                self.worker_task_counts[task.worker_id] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Benchmark statistikası — hər iki rejim üçün eyni hesablama.
        Alt siniflər öz əlavə statistikalarını üstünə yazır (super() ilə).
        """
        if not self.completed_tasks:
            return {"mode": self.mode_name, "total_tasks": 0}

        wait_times  = [t.wait_time  for t in self.completed_tasks if t.wait_time  is not None]
        total_times = [t.total_time for t in self.completed_tasks if t.total_time is not None]

        sorted_total = sorted(total_times)
        p99_idx = max(0, int(len(sorted_total) * 0.99) - 1)

        fairness_std = (
            statistics.stdev(self.worker_task_counts)
            if len(self.worker_task_counts) > 1 else 0.0
        )

        return {
            "mode":               self.mode_name,
            "total_tasks":        len(self.completed_tasks),
            "avg_wait_ms":        statistics.mean(wait_times)  * 1000 if wait_times  else 0,
            "avg_total_ms":       statistics.mean(total_times) * 1000 if total_times else 0,
            "tail_latency_p99_ms": sorted_total[p99_idx] * 1000 if sorted_total else 0,
            "fairness_std":       fairness_std,
            "worker_task_counts": self.worker_task_counts[:],
        }

    @property
    def mode_name(self) -> str:
        return self.__class__.__name__
