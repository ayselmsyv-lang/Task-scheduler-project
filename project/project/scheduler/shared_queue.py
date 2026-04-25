"""
SharedQueueRuntime — Rejim 1: Tək ümumi növbə.

Bütün N worker eyni thread-safe queue-dan tapşırıq götürür.
Sadə, etibarlı, amma yüksək contention yarada bilər.
"""

import queue
import threading
import time
from scheduler.base import BaseRuntime
from scheduler.task import Task


class SharedQueueRuntime(BaseRuntime):
    """
    Rejim 1: Global Queue

    ┌─────────────────────────┐
    │   [T1][T2][T3][T4][T5] │  ← Global Queue (thread-safe)
    └────────┬────────────────┘
             │  hər worker buradan götürür
      ┌──────┴──────┐
    W0│           W1│  W2  W3  ...
    """

    mode_name = "Shared Queue"

    def __init__(self, num_workers: int):
        super().__init__(num_workers)
        self._queue = queue.Queue()   # Python-un öz thread-safe queue-su

    def submit(self, task: Task) -> None:
        self._queue.put(task)

    def run(self) -> None:
        self._shutdown.clear()
        self.workers = []
        for i in range(self.num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True,
                name=f"SharedWorker-{i}"
            )
            t.start()
            self.workers.append(t)

    def wait_for_completion(self) -> None:
        self._queue.join()          # Bütün task_done() çağırılana qədər blok
        self._shutdown.set()
        for w in self.workers:
            w.join(timeout=2.0)

    def _worker_loop(self, worker_id: int) -> None:
        while not self._shutdown.is_set():
            try:
                task: Task = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue

            # İcra
            task.started_at = time.perf_counter()
            task.worker_id  = worker_id
            time.sleep(task.duration)
            task.finished_at = time.perf_counter()

            self._record_completion(task)
            self._queue.task_done()
