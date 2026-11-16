"""Paper figures from results/*.json (PDF + PNG in figures/)."""
import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BLUE, GREY, LGREY, INK, QUIET = '#2a78d6', '#8a8984', '#c9c8c2', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': QUIET, 'axes.labelcolor': INK, 'xtick.color': QUIET, 'ytick.color': QUIET})
d = json.load(open('results/frontier_base.json'))
fig, ax = plt.subplots(figsize=(5.2, 3.0))
for pol, lab, c, ls, a in (('panel, random pairs', 'Panel, random pairs', LGREY, '-', 1), ('panel, money-weighted', 'Panel, pairs by money', GREY, '-', 1),
                           ('flag and sample', 'Flag and sample', BLUE, '-', 1), ('flag, sample, escalate', 'Flag, sample, escalate', BLUE, '--', 0.6)):
    pts = sorted((d[f'{pol}|{K}']['attention'][0], 100 * d[f'{pol}|{K}']['error'][0]) for K in (2, 5, 10, 20, 40, 80))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, color=c, alpha=a, lw=2, marker='o', ms=4, label=lab)
e = 100 * d['engine only|0']['error'][0]
ax.axhline(e, color=QUIET, ls=(0, (4, 3)), lw=1); ax.text(1.0, e + 0.5, f'AI layer alone {e:.1f}%', va='bottom', fontsize=8, color=QUIET)
for k, lab in (('open, nudges|0', 'Open forum, nudges'), ('open, multipliers|0', 'Open forum, multipliers')):
    x, y = d[k]['attention'][0], 100 * d[k]['error'][0]
    ax.plot([x], [y], 's', mfc='none', mec=QUIET); ax.text(x * 1.08, y, f'{lab} {y:.1f}%', va='center', fontsize=8, color=QUIET)
ax.set_xscale('log'); ax.set_xticks([1, 2, 5, 10, 20, 40]); ax.set_xticklabels(['1', '2', '5', '10', '20', '40'])
ax.set_xlabel('Answered questions per day'); ax.set_ylabel('Fund misallocated (%)'); ax.set_ylim(0, 23)
ax.grid(axis='y', color='#e6e5e0', lw=0.8); ax.legend(frameon=False, fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig('figures/frontier.pdf'); fig.savefig('figures/frontier.png', dpi=200)

s = json.load(open('results/steering_tuned_base.json'))
names = list(s)[::-1]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(5.6, 2.6), sharey=True, gridspec_kw={'width_ratios': [1.4, 1]})
col = [BLUE if n == 'panel, nudges, flags' else GREY for n in names]
a1.barh(names, [100 * s[n]['error'][0] for n in names], color=col); a1.set_xlabel('Fund misallocated (%)')
a2.barh(names, [100 * s[n]['capture'][0] for n in names], color=col); a2.axvline(0, color=QUIET, lw=0.8); a2.set_xlabel('Captured by maintainers (%)')
for ax in (a1, a2): ax.tick_params(axis='y', length=0)
fig.tight_layout(); fig.savefig('figures/steering.pdf', bbox_inches='tight'); fig.savefig('figures/steering.png', dpi=200, bbox_inches='tight')
print('ok')
