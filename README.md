# Project 9: Task Scheduler with Work Stealing

Two-mode concurrent task scheduler with Python.

## Structure

```
project/
├── scheduler/
│ ├── task.py # Task dataclass (shared)
│ ├── base.py # BaseRuntime (abstract class)
│ ├── shared_queue.py # Mode 1: Single shared queue
│ └── work_stealing.py # Mode 2: Per-worker + stealing
├── benchmarks/
│ ├── workload.py # Test task generator
│ └── benchmark.py # Benchmarking and comparison
├── tests/
│ └── test_scheduler.py # Unit tests
├── main.py # Entry point
└── README.md
```

## Run

```bash
# Default demo (mixed workload, 4 workers)
python main.py

# Different workloads
python main.py --workload mixed # Fast + slow tasks
python main.py --workload uniform # All with the same duration
python main.py --workload burst # Most are very fast

# Change parameters
python main.py --workers 8 --fast 80 --slow 20

# Tests
python main.py --test
python -m pytest tests/ -v
```

## Architecture

### Mode 1: Shared Queue
```
[T1, T2, T3, T4, T5] ← Global Queue
↓ ↓ ↓ ↓
W0 W1 W2 W3 ← Everyone looks at the same place
```
- **Advantage**: Simple, automatic load balancing
- **Disadvantage**: High contention (mutex contention)

### Mode 2: Work Stealing
```
W0:[T1,T2] W1:[T3,T4] W2:[] W3:[T5]
↑
Steals T3 from W1
```
- **Advantage**: Low contention, fairer workload distribution
- **Mechanism**: Idle worker → takes from the left end of someone else's queue

## Result

Work Stealing mode:
- **~1.3x faster** (on mixed workload)
- **Fairer** worker distribution (low fairness std)
- **Tail latency** reduced (slow tasks are distributed)
