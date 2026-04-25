"""
main.py — Tək giriş nöqtəsi.

İstifadə:
  python main.py                  # Default demo (mixed workload)
  python main.py --workload mixed
  python main.py --workload uniform
  python main.py --workload burst
  python main.py --workers 4 --fast 40 --slow 10
  python main.py --test           # Testləri işlət
"""

import sys
import os
import argparse

# Project root-u path-ə əlavə et
sys.path.insert(0, os.path.dirname(__file__))

from benchmarks.workload import generate_mixed, generate_uniform, generate_burst
from benchmarks.benchmark import compare, print_report


def main():
    parser = argparse.ArgumentParser(
        description="Task Scheduler — Work Stealing Demo"
    )
    parser.add_argument("--workload", choices=["mixed", "uniform", "burst"],
                        default="mixed", help="İş yükü profili")
    parser.add_argument("--workers", type=int, default=4,
                        help="Worker thread sayı")
    parser.add_argument("--fast", type=int, default=40,
                        help="Sürətli tapşırıq sayı (mixed üçün)")
    parser.add_argument("--slow", type=int, default=10,
                        help="Yavaş tapşırıq sayı (mixed üçün)")
    parser.add_argument("--test", action="store_true",
                        help="Unit testləri işlət")
    args = parser.parse_args()

    if args.test:
        from tests.test_scheduler import run_all_tests
        success = run_all_tests()
        sys.exit(0 if success else 1)

    # İş yükünü seç
    print("\n" + "═" * 62)
    print("  🚀 Task Scheduler — Work Stealing Müqayisəsi")
    print("═" * 62)

    if args.workload == "mixed":
        tasks = generate_mixed(num_fast=args.fast, num_slow=args.slow)
        profile = f"Qarışıq ({args.fast} sürətli + {args.slow} yavaş tapşırıq)"
    elif args.workload == "uniform":
        tasks = generate_uniform(count=args.fast + args.slow)
        profile = f"Bərabər ({args.fast + args.slow} tapşırıq, ~20ms)"
    else:
        tasks = generate_burst(count=args.fast + args.slow)
        profile = f"Burst ({args.fast + args.slow} tapşırıq, %90 sürətli)"

    print(f"\n  İş yükü  : {profile}")
    print(f"  Workerlər: {args.workers}")
    print(f"  Tapşırıq : {len(tasks)}\n")

    result = compare(tasks, num_workers=args.workers)
    print_report(result)


if __name__ == "__main__":
    main()
