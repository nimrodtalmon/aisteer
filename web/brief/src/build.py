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
def motivation_vis():
    items = sorted(json.load(open(os.path.join(ROOT, 'app', 'seed.json')))['items'], key=lambda r: -r['ai_weight'])
    w, h, b = 1660, 560, ''
    # engine
    b += f'<rect x="0" y="150" width="300" height="220" rx="24" fill="{DK}"/>'
    b += text(150, 255, 'engine', 48, LT, weight=800) + text(150, 305, 'updates daily', 30, GL)
    b += f'<path d="M320 260 l70 0 l0 -22 l40 32 l-40 32 l0 -22 l-70 0 Z" fill="{GL}"/>'
    # 98 shares
    X0, Y0, top = 460, 470, items[0]['ai_weight']
    bw = 820 / len(items)
    checked = {12, 47}
    for k, it in enumerate(items):
        hh = it['ai_weight'] / top * 400
        b += f'<rect x="{X0 + k*bw:.1f}" y="{Y0 - hh:.1f}" width="{bw*0.72:.1f}" height="{hh:.1f}" fill="{OR if k in checked else GR}"/>'
    b += text(X0 + 410, 525, '98 repos, $350k', 32, DK, weight=700)
    b += f'<path d="M1340 260 l-70 0 l0 -22 l-40 32 l40 32 l0 -22 l70 0 Z" fill="{GL}"/>'
    # people
    b += f'<rect x="1360" y="150" width="300" height="220" rx="24" fill="{CARD}" stroke="{GL}" stroke-width="3"/>'
    for k in range(3):
        b += head(1450 + k * 60, 205, 14, OR)
    b += text(1510, 305, 'jurors', 48, DK, weight=800) + text(1510, 345, 'check a few pairs', 28, GR)
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
    b += text(X1, Y(truth) - 14, 'median judged gap', 26, GR, 'end')
    b += poly([(X(t), Y(g)) for t, g in enumerate(mul)], BLUE, 5)
    b += poly([(X(t), Y(g)) for t, g in enumerate(nud)], OR, 6)
    b += text(X1, Y(max(mul)) - 4, 'multiplier: one 999× answer', 28, BLUE, 'end', 700)
    b += text(X(8), Y(nud[8]) + 50, 'nudge', 30, OR, 'middle', 800)
    b += text((X0 + X1) / 2, 500, 'answers', 28, GR) + text(X0 - 14, Y(0) + 10, '0', 26, GR, 'end') + text(X0 - 14, Y(2) + 10, '2', 26, GR, 'end')
    b += text(X0, 26, 'gap (log-ratio)', 26, GR, 'start', 700)
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
    b += text((X0 + X1) / 2, 490, 'gap', 28, GR)
    b += text(X0, 30, 'expected |judged gap − gap|', 26, GR, 'start', 700)
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
    b += text(X0, 30, 'change of log-ratio', 26, GR, 'start', 700)
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
    b += text(X0, 30, 'gap between projects 1 and 3', 26, GR, 'start', 700)
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
    b += text(X0, 30, 'resting gap above consensus', 26, GR, 'start', 700)
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
    b += text(390, 410, 'judged gap of one pair (log-ratio)', 26, GR)
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
    b += text(X0 + 10, Y(eng) - 14, f'engine alone: {eng:.1f}%', 28, DK, 'start', 800)
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
    rows = [('engine alone', eng, DK),
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
    b += line(x, 20, x, 470, DK, 4, 'stroke-dasharray="12 8"') + text(x + 14, 506, f'engine alone: {eng:.1f}%', 28, DK, 'start', 800)
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
    boxes = [('Iterative Local Voting', 'Garg et al. 2017', 'random voters move a point locally; no stakeholders, agenda or engine'),
             ('Budget aggregation, medians', 'Freeman et al. 2021 · El-Mhamdi et al. 2023', 'one-shot proposals and strategyproofness; here a stream of small answers'),
             ('Costly voluntary voting', 'Krishna &amp; Morgan 2015 · Müller &amp; Puppe 2020', 'turnout follows intensity: a reason to split attention from verdict'),
             ('Random juries, AI control', 'Kleros 2019 · Greenblatt et al. 2024', 'review where someone is suspicious; here flags only set the agenda')]
    return '<div class="rw">' + ''.join(
        f'<div class="box"><h3>{t}</h3><p class="who">{w}</p><p class="diff">{x}</p></div>' for t, w, x in boxes) + '</div>'


# ---------- notation ----------
I = lambda v: '\\(' + v + '\\)'
alloc, view, step, rate, gap, share, target, loss = (r'\mathrm{alloc}', r'\mathrm{view}', r'\mathrm{step}', r'\mathrm{rate}',
                                                     r'\mathrm{gap}', r'\mathrm{share}', r'\mathrm{target}', r'\mathrm{loss}')
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
  <p class="big">An engine splits a fund; a community keeps it on course</p>
  <p class="muted">Nimrod Talmon · Ben-Gurion University · draft, {DATE}</p>
</section>'''

slides = [TITLE]
S = slides.append

S(f'''<section class="slide light">
  <p class="eyebrow">Motivation</p>
  <h2>An AI splits the money; people can check little</h2>
  <p class="sub">Deep Funding, GG24: 50 jurors, 500 judgments; motivation was the bottleneck.</p>
  <div class="vis">{motivation_vis()}</div>
</section>''')

S(thm('Model', 'Projects, an engine, members',
      f"""<p>{I('m')} projects; log-weights {I(alloc + r'_t \in \mathbb{R}^m')}:</p>
<p class="eq">{I(share + r'_t(j) = \frac{e^{' + alloc + r'_t(j)}}{\sum_k e^{' + alloc + r'_t(k)}}')}</p>
<p><b>Engine:</b> moves {I(alloc + '_t')} over time.</p>
<p>{I('n')} members; view {I(view + r'_i \in \mathbb{R}^m')}; may maintain one project.</p>
<p><b>Actions:</b> flag a project (nearly free); answer a question (one unit of attention).</p>""",
      f"<p>A question: a pair {I('a, b')} with current amounts; more to {I('a')}, about right, or more to {I('b')}.</p>",
      card_vis()))

S(thm('Model', 'The constitution turns answers into movement',
      f"""<p>It fixes the rates {I(rate + '_{ab}')} of asking pairs, who answers, recusal, caps, escalation, the update.</p>
<p>{I(gap + '_{ab} = ' + alloc + '(a) - ' + alloc + '(b)')}; {I('d_{ab}')}: the answerer’s judged gap.</p>
<p><b>Nudge:</b> {I(gap + '_{ab}')} moves by {I(step + r'\cdot\operatorname{sign}(d_{ab} - ' + gap + '_{ab})')}.</p>
<p><b>Multiplier</b> (the round’s): typed {I('x')}; {I(gap + '_{ab}')} moves by {I(lr + r'\cdot(\log x - ' + gap + '_{ab})')}.</p>""",
      '', formats_vis(), f"Simulated answers on one pair; {I(step + '=0.1')}, {I(lr + '=0.3')}."))

S(thm('Model', 'Objectives',
      f"""<p><b>Target:</b> {I(target + '(a) - ' + target + r'(b) = \operatorname{median}(d_{ab})')}.</p>
<p><b>Misallocation:</b> {I(r'\tfrac12 \sum_j |' + share + '(j) - ' + share + '_{' + target + '}(j)|')}.</p>
<p><b>Attention:</b> answered questions per day.</p>
<p><b>Capture:</b> extra share of projects whose maintainers answer.</p>
<p><b>Shortchanged:</b> projects below half their target share.</p>""",
      '<p>Misallocation is the fraction of the fund in the wrong place. Goal: little of it for little attention, with no capture.</p>',
      misalloc_vis(), 'Illustration with ten projects.'))

S(thm('Observation', 'Nudges minimize a loss at the median',
      f"""<p>In the small-step limit, nudges follow the gradient flow of</p>
<p class="eq">{I(loss + '(' + alloc + r') = \tfrac{' + step + r'}{2} \sum_{a \lt b} ' + rate + r'_{ab}\, \mathbb{E}\,|d_{ab} - ' + gap + '_{ab}|')}</p>
<p>The loss is convex; its minimizers are the resting points.</p>""",
      f"<p>The derivative of {I(r'\mathbb{E}|d - ' + gap + '|')} in {I(gap)} is {I(r'\Pr[d \lt ' + gap + r'] - \Pr[d > ' + gap + ']')}: minus the expected answer.</p>",
      loss_vis(), 'Judged gaps from a skewed distribution.'))

S(thm('Proposition 1', 'Bounded influence',
      f"""<p>One answer changes any log-ratio of two shares by at most {I(step)}.</p>
<p>If a member answers at most {I('k')} questions a day, then a factor of {I('e^{k \\cdot ' + step + '}')} bounds how much they change any ratio of two shares in a day.</p>""",
      f"<p>Immediate from the update. A multiplier answer moves a log-ratio by {I(lr + r'\cdot(\log x - ' + gap + ')')}, unbounded as the cap on {I('x')} grows.</p>",
      bound_vis(), f"{I('k = 10')}, {I(step + ' = 0.1')}."))

AG, g13a, g13b = agenda_vis()
S(thm('Proposition 2', 'The agenda is not the verdict',
      f"""<p>If {I(r'\operatorname{median}(d_{ab}) = ' + target + '(a) - ' + target + '(b)')} for every pair, then {I(target)} minimizes the loss for all rates.</p>
<p>If also the asked pairs connect all projects and each {I('d_{ab}')} has positive density at its median, then it is the unique minimizer, up to a constant.</p>""",
      f"<p>Each term is smallest at its median, and {I(target)} attains all of them.</p>",
      AG, f"Simulation, inconsistent medians: 1 on (1,2) and (2,3), 0 on (1,3). The gap ends at {g13a} or {g13b}."))

S(thm('Proposition 3', 'Maintainers set the overlooked projects',
      f"""<p>If maintainers give a fraction {I(frac)} of the answers about {I('j')}, with judged gaps shifted up by {I(bias + ' > 0')}, then the resting gap of {I('j')} grows with {I(frac)}, toward {I(bias)} above consensus.</p>""",
      f"<p>The resting gap is a median of a mixture. Recusal sets {I(frac + ' = 0')}; without it, {I(frac + r' \approx 1')} for projects nobody else looks at.</p>",
      mixture_vis(), f"{I(bias + ' = 1')}; judged gaps normal, standard deviation 0.71."))

EX, exm, exmean = exaggeration_vis()
S(thm('Proposition 4', 'Exaggeration moves multipliers, not nudges',
      f"""<p>If every member types multipliers whose logarithm is inflated by {I(infl + ' > 1')}, then the multiplier rule rests at {I(infl)} times the mean gaps.</p>
<p>Nudges rest at the median gaps, whatever members would have typed.</p>""",
      '<p>Multipliers rest where the expected residual vanishes; nudges where the expected answer vanishes, which depends only on the judged gaps.</p>',
      EX, f"Nine judged gaps, one extreme; {I(infl + ' = 2.7')}, the simulation’s value."))

S(f'''<section class="slide light">
  <p class="eyebrow">Policy</p>
  <h2>Flag, sample, nudge, escalate</h2>
  <p class="sub">Interested attention is safe as an agenda and harmful as a verdict (Propositions 2 and 3).</p>
  {policy_vis()}
  <p class="why">Each rule is a parameter of the constitution. Step and agenda change the speed; recusal and format change where the split rests.</p>
</section>''')

FR, fs, eng = frontier_vis()
at = {round(a): e for a, e in fs}
S(thm('Simulation', 'Five answers a day halve the engine’s error',
      f"<p>With flag and sample, the misallocation is {at[5]:.1f}% at 5 answered questions a day and {at[10]:.1f}% at 10; the engine alone leaves {eng:.1f}%.</p>",
      '', FR, 'Simulation: 98 repos of the round; engine off by about 4.5× on 10% of them; 150 members, 50 maintainers; 12 runs of 180 days.', stack=True, pic_h=430))

DS, rows = designs_vis()
r = lambda k: rows[k]['error'][0] * 100
S(thm('Simulation', 'Ask uninvolved members for a direction',
      f"<p>At about 12 answers a day, random members with nudges leave {r('random members, nudges'):.1f}% misallocated ({r('random members, nudges, flags'):.1f}% with flags); an open forum, {r('open forum, nudges'):.1f}%, with {rows['open forum, nudges']['capture'][0]*100:.1f}% captured.</p>",
      '', DS, 'Simulation, same world. Recusal removes capture; multipliers do not improve on the engine.', stack=True, pic_h=430))

IV, ilo, ihi, ieng = inflated_vis()
S(thm('Simulation', 'If judgments are inflated, humans stop helping',
      f"<p>If judgments themselves are inflated by 2.7, then every human channel leaves between {ilo:.1f}% and {ihi:.1f}% misallocated, against {ieng:.1f}% for the engine alone.</p>",
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
    <div class="row"><span class="n">2</span><p>The policy halves the engine’s error at 5 answers a day</p></div>
    <div class="row"><span class="n">3</span><p>Open: inflated judgments, or only inflated typing?</p></div>
    <div class="row"><span class="n">4</span><p>Next: an adversarial engine; steering the constitution</p></div>
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
.split { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 56px; align-items: center; margin-block: auto; }
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
