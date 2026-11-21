"""How much attention should follow flags? Sweep flag_mix in the GG24 world.

    python3 experiments/mix_exp.py   -> results/mix_exp.json
"""
import sys, json
sys.path.insert(0, '.')
from experiments.run_all import run_jobs, mean, sem, TUNE_SEEDS, TEST_SEEDS, STEPS

MIXES = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9)
if __name__ == '__main__':
    out = {}
    for K in (2, 10, 24, 48):
        jobs = [((f, st), {}, dict(base='flag and sample', invited_per_day=K, flag_mix=f, step=st), s)
                for f in MIXES for st in STEPS for s in TUNE_SEEDS]
        t = run_jobs(jobs)
        best = {f: min(STEPS, key=lambda v: mean(t[(f, v)], 'error')) for f in MIXES}
        acc = run_jobs([(f, {}, dict(base='flag and sample', invited_per_day=K, flag_mix=f, step=best[f]), s)
                        for f in MIXES for s in TEST_SEEDS])
        for f in MIXES:
            out[f'{K}|{f}'] = dict(error=[mean(acc[f], 'error'), sem(acc[f], 'error')], step=best[f],
                                   attention=mean(acc[f], 'attention'))
            print(K, f, best[f], round(mean(acc[f], 'error') * 100, 2), '±', round(sem(acc[f], 'error') * 100, 2), flush=True)
    json.dump(out, open('results/mix_exp.json', 'w'), indent=1)
