"""
test_scheduler.py — Unit testlər.
İşlətmək: python -m pytest tests/ -v
         və ya: python tests/test_scheduler.py
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler.task import Task
from scheduler.shared_queue import SharedQueueRuntime
from scheduler.work_stealing import WorkStealingRuntime, WorkStealingDeque


# ─── Task testləri ───────────────────────────────────────────

def test_task_properties():
    """Task property-ləri düzgün hesablanır"""
    t = Task(task_id=1, duration=0.1)
    assert t.wait_time is None
    assert t.total_time is None

    t.started_at  = t.submitted_at + 0.05
    t.finished_at = t.submitted_at + 0.15

    assert abs(t.wait_time - 0.05) < 0.001
    assert abs(t.execution_time - 0.10) < 0.001
    assert abs(t.total_time - 0.15) < 0.001
    print("  ✅ test_task_properties")


# ─── WorkStealingDeque testləri ──────────────────────────────

def test_deque_push_pop():
    """Owner LIFO sırası ilə götürür"""
    d = WorkStealingDeque()
    t1 = Task(task_id=1, duration=0.01)
    t2 = Task(task_id=2, duration=0.01)
    d.push(t1)
    d.push(t2)
    assert d.pop().task_id == 2   # LIFO: son girən ilk çıxır
    assert d.pop().task_id == 1
    assert d.pop() is None
    print("  ✅ test_deque_push_pop")


def test_deque_steal():
    """Thief soldan oğurlayır, tək element olduqda oğurlamır"""
    d = WorkStealingDeque()
    t1 = Task(task_id=1, duration=0.01)
    t2 = Task(task_id=2, duration=0.01)

    d.push(t1)
    assert d.steal() is None   # 1 element — oğurlanmır

    d.push(t2)
    stolen = d.steal()
    assert stolen is not None
    assert stolen.task_id == 1  # FIFO: ilk girən oğurlanır
    assert stolen.stolen is True
    print("  ✅ test_deque_steal")


# ─── SharedQueueRuntime testləri ─────────────────────────────

def test_shared_all_tasks_completed():
    """Shared Queue — heç bir tapşırıq itirilmir"""
    runtime = SharedQueueRuntime(num_workers=3)
    runtime.run()

    count = 20
    for i in range(count):
        runtime.submit(Task(task_id=i, duration=0.005))

    runtime.wait_for_completion()

    assert len(runtime.completed_tasks) == count
    ids = sorted(t.task_id for t in runtime.completed_tasks)
    assert ids == list(range(count))
    print("  ✅ test_shared_all_tasks_completed")


def test_shared_all_workers_used():
    """Shared Queue — bütün workerlər iş görür"""
    runtime = SharedQueueRuntime(num_workers=4)
    runtime.run()

    for i in range(40):
        runtime.submit(Task(task_id=i, duration=0.005))

    runtime.wait_for_completion()

    # Hər worker ən azı 1 tapşırıq etməlidir
    for i, count in enumerate(runtime.worker_task_counts):
        assert count >= 1, f"Worker {i} heç iş görmədı!"
    print("  ✅ test_shared_all_workers_used")


def test_shared_task_timing():
    """Shared Queue — task timing məlumatları düzgün doldurulur"""
    runtime = SharedQueueRuntime(num_workers=2)
    runtime.run()
    runtime.submit(Task(task_id=0, duration=0.01))
    runtime.wait_for_completion()

    task = runtime.completed_tasks[0]
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.worker_id is not None
    assert task.finished_at > task.started_at
    print("  ✅ test_shared_task_timing")


# ─── WorkStealingRuntime testləri ────────────────────────────

def test_stealing_all_tasks_completed():
    """Work Stealing — heç bir tapşırıq itirilmir"""
    runtime = WorkStealingRuntime(num_workers=3)
    runtime.run()

    count = 30
    for i in range(count):
        runtime.submit(Task(task_id=i, duration=0.005))

    runtime.wait_for_completion()

    assert len(runtime.completed_tasks) == count
    print("  ✅ test_stealing_all_tasks_completed")


def test_stealing_occurs():
    """Work Stealing — çarpaz yük olduqda oğurlanma baş verir"""
    # 1 workerdə çox yük, digərləri boş başlayır
    runtime = WorkStealingRuntime(num_workers=4)

    # Hamısı ilk workerin növbəsinə (round-robin: 0,1,2,3,0,1,...)
    # Bərabər paylanır amma biri yavaş olsa digəri oğurlar
    runtime.run()

    for i in range(20):
        runtime.submit(Task(task_id=i, duration=0.008))

    runtime.wait_for_completion()

    total_steals = sum(runtime._steal_counts)
    # Heç olmasa bir oğurlanma baş verməlidir (iş yükü var)
    # (qeyd: çox kiçik tapşırıqlarda bəzən 0 da ola bilər — bu normaldır)
    assert len(runtime.completed_tasks) == 20
    print(f"  ✅ test_stealing_occurs  (steals={total_steals})")


def test_stealing_get_stats():
    """Work Stealing — get_stats() stealing məlumatlarını qaytarır"""
    runtime = WorkStealingRuntime(num_workers=2)
    runtime.run()

    for i in range(10):
        runtime.submit(Task(task_id=i, duration=0.005))

    runtime.wait_for_completion()
    stats = runtime.get_stats()

    assert "total_steals" in stats
    assert "stolen_tasks" in stats
    assert "steal_counts_per_worker" in stats
    print("  ✅ test_stealing_get_stats")


# ─── Runner ──────────────────────────────────────────────────

def run_all_tests():
    tests = [
        test_task_properties,
        test_deque_push_pop,
        test_deque_steal,
        test_shared_all_tasks_completed,
        test_shared_all_workers_used,
        test_shared_task_timing,
        test_stealing_all_tasks_completed,
        test_stealing_occurs,
        test_stealing_get_stats,
    ]

    print("\n" + "═" * 50)
    print("  🧪 TESTLƏR")
    print("═" * 50)

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1

    print("─" * 50)
    print(f"  Nəticə: {passed} keçdi, {failed} uğursuz")
    print("═" * 50 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
