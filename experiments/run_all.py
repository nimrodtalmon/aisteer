"""Runs every experiment of the report and writes results/*.json and figures/*.png.
Usage: python experiments/run_all.py   (about 10-15 minutes on 2 cores)"""
import sys, json, itertools, collections, os
sys.path.insert(0, '.')
from steer.sim import *
from concurrent.futures import ProcessPoolExecutor

os.makedirs('results', exist_ok=True)
TUNE_SEEDS, TEST_SEEDS = range(4), range(100, 112)
STEPS = (0.05, 0.1, 0.2, 0.3, 0.4)
LRS = (0.01, 0.02, 0.05, 0.1)
KS = (2, 5, 10, 20, 40, 80)
PANELS = ['panel, random pairs', 'panel, money-weighted', 'flag and sample', 'flag, sample, escalate']

def job(a):
    tag, wkw, pkw, seed = a
    w = World(**wkw); p = replace(POLICIES[pkw.pop('base')], **pkw)
    r = run(w, p, seed=seed)
    return tag, r

def mean(rs, k): return float(np.mean([r[k] for r in rs]))
def sem(rs, k): return float(np.std([r[k] for r in rs]) / np.sqrt(len(rs)))

def run_jobs(jobs):
    acc = collections.defaultdict(list)
    with ProcessPoolExecutor() as ex:
        for tag, r in ex.map(job, jobs, chunksize=4):
            acc[tag].append(r)
    return acc

def frontier(wkw, label):
    # 1) tune the step per policy and attention level on tuning seeds
    jobs = [((pol, K, st), wkw, dict(base=pol, invited_per_day=K, step=st), s)
            for pol in PANELS for K in KS for st in STEPS for s in TUNE_SEEDS]
    acc = run_jobs(jobs)
    best = {}
    for pol in PANELS:
        for K in KS:
            best[(pol, K)] = min(STEPS, key=lambda st: mean(acc[(pol, K, st)], 'error'))
    # 2) evaluate on fresh seeds
    jobs = [((pol, K), wkw, dict(base=pol, invited_per_day=K, step=best[(pol, K)]), s)
            for pol in PANELS for K in KS for s in TEST_SEEDS]
    jobs += [(('engine only', 0), wkw, dict(base='engine only'), s) for s in TEST_SEEDS]
    # open forums: tune their own parameter too
    for pol, grid, key in (('open, nudges', STEPS, 'step'), ('open, multipliers', LRS, 'lr'),
                           ('open, multipliers (huber)', LRS, 'lr')):
        t = run_jobs([((pol, v), wkw, dict(base=pol, **{key: v}), s) for v in grid for s in TUNE_SEEDS])
        bv = min(grid, key=lambda v: mean(t[(pol, v)], 'error'))
        jobs += [((pol, 0), wkw, dict(base=pol, **{key: bv}), s) for s in TEST_SEEDS]
        best[(pol, 0)] = bv
    acc = run_jobs(jobs)
    out = {f"{k[0]}|{k[1]}": {m: [mean(v, m), sem(v, m)] for m in
           ('error', 'attention', 'capture', 'shortchanged', 'escalations')} for k, v in acc.items()}
    out['best_param'] = {f"{k[0]}|{k[1]}": v for k, v in best.items()}
    json.dump(out, open(f'results/frontier_{label}.json', 'w'), indent=1)
    return out

def steering(wkw, label, K=24):
    """How humans steer, at about the same attention as the open forum."""
    cases = {
        'open forum, multipliers': dict(base='open, multipliers', lr=0.05),
        'open forum, multipliers clipped': dict(base='open, multipliers (huber)', lr=0.05),
        'open forum, nudges': dict(base='open, nudges', step=0.1),
        'panel, multipliers': dict(base='panel, multipliers', invited_per_day=K, lr=0.02),
        'panel, nudges': dict(base='panel, money-weighted', invited_per_day=K, step=0.1),
        'panel, nudges, flags': dict(base='flag and sample', invited_per_day=K, step=0.1),
    }
    jobs = [(name, wkw, dict(kw), s) for name, kw in cases.items() for s in TEST_SEEDS]
    acc = run_jobs(jobs)
    out = {k: {m: [mean(v, m), sem(v, m)] for m in ('error', 'attention', 'capture', 'shortchanged')} for k, v in acc.items()}
    json.dump(out, open(f'results/steering_{label}.json', 'w'), indent=1)
    return out

if __name__ == '__main__':
    which = sys.argv[1:] or ['base', 'skewed', 'inflated', 'fewblind']
    worlds = {'base': {}, 'skewed': dict(top_share=0.15), 'inflated': dict(nudge_inflation=2.7),
              'fewblind': dict(blind_frac=0.03)}
    for lab in which:
        print('==', lab, flush=True)
        frontier(worlds[lab], lab)
        steering(worlds[lab], lab)
