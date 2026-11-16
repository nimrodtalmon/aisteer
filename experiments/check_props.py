"""Numerical checks of Propositions 2 and 4 (small instances)."""
import numpy as np
rng = np.random.default_rng(0)

def run(m, rates, draw, steps=200000, step=0.01):
    x = np.zeros(m); pairs = [(a, b) for a in range(m) for b in range(a + 1, m)]
    p = np.array([rates[pr] for pr in pairs], dtype=float); p /= p.sum()
    idx = rng.choice(len(pairs), steps, p=p)
    for k in idx:
        a, b = pairs[k]; d = draw(a, b)
        s = np.sign(d - (x[a] - x[b])); x[a] += step * s / 2; x[b] -= step * s / 2
    return x - x.mean()

# Prop 2, consistent views: target + iid symmetric noise
m = 5; t = rng.normal(0, 1, m); t -= t.mean()
draw = lambda a, b: (t[a] - t[b]) + rng.normal(0, 1) + rng.standard_t(3) * 0.3
uniform = {(a, b): 1 for a in range(m) for b in range(a + 1, m)}
skewed = {(a, b): (50 if 0 in (a, b) else 1) for a in range(m) for b in range(a + 1, m)}
x1, x2 = run(m, uniform, draw), run(m, skewed, draw)
print('target ', np.round(t, 2)); print('uniform', np.round(x1, 2)); print('skewed ', np.round(x2, 2))
# Prop 2, inconsistent medians: (1,2)=1, (2,3)=1, (1,3)=0
med = {(0, 1): 1.0, (1, 2): 1.0, (0, 2): 0.0}
drawi = lambda a, b: med[(a, b)] + rng.normal(0, 0.5)
for name, r in (('mostly (1,3)', {(0, 1): 1, (1, 2): 1, (0, 2): 20}), ('mostly others', {(0, 1): 20, (1, 2): 20, (0, 2): 1})):
    x = run(3, r, drawi); print(name, 'gap 1-3 =', round(x[0] - x[2], 2))
