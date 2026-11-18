#!/usr/bin/env python3
"""Builds web/brief/index.html: the state of the work as conference-style slides
(motivation, model, results, related work, summary). Pictures come from the
project's results files and from small runs done here. Questions for Nimrod go
in the chat, not on slides.

    python3 web/brief/src/build.py

The deck engine (web/assets/deck.css, deck.js) is copied from the zutot repo.
"""
import json, math, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, '..', 'index.html')
DATE = 'November 18, 2026'

OR, DK, GR, GL, CARD, PALE, LT = '#F7941D', '#26282C', '#5F6368', '#B9BCC1', '#FDFDFB', '#FCE8D2', '#F3F3F1'
BLUE = '#3A7BC8'
FONT = 'font-family="Heebo, Arial, sans-serif"'


def res(name):
    return json.load(open(os.path.join(ROOT, 'results', name)))


def svg(w, h, body):
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>{body}</svg>'


def text(x, y, s, size=30, fill=DK, anchor='middle', weight=400):
    return f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'


def line(x1, y1, x2, y2, col=GL, w=3, extra=''):
    return f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" stroke-width="{w}" {extra}/>'


def poly(pts, col, w=5, extra=''):
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round" {extra}/>'


def head(cx, cy, r, fill):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            f'<path d="M{cx-1.6*r} {cy+2.6*r} a{1.6*r} {1.6*r} 0 0 1 {3.2*r} 0 Z" fill="{fill}"/>')


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ---------- pictures ----------
def excess_series():
    """The engine over-funds one project from time 20; a member notices at 55
    and nudges it back in four steps."""
    ts = [k / 2 for k in range(201)]
    def e(t):
        if t < 20: return 0.0
        v = min(0.12, 0.12 * (t - 20) / 5)
        for tn in (55, 62, 69, 76):
            if t >= tn: v -= 0.03
        return max(v, 0.0)
    return ts, [e(t) for t in ts]


def flow_vis(annotated=True, w=1660):
    ts, es = excess_series()
    others = [0.24, 0.20, 0.16, 0.12, 0.08]
    h, b = 560 if annotated else 470, ''
    X0, X1, Yb, Yt = 40, w - 40, 470 if annotated else 420, 70 if annotated else 30
    X = lambda t: X0 + t / 100 * (X1 - X0)
    Y = lambda v: Yb - v * (Yb - Yt)
    b += f'<defs><pattern id="hatch{w}" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' \
         f'<rect width="14" height="14" fill="{PALE}"/><line x1="0" y1="0" x2="0" y2="14" stroke="{OR}" stroke-width="7"/></pattern></defs>'
    layers = []                                   # cumulative boundaries, bottom to top
    for t, e in zip(ts, es):
        z = 1 + 1.6 * e
        cuts = [0.20 / z, (0.20 + 1.6 * e) / z]
        acc = cuts[-1]
        for o in others:
            acc += o / z; cuts.append(acc)
        layers.append(cuts)
    fills = [OR, f'url(#hatch{w})', '#6E7277', '#9A9DA2', '#7F8388', '#AEB1B5', '#8C9095']
    for L in range(len(fills)):
        lo = [0.0 if L == 0 else c[L - 1] for c in layers]
        hi = [c[L] for c in layers]
        pts = [(X(t), Y(v)) for t, v in zip(ts, hi)] + [(X(t), Y(v)) for t, v in zip(reversed(ts), reversed(lo))]
        b += '<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + f'" fill="{fills[L]}"/>'
    b += line(X0, Yb, X1, Yb, DK, 3)
    b += f'<path d="M{X1-4} {Yb-10} l18 10 l-18 10 Z" fill="{DK}"/>' + text(X1, Yb + 40, 'time', 28, GR, 'end', 700)
    if annotated:
        b += text(X(22), Yt - 30, 'the AI starts to over-fund one project', 28, OR, 'start', 800)
        b += head(int(X(55)), Yb + 30, 14, BLUE)
        b += text(X(55) + 30, Yb + 72, 'a member notices and nudges', 28, BLUE, 'start', 800)
        b += f'<rect x="{X0}" y="{Yb + 50}" width="28" height="28" fill="url(#hatch{w})"/>' + text(X0 + 40, Yb + 74, 'funding to the wrong place', 28, DK, 'start', 700)
    else:
        x = X(40)
        b += line(x, Yt - 10, x, Yb, DK, 4) + text(x + 12, Yt + 30, 'split at time t', 28, LT, 'start', 800)
        b += text(X0, Yb + 40, 'shares of the funding flow', 26, GR, 'start', 700)
    return svg(w, h, b)


def notice_vis():
    taus = [k / 20 for k in range(201)]
    w, h, b = 760, 500, ''
    X0, X1, Y0, Y1 = 90, 740, 420, 50
    X = lambda t: X0 + t / 10 * (X1 - X0)
    Y = lambda p: Y0 - p * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    b += poly([(X(t), Y(1 - math.exp(-0.25 * t))) for t in taus], GR, 5)
    b += poly([(X(t), Y(1 - math.exp(-0.04 * t * t))) for t in taus], OR, 6)
    b += text(X(2.8), Y(1 - math.exp(-0.7)) - 18, 'constant rate', 28, GR, 'end', 700)
    b += text(X(3.3), Y(1 - math.exp(-0.04 * 3.3 ** 2)) + 40, 'rate grows with age', 28, OR, 'start', 800)
    b += text(X0 - 14, Y(0) + 10, '0', 26, GR, 'end') + text(X0 - 14, Y(1) + 10, '1', 26, GR, 'end')
    b += text((X0 + X1) / 2, 470, 'age of the problem', 28, GR)
    b += text(X0, 30, 'probability it was noticed', 26, GR, 'start', 700)
    return svg(w, h, b)


def excess_vis():
    ts, es = excess_series()
    sh = [(0.20 + e) / (1 + e) for e in es]
    w, h, b = 760, 500, ''
    X0, X1, Y0, Y1, lo, hi = 90, 740, 420, 60, 0.15, 0.31
    X = lambda t: X0 + t / 100 * (X1 - X0)
    Y = lambda v: Y0 - (v - lo) / (hi - lo) * (Y0 - Y1)
    pts = [(X(t), Y(v)) for t, v in zip(ts, sh)] + [(X(ts[-1]), Y(0.2)), (X(0), Y(0.2))]
    b += '<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + f'" fill="{PALE}"/>'
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    b += line(X0, Y(0.2), X1, Y(0.2), DK, 4, 'stroke-dasharray="12 8"') + text(X1, Y(0.2) + 40, 'target share', 28, DK, 'end', 700)
    b += poly([(X(t), Y(v)) for t, v in zip(ts, sh)], OR, 6)
    b += text(X(36), Y(0.29) - 10, 'share', 28, OR, 'middle', 800)
    b += text(X(40), Y(0.23), 'paid to the wrong place', 26, DK, 'middle', 700)
    b += text((X0 + X1) / 2, 470, 'time', 28, GR)
    return svg(w, h, b)


def card_vis():
    w, h, b = 760, 470, ''
    b += f'<rect x="10" y="10" width="740" height="450" rx="28" fill="{CARD}" stroke="{GL}" stroke-width="3"/>'
    b += text(50, 75, 'current split', 30, GR, 'start', 700)
    for k, (lab, amt, bw) in enumerate((('a', '$6.2k', 430), ('b', '$3.5k', 245))):
        y = 120 + k * 90
        b += text(60, y + 42, lab, 44, DK, 'start', 800)
        b += f'<rect x="120" y="{y}" width="{bw}" height="56" rx="10" fill="{GR}"/>'
        b += text(140 + bw, y + 42, amt, 36, DK, 'start', 700)
    for k, (lab, on) in enumerate((('more to a', False), ('about right', False), ('more to b', True))):
        x = 40 + k * 230
        b += f'<rect x="{x}" y="340" width="210" height="80" rx="16" fill="{OR if on else LT}" stroke="{OR if on else GL}" stroke-width="2"/>'
        b += text(x + 105, 392, lab, 30, DK, weight=700)
    return svg(w, h, b)


def formats_vis():
    """Simulated answers on one pair; answer 15 types a multiplier of 999."""
    rng = random.Random(3)
    T, gap0, truth, sd = 30, 0.0, 0.6, 0.7
    ds = [truth + rng.gauss(0, sd) for _ in range(T)]
    ds[14] = math.log(999)
    nud, mul = [gap0], [gap0]
    for d in ds:
        g = nud[-1]; nud.append(g + 0.1 * ((d > g) - (d < g)))
        g = mul[-1]; mul.append(g + 0.3 * (d - g))
    w, h, b = 760, 520, ''
    X0, X1, Y0, Y1, lo, hi = 90, 740, 440, 40, -0.5, 2.5
    X = lambda t: X0 + t / T * (X1 - X0)
    Y = lambda g: Y0 - (g - lo) / (hi - lo) * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    b += line(X0, Y(truth), X1, Y(truth), GL, 3, 'stroke-dasharray="10 8"')
    b += text(X1, Y(truth) - 14, 'median wanted ratio', 26, GR, 'end')
    b += poly([(X(t), Y(g)) for t, g in enumerate(mul)], BLUE, 5)
    b += poly([(X(t), Y(g)) for t, g in enumerate(nud)], OR, 6)
    b += text(X(15) + 18, Y(max(mul)) + 30, 'multiplier: one 999× answer', 26, BLUE, 'start', 700)
    b += text(X(8), Y(nud[8]) + 50, 'nudge', 30, OR, 'middle', 800)
    b += text((X0 + X1) / 2, 500, 'answers', 28, GR) + text(X0 - 14, Y(0) + 10, '0', 26, GR, 'end') + text(X0 - 14, Y(2) + 10, '2', 26, GR, 'end')
    b += text(X0, 26, 'ratio of a to b (log scale)', 26, GR, 'start', 700)
    return svg(w, h, b)


def misalloc_vis():
    alloc = [0.20, 0.16, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03]
    targ = [0.17, 0.17, 0.11, 0.13, 0.08, 0.10, 0.06, 0.08, 0.03, 0.07]
    w, h, b = 760, 500, ''
    X0, Y0, H, bw = 60, 420, 1600, 66
    b += line(X0 - 10, Y0, X0 + 10 * bw + 10, Y0)
    for k, (a, t) in enumerate(zip(alloc, targ)):
        x = X0 + k * bw
        b += f'<rect x="{x+8}" y="{Y0 - a*H:.0f}" width="{bw-16}" height="{a*H:.0f}" rx="4" fill="{GR}"/>'
        lo, hi = sorted((a, t))
        if hi > lo:
            b += f'<rect x="{x+8}" y="{Y0 - hi*H:.0f}" width="{bw-16}" height="{(hi-lo)*H:.0f}" fill="{OR}" opacity=".85"/>'
        b += line(x + 2, Y0 - t * H, x + bw - 2, Y0 - t * H, DK, 5)
    b += f'<rect x="{X0}" y="455" width="28" height="28" rx="4" fill="{GR}"/>' + text(X0 + 40, 479, 'share', 28, DK, 'start', 700)
    b += line(X0 + 170, 469, X0 + 210, 469, DK, 5) + text(X0 + 222, 479, 'target share', 28, DK, 'start', 700)
    b += f'<rect x="{X0+420}" y="455" width="28" height="28" rx="4" fill="{OR}"/>' + text(X0 + 460, 479, 'difference', 28, DK, 'start', 700)
    return svg(w, h, b)


def loss_vis():
    # judged gaps: a skewed mixture; plot E|d - gap|
    comps = [(0.75, 0.3, 0.4), (0.25, 1.6, 0.5)]
    def el(g):
        s = 0
        for wgt, mu, sd in comps:
            z = (g - mu) / sd
            s += wgt * ((g - mu) * (2 * ncdf(z) - 1) + 2 * sd * math.exp(-z * z / 2) / math.sqrt(2 * math.pi))
        return s
    cdf = lambda g: sum(wgt * ncdf((g - mu) / sd) for wgt, mu, sd in comps)
    lo, hi = -1.0, 3.0
    a, c = lo, hi
    for _ in range(60):
        mid = (a + c) / 2
        a, c = (mid, c) if cdf(mid) < 0.5 else (a, mid)
    med, mean = a, sum(wgt * mu for wgt, mu, _ in comps)
    w, h, b = 760, 520, ''
    X0, X1, Y0, Y1 = 60, 740, 440, 40
    gs = [lo + k * (hi - lo) / 200 for k in range(201)]
    vals = [el(g) for g in gs]
    vmax = max(vals)
    X = lambda g: X0 + (g - lo) / (hi - lo) * (X1 - X0)
    Y = lambda v: Y0 - v / vmax * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0)
    b += poly([(X(g), Y(v)) for g, v in zip(gs, vals)], OR, 6)
    b += line(X(med), Y0, X(med), Y(el(med)) - 30, DK, 4)
    b += text(X(med), Y(el(med)) - 44, 'median: minimum', 28, DK, 'middle', 800)
    b += line(X(mean), Y0, X(mean), Y0 - 60, BLUE, 4)
    b += text(X(mean) + 12, Y0 - 70, 'mean', 28, BLUE, 'start', 700)
    b += text((X0 + X1) / 2, 490, 'current ratio (log scale)', 28, GR)
    b += text(X0, 30, 'expected distance to wanted ratios', 26, GR, 'start', 700)
    return svg(w, h, b)


def bound_vis():
    rng = random.Random(5)
    k, step = 10, 0.1
    w, h, b = 760, 520, ''
    X0, X1, Y0, Y1 = 90, 740, 440, 50
    X = lambda t: X0 + t / k * (X1 - X0)
    Y = lambda g: Y0 - g / (k * step) * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    worst = [t * step for t in range(k + 1)]
    pts = []
    for t, g in enumerate(worst):
        pts += [(X(t), Y(g))] + ([(X(t + 1), Y(g))] if t < k else [])
    b += f'<polygon points="{X0},{Y0} ' + ' '.join(f"{x:.0f},{y:.0f}" for x, y in pts) + f' {X1},{Y0}" fill="{PALE}"/>'
    b += poly(pts, OR, 6)
    g, rp = 0.0, [(X(0), Y(0))]
    for t in range(k):
        g += step * rng.choice((1, 1, 0, -1)); g = max(g, 0)
        rp += [(X(t + 1), rp[-1][1]), (X(t + 1), Y(g))]
    b += poly(rp, GR, 4)
    b += text(X(6.4), Y(0.66) - 20, 'all ten push one way', 28, OR, 'end', 800)
    b += text(X(9.6), Y(g) - 16, 'typical', 28, GR, 'end', 700)
    b += text(X1, Y(1.0) - 16, 'ratio × e ≈ 2.7', 30, DK, 'end', 800)
    b += text((X0 + X1) / 2, 490, 'answers in one day', 28, GR)
    b += text(X0, 30, 'change of ratio (log scale)', 26, GR, 'start', 700)
    return svg(w, h, b)


def agenda_vis():
    """The inconsistent example: medians 1 on (1,2) and (2,3), 0 on (1,3)."""
    rng = random.Random(0)
    med = {(0, 1): 1.0, (1, 2): 1.0, (0, 2): 0.0}
    pairs = list(med)
    out = {}
    for name, r in (('mostly (1,3)', (1, 1, 20)), ('mostly the others', (20, 20, 1))):
        x, tr = [0.0, 0.0, 0.0], []
        tot = sum(r)
        for s in range(60000):
            u, acc = rng.random() * tot, 0
            for pr, rr in zip(pairs, r):
                acc += rr
                if u < acc:
                    break
            a, c = pr
            d = med[pr] + rng.gauss(0, 0.5)
            sg = (d > x[a] - x[c]) - (d < x[a] - x[c])
            x[a] += 0.01 * sg / 2; x[c] -= 0.01 * sg / 2
            if s % 600 == 0:
                tr.append(x[0] - x[2])
        out[name] = tr
    w, h, b = 760, 520, ''
    X0, X1, Y0, Y1, hi = 90, 740, 440, 50, 2.2
    n = len(out['mostly (1,3)'])
    X = lambda t: X0 + t / (n - 1) * (X1 - X0)
    Y = lambda g: Y0 - g / hi * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    for g in (1, 2):
        b += line(X0, Y(g), X1, Y(g), '#E3E2DD', 2) + text(X0 - 14, Y(g) + 10, str(g), 26, GR, 'end')
    b += text(X0 - 14, Y(0) + 10, '0', 26, GR, 'end')
    b += poly([(X(t), Y(g)) for t, g in enumerate(out['mostly the others'])], OR, 6)
    b += poly([(X(t), Y(g)) for t, g in enumerate(out['mostly (1,3)'])], BLUE, 6)
    b += text((X0 + X1) / 2, Y(2) + 50, 'ask mostly about (1,2) and (2,3)', 28, OR, 'middle', 800)
    b += text((X0 + X1) / 2, Y(0) - 40, 'ask mostly about (1,3)', 28, BLUE, 'middle', 800)
    b += text((X0 + X1) / 2, 490, 'answers', 28, GR)
    b += text(X0, 30, 'ratio of projects 1 and 3 (log scale)', 26, GR, 'start', 700)
    return svg(w, h, b), round(out['mostly (1,3)'][-1], 2), round(out['mostly the others'][-1], 2)


def mixture_vis(bias=1.0, sd=0.71):
    def med(f):
        a, c = -3, 4
        for _ in range(60):
            m = (a + c) / 2
            v = (1 - f) * ncdf(m / sd) + f * ncdf((m - bias) / sd)
            a, c = (m, c) if v < 0.5 else (a, m)
        return a
    fs = [k / 100 for k in range(101)]
    ms = [med(f) for f in fs]
    w, h, b = 760, 520, ''
    X0, X1, Y0, Y1 = 90, 740, 440, 50
    X = lambda f: X0 + f * (X1 - X0)
    Y = lambda g: Y0 - g / 1.15 * (Y0 - Y1)
    b += line(X0, Y0, X1, Y0) + line(X0, Y0, X0, Y1)
    b += line(X0, Y(bias), X1, Y(bias), GL, 3, 'stroke-dasharray="10 8"') + text(X0 + 10, Y(bias) - 14, 'bias', 28, GR, 'start', 700)
    b += poly([(X(f), Y(m)) for f, m in zip(fs, ms)], OR, 6)
    b += f'<circle cx="{X(0)}" cy="{Y(0)}" r="11" fill="{DK}"/>' + text(X(0) + 20, Y(0) - 18, 'recusal', 28, DK, 'start', 800)
    b += f'<circle cx="{X(0.95)}" cy="{Y(med(0.95))}" r="11" fill="{DK}"/>' + text(X(0.95) - 18, Y(med(0.95)) + 44, 'nobody else looks', 28, DK, 'end', 800)
    b += text(X0 - 14, Y(0) + 10, '0', 26, GR, 'end') + text(X0 - 14, Y(1) + 10, '1', 26, GR, 'end')
    b += text(X(0) , 488, '0', 26, GR) + text(X(1), 488, '1', 26, GR)
    b += text((X0 + X1) / 2, 490, 'fraction of answers from maintainers', 28, GR)
    b += text(X0, 30, 'resting ratio above consensus (log)', 26, GR, 'start', 700)
    return svg(w, h, b)


def exaggeration_vis(infl=2.7):
    rng = random.Random(11)
    ds = sorted(0.5 + rng.gauss(0, 0.5) for _ in range(8)) + [2.6]
    ds.sort()
    med, mean = ds[len(ds) // 2], sum(ds) / len(ds)
    w, h, b = 780, 420, ''
    lo, hi = -0.5, 3.5
    X = lambda g: 40 + (g - lo) / (hi - lo) * 700
    b += line(30, 200, 750, 200, GL, 4)
    for d in ds:
        b += f'<circle cx="{X(d):.0f}" cy="200" r="15" fill="{DK}"/>'
    for g, col, lab, y, anchor, dx in ((med, OR, 'nudges: median', 110, 'end', 8), (mean, GR, 'mean', 310, 'start', -8),
                                       (infl * mean, BLUE, 'multipliers: infl × mean', 110, 'middle', 0)):
        b += f'<rect x="{X(g)-4:.0f}" y="140" width="8" height="120" rx="4" fill="{col}"/>'
        b += text(X(g) + dx, y, lab, 30, col, anchor, 800)
    b += text(X(0), 380, '0', 26, GR) + text(X(1), 380, '1', 26, GR) + text(X(2), 380, '2', 26, GR) + text(X(3), 380, '3', 26, GR)
    b += text(390, 410, 'wanted ratio of one pair (log scale)', 26, GR)
    return svg(w, h, b), med, mean


def frontier_vis():
    d = res('frontier_base.json')
    def series(name):
        pts = sorted((v['attention'][0], v['error'][0] * 100) for k, v in d.items()
                     if k.split('|')[0] == name and v['attention'][0] > 0.5)
        return pts
    fs, rp = series('flag and sample'), series('panel, random pairs')
    eng = d['engine only|0']['error'][0] * 100
    esc = d['flag, sample, escalate|2']; esc = (esc['attention'][0], esc['error'][0] * 100)
    on, om = d['open, nudges|0'], d['open, multipliers|0']
    w, h, b = 1660, 520, ''
    X0, X1, Y0, Y1, ymax = 120, 1620, 436, 30, 22
    X = lambda a: X0 + math.log(a) / math.log(40) * (X1 - X0)
    Y = lambda e: Y0 - e / ymax * (Y0 - Y1)
    for e in (5, 10, 15, 20):
        b += line(X0, Y(e), X1, Y(e), '#E3E2DD', 2) + text(X0 - 16, Y(e) + 10, f'{e}%', 26, GR, 'end')
    b += line(X0, Y0, X1, Y0) + text(X0 - 16, Y0 + 10, '0%', 26, GR, 'end')
    for a in (1, 2, 5, 10, 20, 40):
        b += text(X(a), Y0 + 38, str(a), 26, GR)
    b += text(X1, Y0 + 70, 'answered questions per day (log scale)', 26, GR, 'end')
    b += line(X0, Y(eng), X1, Y(eng), DK, 4, 'stroke-dasharray="14 10"')
    b += text(X0 + 10, Y(eng) - 14, f'AI alone: {eng:.1f}%', 28, DK, 'start', 800)
    b += poly([(X(a), Y(e)) for a, e in rp], GR, 4)
    b += ''.join(f'<circle cx="{X(a):.0f}" cy="{Y(e):.0f}" r="8" fill="{GR}"/>' for a, e in rp)
    b += poly([(X(a), Y(e)) for a, e in fs], OR, 6)
    b += ''.join(f'<circle cx="{X(a):.0f}" cy="{Y(e):.0f}" r="11" fill="{OR}"/>' for a, e in fs)
    b += text(X(fs[3][0]) + 10, Y(fs[3][1]) + 46, 'flag and sample', 30, OR, 'start', 800)
    b += text(X(rp[2][0]) + 20, Y(rp[2][1]) - 16, 'random pairs, random members', 28, GR, 'start', 700)
    x, y = X(esc[0]), Y(esc[1])
    b += f'<rect x="{x-12:.0f}" y="{y-12:.0f}" width="24" height="24" fill="{BLUE}" transform="rotate(45 {x:.0f} {y:.0f})"/>'
    b += text(x, y + 50, f'+ escalation: {esc[1]:.1f}%', 28, BLUE, 'start', 800)
    for v, lab in ((on, 'open forum, nudges'), (om, 'open forum, multipliers')):
        x, y = X(v['attention'][0]), Y(v['error'][0] * 100)
        b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="{LT}" stroke="{DK}" stroke-width="4"/>'
        b += text(x + 22, y + 10, lab, 28, DK, 'start', 700)
    return svg(w, h, b), fs, eng


def designs_vis():
    d = res('steering_tuned_base.json')
    eng = res('frontier_base.json')['engine only|0']
    rows = [('AI alone', eng, DK),
            ('open forum, multipliers', d['open forum, multipliers'], GR),
            ('open forum, nudges', d['open forum, nudges'], GR),
            ('random members, multipliers', d['panel, multipliers'], GR),
            ('random members, nudges', d['panel, nudges'], OR),
            ('random members, nudges, flags', d['panel, nudges, flags'], OR)]
    w, h, b = 1660, 520, ''
    L, bx, sc = 520, 540, 820 / 22
    b += text(bx, 30, 'misallocated', 28, GR, 'start', 700) + text(1650, 30, 'captured', 28, GR, 'end', 700)
    for k, (lab, v, col) in enumerate(rows):
        y = 70 + k * 74
        e, c = v['error'][0] * 100, v['capture'][0] * 100
        b += text(L, y + 38, lab, 32, DK, 'end', 700 if col == OR else 400)
        b += f'<rect x="{bx}" y="{y}" width="{e*sc:.0f}" height="52" rx="8" fill="{col}"/>'
        b += text(bx + e * sc + 16, y + 38, f'{e:.1f}%', 32, DK, 'start', 800)
        cap = '—' if k == 0 else (f'{c:.1f}%' if c > 1 else '≈ 0')
        b += text(1650, y + 38, cap, 32, DK, 'end', 700)
    return svg(w, h, b), {lab: v for lab, v, _ in rows}


def inflated_vis():
    base, infl = res('steering_tuned_base.json'), res('steering_tuned_inflated.json')
    fb, fi = res('frontier_base.json'), res('frontier_inflated.json')
    eng = fb['engine only|0']['error'][0] * 100
    rows = [('flag and sample, 5 a day', fb['flag and sample|10'], fi['flag and sample|10']),
            ('random members, nudges, flags', base['panel, nudges, flags'], infl['panel, nudges, flags']),
            ('random members, nudges', base['panel, nudges'], infl['panel, nudges']),
            ('open forum, nudges', base['open forum, nudges'], infl['open forum, nudges'])]
    w, h, b = 1660, 520, ''
    L, bx, sc = 520, 540, 900 / 26
    for k, (lab, vb, vi) in enumerate(rows):
        y = 40 + k * 110
        eb, ei = vb['error'][0] * 100, vi['error'][0] * 100
        b += text(L, y + 56, lab, 32, DK, 'end', 700)
        b += f'<rect x="{bx}" y="{y}" width="{eb*sc:.0f}" height="40" rx="6" fill="{OR}"/>' + text(bx + eb * sc + 14, y + 32, f'{eb:.1f}%', 28, DK, 'start', 800)
        b += f'<rect x="{bx}" y="{y+46}" width="{ei*sc:.0f}" height="40" rx="6" fill="{BLUE}"/>' + text(bx + ei * sc + 14, y + 78, f'{ei:.1f}%', 28, DK, 'start', 800)
    x = bx + eng * sc
    b += line(x, 20, x, 470, DK, 4, 'stroke-dasharray="12 8"') + text(x + 14, 506, f'AI alone: {eng:.1f}%', 28, DK, 'start', 800)
    b += f'<rect x="60" y="482" width="28" height="28" rx="4" fill="{OR}"/>' + text(100, 506, 'base world', 28, DK, 'start', 700)
    b += f'<rect x="300" y="482" width="28" height="28" rx="4" fill="{BLUE}"/>' + text(340, 506, 'judgments inflated', 28, DK, 'start', 700)
    lo = min(fi['flag and sample|10']['error'][0], infl['panel, nudges, flags']['error'][0], infl['open forum, multipliers clipped']['error'][0]) * 100
    hi = max(v['error'][0] for v in infl.values()) * 100
    return svg(w, h, b), lo, hi, eng


def policy_vis():
    steps = [('Flag', 'anyone, any time; signed, standing; opposite flags cancel; own project counts ½'),
             ('Sample', '½ of questions by net flags, ½ by share, each with a random partner'),
             ('Nudge', 'a random member who maintains neither project; one fixed step; ≤ 10 a day'),
             ('Escalate', 'net flags at a threshold: a panel answers the next questions')]
    out = '<div class="flow">'
    for k, (t, s) in enumerate(steps):
        if k:
            out += '<span class="arrow">→</span>'
        out += f'<div class="step{" on" if t == "Nudge" else ""}"><b>{t}</b><span>{s}</span></div>'
    return out + '</div>'


def related_vis():
    boxes = [('Iterative Local Voting', 'Garg et al. 2017', 'random voters move a point locally; no stakeholders, agenda or AI'),
             ('Budget aggregation, medians', 'Freeman et al. 2021 · El-Mhamdi et al. 2023', 'one-shot proposals and strategyproofness; here a stream of small answers'),
             ('Costly voluntary voting', 'Krishna &amp; Morgan 2015 · Müller &amp; Puppe 2020', 'turnout follows intensity: a reason to split attention from verdict'),
             ('Random juries, AI control', 'Kleros 2019 · Greenblatt et al. 2024', 'review where someone is suspicious; here flags only set the agenda')]
    return '<div class="rw">' + ''.join(
        f'<div class="box"><h3>{t}</h3><p class="who">{w}</p><p class="diff">{x}</p></div>' for t, w, x in boxes) + '</div>'


# ---------- notation ----------
I = lambda v: '\\(' + v + '\\)'
view, step, rate, gap, share, target, loss = (r'\mathrm{view}', r'\mathrm{step}', r'\mathrm{rate}',
                                                     r'\mathrm{gap}', r'\mathrm{split}', r'\mathrm{target}', r'\mathrm{loss}')
frac, bias, infl, lr = r'\mathrm{frac}_j', r'\mathrm{bias}', r'\mathrm{infl}', r'\mathrm{lr}'


def thm(label, title, box, why, vis, caption='', stack=False, pic_h=None):
    cap = f'<p class="cap">{caption}</p>' if caption else ''
    return f'''<section class="slide light">
  <p class="eyebrow">{label}</p>
  <h2>{title}</h2>
  <div class="{'stack' if stack else 'split'}">
    <div><div class="box">{box}</div><div class="why">{why}</div></div>
    <div class="pic"{f' style="--ph:{pic_h}px"' if pic_h else ''}>{vis}{cap}</div>
  </div>
</section>'''


TITLE = f'''<section class="slide dark center">
  <p class="eyebrow">aisteer</p>
  <h1>Steering a Living Allocator<br>with Scarce Attention</h1>
  <p class="big">An AI splits a fund; a community keeps it on course</p>
  <p class="muted">Nimrod Talmon · Ben-Gurion University · draft, {DATE}</p>
</section>'''

slides = [TITLE]
S = slides.append

S(f'''<section class="slide light">
  <p class="eyebrow">Motivation</p>
  <h2>An AI splits a stream of funding</h2>
  <p class="sub">Money flows all the time; when the split goes wrong, someone should notice.</p>
  <div class="vis">{flow_vis()}</div>
</section>''')

S('''<section class="slide light">
  <p class="eyebrow">Motivation</p>
  <h2>A real case: Deep Funding, round GG24</h2>
  <p class="sub">An AI splits $350k among 98 open-source repos; human jurors compare pairs.</p>
  <div class="facts">
    <div class="box"><p class="k">scarce</p><p>About 50 jurors gave about 500 judgments; motivation was the main constraint.</p></div>
    <div class="box"><p class="k">noisy</p><p>Jurors disagreed on which project ranks higher 40% of the time.</p></div>
    <div class="box"><p class="k">fragile</p><p>One answer rating a project 999× another moved about a quarter of the funding.</p></div>
    <div class="box"><p class="k">wanted</p><p>The trial’s analysis asks for continuous funding with occasional juror input.</p></div>
  </div>
</section>''')

S(thm('Model', 'The fund and the AI',
      f"""<p>Projects {I(r'1, \dots, m')}. Funding flows continuously over time.</p>
<p>The <b>split</b> {I(share + '_t')}: the fraction of the flow each project gets at time {I('t')}; the fractions sum to 1.</p>
<p>An <b>AI</b> sets the split and may change it at any time.</p>""",
      '<p>First, a well-meaning AI: right on most projects, but wrong on some for a long time.</p>',
      flow_vis(False, 760)))

S(thm('Model', 'Members',
      f"""<p>Members {I(r'1, \dots, n')}; <b>view</b> {I(view + '_i')}: the split {I('i')} considers right. Some maintain a project.</p>
<p><b>Noticing:</b> members look at projects now and then; a project that is more off, for longer, is more likely to be noticed.</p>
<p><b>Flag:</b> a member who notices a project may mark it as too low or too high.</p>""",
      '<p>The chance that a problem is still unnoticed falls with its age.</p>',
      notice_vis(), 'Illustration: one problem, many members.'))

S(thm('Model', 'Questions',
      f"""<p>A <b>question</b> shows a member two projects {I('a, b')} and their current amounts.</p>
<p>The member answers by their view, with some noise: more to {I('a')}, about right, or more to {I('b')}.</p>
<p><b>Attention:</b> answered questions per unit of time. Flags are nearly free.</p>""",
      '<p>An answer gives a direction, never an amount.</p>',
      card_vis()))

S(thm('Model', 'The constitution',
      f"""<p>It decides which questions to ask, whom to ask, and how an answer moves the split.</p>
<p><b>Nudge:</b> “more to {I('a')}” multiplies {I(r'\tfrac{' + share + '(a)}{' + share + '(b)}')} by a fixed factor {I(r'e^{' + step + '}')}; “more to {I('b')}” divides by it.</p>
<p><b>Multiplier</b> (the round’s format): the member types how many times more {I('a')} deserves; the ratio moves part of the way there.</p>""",
      '',
      formats_vis(), 'Simulated answers on one pair. A nudge uses an answer’s direction, a multiplier its size.'))

S(thm('Model', 'Objective',
      f"""<p><b>Target</b> {I(target)}: the split that gives every pair the ratio the median member wants.</p>
<p><b>Misallocated funding</b> up to time {I('T')}:</p>
<p class="eq">{I(r'\int_0^T \tfrac12 \textstyle\sum_j |' + share + '_t(j) - ' + target + r'(j)|\, dt')}</p>
<p><b>Goal:</b> little misallocated funding for little attention.</p>""",
      '<p>A problem costs its size times how long it lasts.</p>',
      excess_vis(), 'One project; the shaded area is funding paid to the wrong place.'))

S(thm('Observation', 'Nudges settle where answers balance',
      f"""<p>A pair’s ratio stops moving when “more” and “less” are equally likely: at the ratio the median member wants.</p>
<p>Formally, with small steps, nudges descend a convex loss: the expected distance, on a log scale, between wanted and current ratios, weighted by how often each pair is asked.</p>""",
      '<p>Directions balance at the median, not at the mean.</p>',
      loss_vis(), 'Wanted ratios from a skewed distribution.'))

S(thm('Proposition 1', 'Bounded influence',
      f"""<p>One answer changes the ratio of two projects’ shares by a factor of at most {I(r'e^{' + step + '}')}.</p>
<p>If a member answers at most {I('k')} questions a day, then a factor of {I(r'e^{k \cdot ' + step + '}')} bounds how much they change any such ratio in a day.</p>""",
      '<p>Immediate from the nudge. Multipliers have no such bound: a larger typed number moves the ratio more.</p>',
      bound_vis(), f"{I('k = 10')}, {I(step + ' = 0.1')}."))

AG, g13a, g13b = agenda_vis()
S(thm('Proposition 2', 'The agenda is not the verdict',
      f"""<p>Suppose some split gives every pair the ratio its median member wants. Then nudges rest at that split, however often each pair is asked.</p>
<p>If the asked pairs connect all projects and every median is strict, then it is the only resting point.</p>""",
      '<p>Each pair settles at its own median. If these medians clash, the question rates decide (right).</p>',
      AG, 'Simulation with clashing medians: in logs, 1 for pairs (1,2) and (2,3) but 0 for (1,3).'))

S(thm('Proposition 3', 'Maintainers set the overlooked projects',
      f"""<p>Suppose a fraction {I(frac)} of the answers about project {I('j')} come from its maintainers, who want {I('j')} higher by a factor {I(r'e^{' + bias + '}')}.</p>
<p>Then {I('j')}’s resting share grows with {I(frac)}, up to that factor above the consensus.</p>""",
      f"<p>Recusal sets {I(frac + ' = 0')}; without it, {I(frac + r' \approx 1')} for projects nobody else looks at.</p>",
      mixture_vis(), f"{I(bias + ' = 1')}; wanted log-ratios normal, standard deviation 0.71."))

EX, exm, exmean = exaggeration_vis()
S(thm('Proposition 4', 'Exaggeration moves multipliers, not nudges',
      f"""<p>Suppose members type exaggerated multipliers: a wanted ratio {I('x')} is typed as {I(r'x^{' + infl + '}')}, with {I(infl + ' > 1')}.</p>
<p>Then, on a log scale, multipliers rest at {I(infl)} times the mean wanted ratio. Nudges rest at the median, whatever members would type.</p>""",
      '<p>Multipliers average what is typed; nudges only count directions.</p>',
      EX, f"Nine wanted ratios, one extreme; {I(infl + ' = 2.7')}, the simulation’s value."))

S(f'''<section class="slide light">
  <p class="eyebrow">Policy</p>
  <h2>Flag, sample, nudge, escalate</h2>
  <p class="sub">Interested attention is safe as an agenda and harmful as a verdict (Propositions 2 and 3).</p>
  {policy_vis()}
  <p class="why">Each rule is a parameter of the constitution. Step and agenda change the speed; recusal and format change where the split rests.</p>
</section>''')

FR, fs, eng = frontier_vis()
at = {round(a): e for a, e in fs}
S(thm('Simulation', 'Five answers a day halve the AI’s error',
      f"<p>With flag and sample, {at[5]:.1f}% of the funding is misallocated at 5 answered questions a day and {at[10]:.1f}% at 10; with the AI alone, {eng:.1f}%.</p>",
      '', FR, 'Simulation: 98 repos of the round; AI off by about 4.5× on 10% of them; 150 members, 50 maintainers; 12 runs of 180 days.', stack=True, pic_h=430))

DS, rows = designs_vis()
r = lambda k: rows[k]['error'][0] * 100
S(thm('Simulation', 'Ask uninvolved members for a direction',
      f"<p>At about 12 answers a day, random members with nudges leave {r('random members, nudges'):.1f}% misallocated ({r('random members, nudges, flags'):.1f}% with flags); an open forum, {r('open forum, nudges'):.1f}%, with {rows['open forum, nudges']['capture'][0]*100:.1f}% captured.</p>",
      '', DS, 'Simulation, same world. Recusal removes capture; multipliers do not improve on the AI.', stack=True, pic_h=430))

IV, ilo, ihi, ieng = inflated_vis()
S(thm('Simulation', 'If judgments are inflated, humans stop helping',
      f"<p>If judgments themselves are inflated by 2.7, then every human channel leaves between {ilo:.1f}% and {ihi:.1f}% misallocated, against {ieng:.1f}% for the AI alone.</p>",
      '', IV, 'Simulation, same world; the inflation is in what members believe, not in how they type.', stack=True, pic_h=430))

S(f'''<section class="slide light">
  <p class="eyebrow">Related work</p>
  <h2>Closest work, and the difference</h2>
  {related_vis()}
  <p class="why" style="margin-top:30px">New here: a living allocator, interested volunteers, flags as agenda only, nudges, and misallocation against attention.</p>
</section>''')

S('''<section class="slide dark">
  <p class="eyebrow">Summary</p>
  <h2>Interested attention as agenda, never as verdict</h2>
  <div class="rows ruled">
    <div class="row"><span class="n">1</span><p>Nudges rest at medians; the agenda only sets the speed</p></div>
    <div class="row"><span class="n">2</span><p>The policy halves the AI’s error at 5 answers a day</p></div>
    <div class="row"><span class="n">3</span><p>Open: inflated judgments, or only inflated typing?</p></div>
    <div class="row"><span class="n">4</span><p>Next: an adversarial AI; steering the constitution</p></div>
  </div>
</section>''')

slides.append(TITLE)

KATEX_INIT = r"""<script>
document.addEventListener("DOMContentLoaded", function () {
  renderMathInElement(document.body, {delimiters: [{left: "\\(", right: "\\)", display: false}]});
});
</script>"""

STYLE = '''<style>
.sub { font-size: 42px; color: var(--gray); margin-top: -20px; }
.split { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 56px; align-items: center; margin-block: auto; }
.stack { display: flex; flex-direction: column; gap: 10px; margin-top: -10px; }
.stack .pic svg { max-height: var(--ph, 400px); }
.box { background: var(--card); border-left: 10px solid var(--orange); border-radius: 0 18px 18px 0;
  padding: 24px 32px; font-size: 34px; line-height: 1.33; }
.box p { margin: 0 0 16px; } .box p:last-child { margin: 0; }
.box .eq { text-align: center; font-size: 36px; }
.why { font-size: 31px; color: var(--gray); line-height: 1.33; margin-top: 22px; }
.why p { margin: 0 0 12px; }
.pic svg { width: 100%; height: auto; max-height: var(--ph, 560px); }
.pic .cap { font-size: 28px; color: var(--gray); text-align: center; margin-top: 10px; }
.vis { margin-block: auto; display: flex; justify-content: center; }
.flow .step span { font-size: 30px; }
.facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; margin-block: auto; }
.facts .box { font-size: 36px; border-radius: 18px; border-left: none; border-top: 10px solid var(--orange); }
.facts .k { font-weight: 800; color: var(--orange); font-size: 40px; }
.rw { display: grid; grid-template-columns: 1fr 1fr; gap: 28px 36px; margin-top: 10px; }
.rw .box { background: var(--card); border: 3px solid var(--gray-light); border-radius: 24px; padding: 26px 32px; }
.rw h3 { font-size: 40px; margin: 0 0 8px; }
.rw .who { font-size: 30px; color: var(--gray); margin: 0 0 10px; }
.rw .diff { font-size: 32px; margin: 0; }
</style>'''

html = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Steering a Living Allocator · brief</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@300..900&display=swap">
<link rel="stylesheet" href="../assets/deck.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
''' + KATEX_INIT + '''
''' + STYLE + '''
</head>
<body>
<div id="stage">
''' + '\n'.join(f'<!-- {k+1} -->{s}' for k, s in enumerate(slides)) + '''
</div>
<script src="../assets/deck.js"></script>
</body>
</html>
'''
open(OUT, 'w').write(html)
print(len(slides), 'slides')
