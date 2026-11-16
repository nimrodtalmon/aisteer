"""Build the data files used by the simulation and the app from the public
GG24 Deep Funding artifacts (davidgasquez/gg24-deepfunding-market-weights, phase 2):
98 repositories, and 41,418 pairwise comparisons by six LLM juror personas.
For each persona we fit Bradley-Terry log-scores (with a weak prior)."""
import csv, glob, json, sys, math
import numpy as np

src = sys.argv[1]  # path to .../data/phase_2
ctx = json.load(open(f"{src}/repository_context.json"))
rows = []
for f in sorted(glob.glob(f"{src}/runs/*.csv")):
    rows += list(csv.DictReader(open(f)))
items = sorted({r['item_a'] for r in rows} | {r['item_b'] for r in rows})
idx = {it: k for k, it in enumerate(items)}
personas = sorted({r['juror_id'] for r in rows})

def fit_bt(rs, m, prior=1.0, iters=500):
    # MM algorithm for Bradley-Terry with a prior: each item plays `prior`
    # virtual games (half won) against a virtual item of strength 1.
    wins = np.zeros(m); n = np.zeros((m, m))
    for r in rs:
        a, b, w = idx[r['item_a']], idx[r['item_b']], idx[r['winner']]
        n[a, b] += 1; n[b, a] += 1; wins[w] += 1
    p = np.ones(m)
    for _ in range(iters):
        denom = (n / (p[:, None] + p[None, :])).sum(1) + prior / (p + 1.0)
        p = (wins + prior / 2) / denom
        p /= np.exp(np.log(p).mean())
    s = np.log(p)
    return s - s.mean()

scores = {}
for per in personas:
    scores[per] = fit_bt([r for r in rows if r['juror_id'] == per], len(items)).tolist()
byname = {}
for c in ctx:
    key = c['github_url'].replace('https://github.com/', '')
    byname[key.lower()] = c
repos = []
for it in items:
    c = byname.get(it.lower(), {})
    repos.append({'id': it, 'name': c.get('name', it.split('/')[-1]),
                  'org': c.get('organization', it.split('/')[0]),
                  'description': (c.get('description') or '')[:200],
                  'stars': c.get('stars')})
json.dump({'repos': repos, 'personas': personas, 'scores': scores,
           'source': 'github.com/davidgasquez/gg24-deepfunding-market-weights (phase 2)',
           'n_comparisons': len(rows)}, open('data/gg24.json', 'w'), indent=1)
S = np.array([scores[p] for p in personas])
print('items', len(items), 'personas', personas)
print('score range per persona', [(round(x.min(),2), round(x.max(),2)) for x in S])
print('pairwise corr between personas:\n', np.round(np.corrcoef(S), 3))
med = np.median(S, 0); w = np.exp(med); w /= w.sum()
o = np.argsort(-w)
print('top shares (median persona):', [(items[k], round(w[k]*100,2)) for k in o[:8]])
print('share of top10', round(w[o[:10]].sum()*100,1), 'bottom 50', round(w[o[-50:]].sum()*100,1))
