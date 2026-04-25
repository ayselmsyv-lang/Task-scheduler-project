"""
benchmark.py — İki rejimi ölçür və müqayisə edir.
"""

import time
import copy
from typing import List, Dict, Any
from scheduler.task import Task
from scheduler.shared_queue import SharedQueueRuntime
from scheduler.work_stealing import WorkStealingRuntime


def run_shared_queue(tasks: List[Task], num_workers: int) -> Dict[str, Any]:
    """Shared Queue rejimini işlət, statistika qaytar"""
    # Hər run üçün təzə Task nüsxələri (submitted_at sıfırlanır)
    fresh_tasks = [Task(task_id=t.task_id, duration=t.duration) for t in tasks]

    runtime = SharedQueueRuntime(num_workers=num_workers)
    runtime.run()

    wall_start = time.perf_counter()
    for task in fresh_tasks:
        runtime.submit(task)
    runtime.wait_for_completion()
    wall_time = time.perf_counter() - wall_start

    stats = runtime.get_stats()
    stats["wall_time_s"] = wall_time
    return stats


def run_work_stealing(tasks: List[Task], num_workers: int) -> Dict[str, Any]:
    """Work Stealing rejimini işlət, statistika qaytar"""
    fresh_tasks = [Task(task_id=t.task_id, duration=t.duration) for t in tasks]

    runtime = WorkStealingRuntime(num_workers=num_workers)
    runtime.run()

    wall_start = time.perf_counter()
    for task in fresh_tasks:
        runtime.submit(task)
    runtime.wait_for_completion()
    wall_time = time.perf_counter() - wall_start

    stats = runtime.get_stats()
    stats["wall_time_s"] = wall_time
    return stats


def compare(tasks: List[Task], num_workers: int) -> Dict[str, Any]:
    """
    Hər iki rejimi eyni tapşırıqlarla işlət və nəticəni müqayisə et.
    Qaytarır: {'shared': {...}, 'stealing': {...}, 'comparison': {...}}
    """
    print(f"  ▶ Shared Queue işlədilir...", end=" ", flush=True)
    sq_stats = run_shared_queue(tasks, num_workers)
    print(f"✓  ({sq_stats['wall_time_s']:.3f}s)")

    print(f"  ▶ Work Stealing işlədilir...", end=" ", flush=True)
    ws_stats = run_work_stealing(tasks, num_workers)
    print(f"✓  ({ws_stats['wall_time_s']:.3f}s)")

    speedup = sq_stats["wall_time_s"] / ws_stats["wall_time_s"] if ws_stats["wall_time_s"] > 0 else 1.0
    fairness_delta = sq_stats["fairness_std"] - ws_stats["fairness_std"]

    comparison = {
        "speedup":          speedup,
        "faster_mode":      "Work Stealing" if speedup > 1 else "Shared Queue",
        "fairness_delta":   fairness_delta,
        "fairer_mode":      "Work Stealing" if fairness_delta > 0 else "Shared Queue",
    }

    return {
        "shared":     sq_stats,
        "stealing":   ws_stats,
        "comparison": comparison,
    }


def print_report(result: Dict[str, Any]) -> None:
    """Nəticələri gözəl formatda çap et"""

    SEP  = "═" * 62
    SEP2 = "─" * 62

    def bar(count, max_count, width=20):
        filled = int(width * count / max_count) if max_count else 0
        return "█" * filled + "░" * (width - filled)

    def print_mode_stats(stats: dict):
        mx = max(stats["worker_task_counts"]) or 1
        print(f"    Tamamlanan      : {stats['total_tasks']}")
        print(f"    Orta gözləmə    : {stats['avg_wait_ms']:.1f} ms")
        print(f"    Orta ümumi vaxt : {stats['avg_total_ms']:.1f} ms")
        print(f"    Tail latency p99: {stats['tail_latency_p99_ms']:.1f} ms")
        print(f"    Fairness (std)  : {stats['fairness_std']:.2f}")
        print(f"    Ümumi vaxt      : {stats['wall_time_s']:.3f} s")
        print(f"    Worker bölgüsü:")
        for i, c in enumerate(stats["worker_task_counts"]):
            print(f"      W{i}: {bar(c, mx)} {c:3d}")
        if "total_steals" in stats:
            print(f"    Oğurlanma sayı  : {stats['total_steals']}")
            print(f"    Oğurlanan task  : {stats['stolen_tasks']}")

    cmp = result["comparison"]

    print(f"\n{SEP}")
    print(f"  📊 BENCHMARK NƏTİCƏLƏRİ")
    print(f"{SEP}")

    print(f"\n{SEP2}")
    print(f"  REJİM 1 — Shared Queue")
    print(f"{SEP2}")
    print_mode_stats(result["shared"])

    print(f"\n{SEP2}")
    print(f"  REJİM 2 — Work Stealing")
    print(f"{SEP2}")
    print_mode_stats(result["stealing"])

    print(f"\n{SEP}")
    print(f"  📈 MÜQAYİSƏ")
    print(f"{SEP}")

    spd = cmp["speedup"]
    if spd > 1:
        print(f"  Sürət      : Work Stealing {spd:.2f}x daha sürətli ✅")
    else:
        print(f"  Sürət      : Shared Queue {1/spd:.2f}x daha sürətli")

    fd = cmp["fairness_delta"]
    if fd > 0:
        print(f"  Ədalətlik  : Work Stealing {fd:.2f} std daha ədalətli ✅")
    else:
        print(f"  Ədalətlik  : Shared Queue daha ədalətli")

    print(f"{SEP}\n")
