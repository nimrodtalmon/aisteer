import sys; sys.path.insert(0,'.')
from steer.sim import *
from concurrent.futures import ProcessPoolExecutor
def one(args):
    nm, pol, K, s = args
    w=World(n_members=150, n_maintainers=nm)
    return (nm,pol,K), run(w, replace(POLICIES[pol], invited_per_day=K), seed=s)
jobs=[(nm,pol,K,s) for nm in (10,50,98) for pol in ('panel, random pairs','panel, money-weighted','flag and sample') for K in (10,40) for s in range(6)]
import collections
acc=collections.defaultdict(list)
with ProcessPoolExecutor() as ex:
    for k,r in ex.map(one, jobs): acc[k].append(r)
for k,rs in sorted(acc.items()):
    f=lambda q: np.mean([r[q] for r in rs])
    print(k, f"err={f('error'):.3f} short={f('shortchanged'):.3f} flags b/o={f('flags_on_blind'):.0f}/{f('flags_other'):.0f}")
