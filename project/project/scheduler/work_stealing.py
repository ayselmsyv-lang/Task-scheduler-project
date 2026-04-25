"""
WorkStealingRuntime — Rejim 2: Per-worker deque + work stealing.

Hər workerin öz ikitərəfli növbəsi (deque) var.
Boş qalan worker başqa workerin növbəsindən tapşırıq "oğurlayır".
"""

import threading
import time
import random
from collections import deque
from typing import Optional, List
from scheduler.base import BaseRuntime
from scheduler.task import Task


class WorkStealingDeque:
    """
    İkitərəfli növbə (Double-Ended Queue).

    Owner → sağdan götürür  (LIFO — cache locality üçün yaxşı)
    Thief → soldan oğurlayır (FIFO — iri tapşırıqları götürür)

    ←── steal()        push()/pop() ──→
    [T1  T2  T3  T4  T5]
    """

    def __init__(self):
        self._deque: deque = deque()
        self._lock = threading.Lock()

    def push(self, task: Task) -> None:
        """Owner sağdan əlavə edir"""
        with self._lock:
            self._deque.append(task)

    def pop(self) -> Optional[Task]:
        """Owner sağdan götürür (LIFO)"""
        with self._lock:
            return self._deque.pop() if self._deque else None

    def steal(self) -> Optional[Task]:
        """Thief soldan oğurlayır (FIFO) — ən azı 2 element olmalıdır"""
        with self._lock:
            if len(self._deque) > 1:
                task = self._deque.popleft()
                task.stolen = True
                return task
            return None

    def __len__(self) -> int:
        with self._lock:
            return len(self._deque)


class WorkStealingRuntime(BaseRuntime):
    """
    Rejim 2: Per-worker deque + work stealing

    W0:[T1,T2]   W1:[T3,T4]   W2:[]   W3:[T5]
                                 ↑
                         W1-dən T3-ü oğurlayır
    """

    mode_name = "Work Stealing"

    def __init__(self, num_workers: int):
        super().__init__(num_workers)
        self._deques: List[WorkStealingDeque] = [
            WorkStealingDeque() for _ in range(num_workers)
        ]
        self._steal_counts: List[int] = [0] * num_workers
        self._total_submitted = 0
        self._submit_lock = threading.Lock()
        self._next_worker = 0   # Round-robin submit üçün

    def submit(self, task: Task) -> None:
        """Round-robin ilə worker-lərə paylayır"""
        with self._submit_lock:
            idx = self._next_worker % self.num_workers
            self._next_worker += 1
            self._total_submitted += 1
        self._deques[idx].push(task)

    def run(self) -> None:
        self._shutdown.clear()
        self.workers = []
        for i in range(self.num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True,
                name=f"StealWorker-{i}"
            )
            t.start()
            self.workers.append(t)

    def wait_for_completion(self) -> None:
        """Bütün tapşırıqlar tamamlanana qədər poll et"""
        while True:
            with self._lock:
                done = len(self.completed_tasks)
            if done >= self._total_submitted:
                break
            time.sleep(0.005)
        self._shutdown.set()
        for w in self.workers:
            w.join(timeout=2.0)

    def _worker_loop(self, worker_id: int) -> None:
        idle_spins = 0

        while not self._shutdown.is_set():
            task: Optional[Task] = None

            # 1. Öz növbəsindən götür
            task = self._deques[worker_id].pop()

            # 2. Boşdursa — başqasından oğurla
            if task is None:
                victims = list(range(self.num_workers))
                victims.remove(worker_id)
                random.shuffle(victims)
                for v in victims:
                    task = self._deques[v].steal()
                    if task:
                        self._steal_counts[worker_id] += 1
                        break

            # 3. Hər yerdə boşdursa — gözlə
            if task is None:
                idle_spins += 1
                if idle_spins > 200:
                    time.sleep(0.001)
                continue

            idle_spins = 0

            # İcra
            task.started_at  = time.perf_counter()
            task.worker_id   = worker_id
            time.sleep(task.duration)
            task.finished_at = time.perf_counter()

            self._record_completion(task)

    def get_stats(self) -> dict:
        """Əsas statistikaya work stealing xüsusi məlumatlarını əlavə et"""
        stats = super().get_stats()
        stats.update({
            "total_steals":           sum(self._steal_counts),
            "steal_counts_per_worker": self._steal_counts[:],
            "stolen_tasks":           sum(1 for t in self.completed_tasks if t.stolen),
        })
        return stats
