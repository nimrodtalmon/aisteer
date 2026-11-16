import sys; sys.path.insert(0,'.')
from steer.sim import *
from concurrent.futures import ProcessPoolExecutor
W=dict(n_members=150, n_maintainers=50)
def one(a):
    pol,K,s=a; w=World(**W)
    q=POLICIES[pol] if POLICIES[pol].voluntary or pol=='engine only' else replace(POLICIES[pol], invited_per_day=K)
    return (pol,K), run(w,q,seed=s)
pols=['engine only','open, multipliers','open, multipliers (huber)','open, nudges','panel, multipliers','panel, money-weighted','flag and sample','flag, sample, escalate']
jobs=[(p,K,s) for p in pols for K in ((0,) if p.startswith(('open','engine')) else (10,40)) for s in range(6)]
import collections; acc=collections.defaultdict(list)
with ProcessPoolExecutor() as ex:
    for k,r in ex.map(one,jobs): acc[k].append(r)
for k,rs in acc.items():
    f=lambda q: np.mean([r[q] for r in rs])
    print(f"{k[0]:28s} K={k[1]:3d} err={f('error'):.3f} short={f('shortchanged'):.3f} att={f('attention'):5.1f} capture={f('capture'):+.3f} esc={f('escalations'):.0f}")
