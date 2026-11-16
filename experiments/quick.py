import sys, time; sys.path.insert(0,'.')
from steer.sim import *
w=World()
def show(name,q,reps=6):
    rs=[run(w,q,seed=s) for s in range(reps)]
    f=lambda k: np.mean([r[k] for r in rs])
    print(f"{name:25s} K={q.invited_per_day:3d} err={f('error'):.3f} short={f('shortchanged'):.3f} att={f('attention'):5.1f} capture={f('capture'):+.3f} flags b/o={f('flags_on_blind'):.0f}/{f('flags_other'):.0f}")
for name,p in POLICIES.items():
    if p.voluntary or name=='engine only': show(name,p)
    else:
        for K in (10,40): show(name, replace(p, invited_per_day=K))
