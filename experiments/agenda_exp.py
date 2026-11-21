"""Where to spend attention. Theory (Theorem 5): ask about project j at a rate
proportional to (share_j * sqrt(vol_j / dens))^(4/5) when tracking drift, and about
share_j^(3/4) for fixed errors. Here: the GG24 world, weighting pairs by share**exp.

    python3 experiments/agenda_exp.py   -> results/agenda_exp.json
"""
import sys, json
sys.path.insert(0, '.')
from experiments.run_all import run_jobs, mean, sem, TUNE_SEEDS, TEST_SEEDS, STEPS

EXPS = (0.0, 0.5, 0.75, 1.0)
if __name__ == '__main__':
    out = {}
    for base in ('panel, money-weighted', 'flag and sample'):
        for K in (10, 24, 48):
            jobs = [((e, st), {}, dict(base=base, invited_per_day=K, money_exp=e, step=st), s)
                    for e in EXPS for st in STEPS for s in TUNE_SEEDS]
            t = run_jobs(jobs)
            for e in EXPS:
                st = min(STEPS, key=lambda v: mean(t[(e, v)], 'error'))
                acc = run_jobs([(e, {}, dict(base=base, invited_per_day=K, money_exp=e, step=st), s) for s in TEST_SEEDS])
                v = acc[e]
                out[f'{base}|{K}|{e}'] = {m: [mean(v, m), sem(v, m)] for m in ('error', 'attention')}
                out[f'{base}|{K}|{e}']['step'] = st
                print(base, K, e, st, round(mean(v, 'error') * 100, 2), '±', round(sem(v, 'error') * 100, 2), flush=True)
    json.dump(out, open('results/agenda_exp.json', 'w'), indent=1)
