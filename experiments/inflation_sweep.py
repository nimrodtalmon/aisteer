"""Two kinds of exaggeration. The round shows typed multipliers inflated by 2.7.
Part of it may sit in beliefs (b) and the rest in typing (2.7 / b): directions
(nudges) see only b, typed multipliers see all 2.7. Sweep b from 1 (typing only)
to 2.7 (beliefs only); each mechanism keeps its own tuned step.

    python3 experiments/inflation_sweep.py   -> results/inflation_sweep.json
"""
import sys, json
sys.path.insert(0, '.')
from experiments.run_all import run_jobs, mean, sem, TUNE_SEEDS, TEST_SEEDS, STEPS, LRS

BELIEF = (1.0, 1.3, 1.6, 2.0, 2.7)
CASES = {
    'flag and sample, 5 a day': ('flag and sample', {'invited_per_day': 10}, 'step', STEPS),
    'flag and sample, 12 a day': ('flag and sample', {'invited_per_day': 24}, 'step', STEPS),
    'share-weighted, 12 a day': ('panel, money-weighted', {'invited_per_day': 24}, 'step', STEPS),
    'open forum, nudges': ('open, nudges', {}, 'step', STEPS),
    'open forum, multipliers': ('open, multipliers', {}, 'lr', LRS),
}

if __name__ == '__main__':
    out = {}
    for b in BELIEF:
        wkw = dict(nudge_inflation=b)
        jobs = [((name, v), wkw, dict(base=base, **extra, **{key: v}), s)
                for name, (base, extra, key, grid) in CASES.items() for v in grid for s in TUNE_SEEDS]
        t = run_jobs(jobs)
        best = {name: min(grid, key=lambda v: mean(t[(name, v)], 'error')) for name, (base, extra, key, grid) in CASES.items()}
        jobs = [(name, wkw, dict(base=base, **extra, **{key: best[name]}), s)
                for name, (base, extra, key, grid) in CASES.items() for s in TEST_SEEDS]
        jobs += [('AI alone', wkw, dict(base='engine only'), s) for s in TEST_SEEDS]
        acc = run_jobs(jobs)
        out[str(b)] = {k: {m: [mean(v, m), sem(v, m)] for m in ('error', 'attention', 'capture')} for k, v in acc.items()}
        print(b, {k: round(v['error'][0] * 100, 1) for k, v in out[str(b)].items()}, flush=True)
    json.dump(out, open('results/inflation_sweep.json', 'w'), indent=1)
