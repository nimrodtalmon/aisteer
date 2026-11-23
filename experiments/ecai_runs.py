"""Experiments for the ECAI paper: frontier with 40 paired seeds, clipped multipliers,
a sweep of the AI's error size, and strategic maintainers under recusal.
Usage: python experiments/ecai_runs.py  -> results/ecai_*.json"""
import sys, json, collections, os
sys.path.insert(0, '.')
from steer.sim import *
from concurrent.futures import ProcessPoolExecutor

TUNE, TEST = list(range(4)), list(range(100, 140))
STEPS = (0.05, 0.1, 0.2, 0.3, 0.4)
LRS = (0.01, 0.02, 0.05, 0.1)
KS = (2, 5, 10, 20, 40, 80)

def job(a):
    tag, wkw, pkw, seed = a
    pkw = dict(pkw); w = World(**wkw); p = replace(POLICIES[pkw.pop('base')], **pkw)
    return tag, seed, run(w, p, seed=seed)

def run_jobs(jobs):
    acc = collections.defaultdict(dict)
    with ProcessPoolExecutor() as ex:
        for tag, seed, r in ex.map(job, jobs, chunksize=8):
            acc[tag][seed] = r
    return acc

def tuned(cases, key_grid):
    """cases: {name: (wkw, pkw)}; key_grid: {name: (key, grid)} -> best value per case."""
    jobs = [((nm, v), wkw, dict(pkw, **{key_grid[nm][0]: v}), s)
            for nm, (wkw, pkw) in cases.items() if nm in key_grid
            for v in key_grid[nm][1] for s in TUNE]
    acc = run_jobs(jobs)
    best = {}
    for nm in cases:
        if nm in key_grid:
            k, g = key_grid[nm]
            best[nm] = min(g, key=lambda v: np.mean([r['error'] for r in acc[(nm, v)].values()]))
    return best

def evaluate(cases, key_grid, label):
    best = tuned(cases, key_grid)
    jobs = []
    for nm, (wkw, pkw) in cases.items():
        pk = dict(pkw)
        if nm in best: pk[key_grid[nm][0]] = best[nm]
        jobs += [(nm, wkw, pk, s) for s in TEST]
    acc = run_jobs(jobs)
    out = {nm: {m: [acc[nm][s][m] for s in TEST] for m in ('error', 'attention', 'capture')}
           for nm in cases}
    out['_best'] = best
    json.dump(out, open(f'results/ecai_{label}.json', 'w'))
    return out

if __name__ == '__main__':
    os.makedirs('results', exist_ok=True)
    which = sys.argv[1:] or ['frontier', 'aisweep', 'sabotage']
    if 'frontier' in which:
        cases, kg = {}, {}
        for pol in ('panel, random pairs', 'panel, money-weighted', 'flag and sample'):
            for K in KS:
                cases[f'{pol}|{K}'] = ({}, dict(base=pol, invited_per_day=K)); kg[f'{pol}|{K}'] = ('step', STEPS)
        cases['engine only'] = ({}, dict(base='engine only'))
        cases['open, nudges'] = ({}, dict(base='open, nudges')); kg['open, nudges'] = ('step', STEPS)
        cases['open, multipliers'] = ({}, dict(base='open, multipliers')); kg['open, multipliers'] = ('lr', LRS)
        cases['open, clipped'] = ({}, dict(base='open, multipliers (huber)')); kg['open, clipped'] = ('lr', LRS)
        cases['panel, multipliers|24'] = ({}, dict(base='panel, multipliers', invited_per_day=24)); kg['panel, multipliers|24'] = ('lr', LRS)
        cases['panel, clipped|24'] = ({}, dict(base='panel, multipliers', invited_per_day=24, update='huber')); kg['panel, clipped|24'] = ('lr', LRS)
        cases['panel, money-weighted|24'] = ({}, dict(base='panel, money-weighted', invited_per_day=24)); kg['panel, money-weighted|24'] = ('step', STEPS)
        cases['flag and sample|24'] = ({}, dict(base='flag and sample', invited_per_day=24)); kg['flag and sample|24'] = ('step', STEPS)
        evaluate(cases, kg, 'frontier'); print('frontier done', flush=True)
    if 'aisweep' in which:
        cases, kg = {}, {}
        for bs in (0.75, 1.5, 2.25):
            cases[f'engine only|{bs}|0'] = (dict(blind_size=bs), dict(base='engine only'))
            for pol in ('panel, money-weighted', 'flag and sample'):
                for K in (10, 24):
                    nm = f'{pol}|{bs}|{K}'
                    cases[nm] = (dict(blind_size=bs), dict(base=pol, invited_per_day=K)); kg[nm] = ('step', STEPS)
        evaluate(cases, kg, 'aisweep'); print('aisweep done', flush=True)
    if 'sabotage' in which:
        cases, kg = {}, {}
        for sab in (False, True):
            for excl in (False, True):
                nm = f'sabotage={sab}|exclude={excl}'
                cases[nm] = (dict(sabotage=sab), dict(base='flag and sample', invited_per_day=24, exclude_maintainers=excl))
                kg[nm] = ('step', STEPS)
        evaluate(cases, kg, 'sabotage'); print('sabotage done', flush=True)

    if 'worlds' in which:
        for label, wkw in (('skewed', dict(top_share=0.15)), ('fewblind', dict(blind_frac=0.03))):
            cases, kg = {}, {}
            for pol in ('panel, random pairs', 'panel, money-weighted', 'flag and sample'):
                for K in KS:
                    cases[f'{pol}|{K}'] = (wkw, dict(base=pol, invited_per_day=K)); kg[f'{pol}|{K}'] = ('step', STEPS)
            cases['engine only'] = (wkw, dict(base='engine only'))
            evaluate(cases, kg, 'world_' + label); print(label, 'done', flush=True)
    if 'belief' in which:
        cases, kg = {}, {}
        for b in (1.0, 1.3, 1.6, 2.0, 2.7):
            wkw = dict(nudge_inflation=b)
            for nm, pk, key, grid in (('flag and sample, 5 a day', dict(base='flag and sample', invited_per_day=10), 'step', STEPS),
                                      ('flag and sample, 12 a day', dict(base='flag and sample', invited_per_day=24), 'step', STEPS),
                                      ('share-weighted, 12 a day', dict(base='panel, money-weighted', invited_per_day=24), 'step', STEPS),
                                      ('open forum, nudges', dict(base='open, nudges'), 'step', STEPS),
                                      ('open forum, multipliers', dict(base='open, multipliers'), 'lr', LRS)):
                cases[f'{nm}|{b}'] = (wkw, pk); kg[f'{nm}|{b}'] = (key, grid)
            cases[f'AI alone|{b}'] = (wkw, dict(base='engine only'))
        evaluate(cases, kg, 'belief'); print('belief done', flush=True)
    if 'tuning' in which:
        cases, kg = {}, {}
        for e in (0.0, 0.5, 0.75, 1.0):
            nm = f'exp={e}'; cases[nm] = ({}, dict(base='panel, money-weighted', invited_per_day=24, money_exp=e)); kg[nm] = ('step', STEPS)
        for f in (0.0, 0.25, 0.5, 0.75, 0.9):
            nm = f'mix={f}'; cases[nm] = ({}, dict(base='flag and sample', invited_per_day=24, flag_mix=f)); kg[nm] = ('step', STEPS)
        evaluate(cases, kg, 'tuning'); print('tuning done', flush=True)
