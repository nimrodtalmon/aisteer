"""Checks the attention-allocation corollary (Theorem 5 in the brief).

Projects j = 1..m, each tracked against the rest of the fund by its own nudges
(questions at rate q_j, step vol_j / sqrt(q_j), the best step of Theorem 3).
Misallocated funding is about 1/2 sum_j share_j E|err_j|, and E|err_j| is about
sqrt(2/pi) sqrt(MSE_j) with MSE_j = vol_j / (2 dens sqrt(q_j)).
Minimizing under sum_j q_j = A gives q_j proportional to (share_j sqrt(vol_j))^(4/5).

    python3 experiments/agenda_theory.py   -> results/agenda_theory.json
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tracking_theory import run_track

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    rng = np.random.default_rng(7)
    m, A, s, T = 20, 40.0, 0.5, 3000.0
    share = 1 / np.arange(1, m + 1) ** 1.1
    share /= share.sum()
    vol = rng.uniform(0.01, 0.09, m)
    dens = 1 / (s * math.sqrt(2 * math.pi))
    rules = {'uniform': np.ones(m), 'by share': share,
             'optimal': (share * np.sqrt(vol)) ** 0.8}
    out = {}
    for name, w in rules.items():
        q = A * w / w.sum()
        sim = th = 0.0
        for j in range(m):
            step = vol[j] / math.sqrt(q[j])
            mse = np.mean([run_track('nudge', q[j], step, vol[j], s, T, rng) for _ in range(2)])
            sim += 0.5 * share[j] * math.sqrt(2 / math.pi) * math.sqrt(mse)
            th += 0.5 * share[j] * math.sqrt(2 / math.pi) * math.sqrt(vol[j] / (2 * dens * math.sqrt(q[j])))
        out[name] = dict(sim=sim, theory=th)
        print(name, round(sim * 100, 3), round(th * 100, 3))
    json.dump(out, open(os.path.join(ROOT, 'results', 'agenda_theory.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
