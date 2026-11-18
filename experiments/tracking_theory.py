"""Checks the single-pair theory of the brief against direct simulation.

Model: one log-ratio g(t). Questions arrive at rate q (Poisson). The wanted
log-ratio of an answerer is m(t) + noise, noise normal with sd s (or a
contaminated mix). The median wanted log-ratio m(t) is a Brownian motion with
volatility sigma (per unit time); sigma = 0 means a fixed target.

Nudge:      g <- g + step * sign(d - g)
Multiplier: g <- g + lr * (x - g),  x = infl * d   (infl = 1: honest typing)

Theory (small steps, errors small next to s):
  nudge       var(g - m) = (q step^2 + sigma^2) / (4 q step f0),  f0 = density of noise at 0
              best step = sigma / sqrt(q),   var = sigma / (2 f0 sqrt(q))
  multiplier  var(g - m) = (q lr^2 s^2 + sigma^2) / (2 q lr)
              best lr = sigma / (s sqrt(q)),  var = sigma s / sqrt(q)
  blind spot  start at g - m = e0 >> s, sigma = 0: the error falls at speed q*step,
              funding paid to the wrong place (small share, per unit share)
              = (e^e0 - 1)/rate_notice + (e^e0 - 1 - e0)/(q step)

    python3 experiments/tracking_theory.py      -> results/tracking_theory.json
"""
import json, math, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_track(rule, q, par, sigma, s, T, rng, infl=1.0, contam=0.0, burn=0.2):
    """Event-driven run; returns time-averaged mean square error after burn-in."""
    n = rng.poisson(q * T)
    times = np.sort(rng.uniform(0, T, n))
    dts = np.diff(np.concatenate([[0.0], times]))
    dm = rng.normal(0, 1, n) * sigma * np.sqrt(dts)
    noise = rng.normal(0, s, n)
    if contam > 0:
        bad = rng.random(n) < contam
        noise[bad] = math.log(999) * np.sign(rng.normal(size=bad.sum()))
    g = m = 0.0
    acc = w = 0.0
    t0 = burn * T
    for k in range(n):
        if times[k] > t0:                       # error is constant between events except m's walk;
            dt = dts[k] if times[k - 1 if k else 0] > t0 else times[k] - t0
            acc += ((g - m) ** 2 + sigma ** 2 * dt / 2) * dt   # E over the Brownian bridge part
            w += dt
        m += dm[k]
        d = m + noise[k]
        if rule == 'nudge':
            g += par * (1 if d > g else (-1 if d < g else 0))
        else:
            g += par * (infl * d - g)
    return acc / w


def theory_var(rule, q, par, sigma, s):
    if rule == 'nudge':
        f0 = 1 / (s * math.sqrt(2 * math.pi))
        return (q * par ** 2 + sigma ** 2) / (4 * q * par * f0)
    return (q * par ** 2 * s ** 2 + sigma ** 2) / (2 * q * par)


def blind_spot(q, step, s, e0, notice, rng, reps=400):
    """Average funding to the wrong place per unit share, from e0 until the error is below s/4."""
    tot = 0.0
    for _ in range(reps):
        t_notice = rng.exponential(1 / notice)
        cost = (math.exp(e0) - 1) * t_notice
        g, t = e0, 0.0
        while g > 0:                              # stop at the target (then jitter starts)
            dt = rng.exponential(1 / q)
            cost += (math.exp(g) - 1) * dt
            d = rng.normal(0, s)
            g += step * (1 if d > g else -1)
            t += dt
        tot += cost
    return tot / reps


def theory_blind(q, step, e0, notice):
    return (math.exp(e0) - 1) / notice + (math.exp(e0) - 1 - e0) / (q * step)


def main():
    rng = np.random.default_rng(1)
    out = {'track': [], 'best': [], 'blind': [], 'robust': []}
    sigma, s, T = 0.05, 0.5, 4000.0
    for q in (1, 4, 16, 64):
        for rule, grid in (('nudge', (0.25, 0.5, 1, 2, 4)), ('multiplier', (0.25, 0.5, 1, 2, 4))):
            best = theory_par = sigma / math.sqrt(q) if rule == 'nudge' else sigma / (s * math.sqrt(q))
            res = []
            for f in grid:
                par = theory_par * f
                sim = np.mean([run_track(rule, q, par, sigma, s, T, rng) for _ in range(3)])
                th = theory_var(rule, q, par, sigma, s)
                res.append((par, sim, th))
                out['track'].append(dict(rule=rule, q=q, par=par, factor=f, sim=sim, theory=th))
            bp = min(res, key=lambda r: r[1])
            out['best'].append(dict(rule=rule, q=q, best_par_sim=bp[0], best_par_theory=theory_par,
                                    var_sim=bp[1], var_theory=theory_var(rule, q, theory_par, sigma, s)))
            print(rule, q, 'best factor', round(bp[0] / theory_par, 2), 'var sim/theory', round(bp[1], 5), round(theory_var(rule, q, theory_par, sigma, s), 5))
    # robustness: 5% answers at the 999x cap; inflation 2.7
    q = 16
    for name, kw in (('honest', {}), ('5% at 999x', {'contam': 0.05}), ('inflated 2.7', {'infl': 2.7})):
        for rule, par in (('nudge', sigma / math.sqrt(q)), ('multiplier', sigma / (s * math.sqrt(q)))):
            sim = np.mean([run_track(rule, q, par, sigma, s, T, rng, **kw) for _ in range(3)])
            out['robust'].append(dict(case=name, rule=rule, rmse=math.sqrt(sim)))
            print('robust', name, rule, round(math.sqrt(sim), 4))
    # blind spot
    for q, step, notice in ((2, 0.1, 0.1), (8, 0.1, 0.1), (8, 0.3, 0.5), (32, 0.05, 1.0)):
        sim = blind_spot(q, step, s=0.3, e0=1.5, notice=notice, rng=rng)
        th = theory_blind(q, step, 1.5, notice)
        out['blind'].append(dict(q=q, step=step, notice=notice, sim=sim, theory=th))
        print('blind', q, step, notice, round(sim, 2), round(th, 2))
    json.dump(out, open(os.path.join(ROOT, 'results', 'tracking_theory.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
