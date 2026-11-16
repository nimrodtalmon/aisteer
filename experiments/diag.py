import sys; sys.path.insert(0,'.')
import steer.sim as S
from steer.sim import *
# instrument: count flags on blind vs not, by maintainers vs not
w=World(); p=replace(POLICIES['flag and sample'], invited_per_day=40)
import numpy as np
orig=S.run
def run_diag(world, policy, seed=0):
    rng=np.random.default_rng(seed)
    return orig(world, policy, seed)
r=run(w,p,seed=1,record=True)
print(r['error'])
