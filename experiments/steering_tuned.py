"""How humans steer, at the same attention (~12 answered judgments a day), each
design with its own step / learning rate tuned on separate seeds."""
import sys, json; sys.path.insert(0, '.')
from experiments.run_all import run_jobs, mean, sem, TUNE_SEEDS, TEST_SEEDS, STEPS, LRS
K = 24
CASES = {
    'open forum, multipliers': ('open, multipliers', {}, 'lr', LRS),
    'open forum, multipliers clipped': ('open, multipliers (huber)', {}, 'lr', LRS),
    'open forum, nudges': ('open, nudges', {}, 'step', STEPS),
    'panel, multipliers': ('panel, multipliers', {'invited_per_day': K}, 'lr', LRS),
    'panel, multipliers clipped': ('panel, multipliers', {'invited_per_day': K, 'update': 'huber'}, 'lr', LRS),
    'panel, nudges': ('panel, money-weighted', {'invited_per_day': K}, 'step', STEPS),
    'panel, nudges, flags': ('flag and sample', {'invited_per_day': K}, 'step', STEPS),
}
if __name__ == '__main__':
    lab = sys.argv[1] if len(sys.argv) > 1 else 'base'
    wkw = {'base': {}, 'skewed': dict(top_share=0.15), 'inflated': dict(nudge_inflation=2.7), 'fewblind': dict(blind_frac=0.03)}[lab]
    jobs = [((name, v), wkw, dict(base=b, **extra, **{key: v}), s) for name, (b, extra, key, grid) in CASES.items() for v in grid for s in TUNE_SEEDS]
    t = run_jobs(jobs)
    best = {name: min(grid, key=lambda v: mean(t[(name, v)], 'error')) for name, (b, extra, key, grid) in CASES.items()}
    jobs = [(name, wkw, dict(base=b, **extra, **{key: best[name]}), s) for name, (b, extra, key, grid) in CASES.items() for s in TEST_SEEDS]
    acc = run_jobs(jobs)
    out = {k: {m: [mean(v, m), sem(v, m)] for m in ('error', 'attention', 'capture', 'shortchanged')} | {'param': best[k]} for k, v in acc.items()}
    json.dump(out, open(f'results/steering_tuned_{lab}.json', 'w'), indent=1)
    for k, v in out.items():
        print(f"{k:34s} err={v['error'][0]:.3f}±{v['error'][1]:.3f} att={v['attention'][0]:5.1f} short={v['shortchanged'][0]:.3f} cap={v['capture'][0]:+.3f}±{v['capture'][1]:.3f} param={v['param']}")
