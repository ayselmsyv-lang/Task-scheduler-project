"""
Task — hər iki rejimdə istifadə olunan ortaq tapşırıq sinfi.
"""

import time as _time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    task_id: int
    duration: float                  # saniyə — işin uzunluğu
    submitted_at: float = field(default_factory=_time.perf_counter)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    worker_id: Optional[int] = None
    stolen: bool = False             # Work stealing rejimində oğurlanıbmı?

    @property
    def wait_time(self) -> Optional[float]:
        """Növbədə gözləmə vaxtı (saniyə)"""
        if self.started_at is not None:
            return self.started_at - self.submitted_at
        return None

    @property
    def execution_time(self) -> Optional[float]:
        """Faktiki icra vaxtı (saniyə)"""
        if self.started_at is not None and self.finished_at is not None:
            return self.finished_at - self.started_at
        return None

    @property
    def total_time(self) -> Optional[float]:
        """Submit-dən finish-ə qədər ümumi vaxt (saniyə)"""
        if self.finished_at is not None:
            return self.finished_at - self.submitted_at
        return None

    def __repr__(self):
        status = "done" if self.finished_at else "pending"
        return f"Task(id={self.task_id}, dur={self.duration*1000:.1f}ms, status={status})"
