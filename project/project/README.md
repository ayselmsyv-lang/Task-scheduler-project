# Project 9: Task Scheduler with Work Stealing

Python ilə iki rejimli concurrent task scheduler.

## Struktur

```
project/
├── scheduler/
│   ├── task.py           # Task dataclass (ortaq)
│   ├── base.py           # BaseRuntime (soyut sinif)
│   ├── shared_queue.py   # Rejim 1: Tək ümumi növbə
│   └── work_stealing.py  # Rejim 2: Per-worker + stealing
├── benchmarks/
│   ├── workload.py       # Test tapşırıqları generatoru
│   └── benchmark.py      # Ölçmə və müqayisə
├── tests/
│   └── test_scheduler.py # Unit testlər
├── main.py               # Giriş nöqtəsi
└── README.md
```

## İşlətmə

```bash
# Default demo (mixed workload, 4 worker)
python main.py

# Müxtəlif iş yükləri
python main.py --workload mixed    # Sürətli + yavaş tapşırıqlar
python main.py --workload uniform  # Hamısı eyni müddətli
python main.py --workload burst    # Əksəriyyəti çox sürətli

# Parametrləri dəyiş
python main.py --workers 8 --fast 80 --slow 20

# Testlər
python main.py --test
python -m pytest tests/ -v
```

## Arxitektura

### Rejim 1: Shared Queue
```
[T1, T2, T3, T4, T5]  ← Global Queue
      ↓  ↓  ↓  ↓
    W0 W1 W2 W3        ← Hamı eyni yerə baxır
```
- **Üstünlük**: Sadə, avtomatik yük balansı
- **Çatışmazlıq**: Yüksək contention (mutex rəqabəti)

### Rejim 2: Work Stealing
```
W0:[T1,T2]  W1:[T3,T4]  W2:[]  W3:[T5]
                           ↑
                    T3-ü W1-dən oğurlayır
```
- **Üstünlük**: Az contention, daha ədalətli yük bölgüsü
- **Mexanizm**: Boş worker → başqasının növbəsindən sol ucdan götürür

## Nəticə

Work Stealing rejimi:
- **~1.3x daha sürətli** (qarışıq iş yükündə)
- **Daha ədalətli** worker bölgüsü (aşağı fairness std)
- **Tail latency** azalır (yavaş tapşırıqlar paylanır)
