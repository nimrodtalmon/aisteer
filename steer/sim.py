"""Simulation of a living allocator steered by scarce human attention.

Setting (one run):
  * m items (repositories) share a fund; the allocator keeps log-weights x,
    shares are softmax(x).
  * The community's target log-weights t drift slowly over time.
  * An engine (the AI layer) tracks t but has persistent blind spots:
    a few items are badly over- or under-weighted.
  * n members. Each holds a belief about the log-weights: target plus a
    persistent personal deviation. Some members maintain one item and
    overrate it.
  * Humans act in two ways: a judgment on a pair of items (costs one unit of
    attention) and a flag on an item (nearly free).
  * A policy decides which judgments are asked, to whom, and how an answer
    moves the allocation.

Everything is per day. Attention = number of answered judgments per day.
Error = share of the fund that is misallocated, half the L1 distance between
the allocation and the target, averaged over the second half of the horizon.
"""
from __future__ import annotations
import json, math
from dataclasses import dataclass, field, replace
import numpy as np

DATA = None


def load_data(path="data/gg24.json"):
    global DATA
    if DATA is None:
        DATA = json.load(open(path))
    return DATA


def softmax(x):
    z = np.exp(x - x.max())
    return z / z.sum()


@dataclass
class World:
    """Parameters of the world (not chosen by the designer)."""
    n_members: int = 150
    n_maintainers: int = 50          # members who maintain one item each
    days: int = 180
    top_share: float = 0.033         # calibration: largest share ~3.3% (GG24 seed market leader)
    drift: float = 0.02              # daily std of the target's random walk (log scale)
    belief_sd: float = 0.5           # persistent personal deviation of a member's beliefs
    answer_sd: float = 0.5           # noise of a single answer
    engine_sd: float = 0.15          # small engine error on every item
    blind_frac: float = 0.10         # fraction of items the engine gets badly wrong
    blind_size: float = 1.5          # size of a blind spot (log scale; e^1.5 ~ 4.5x)
    maint_bias: float = 1.0          # how much a maintainer overrates their own item
    inflation: float = 2.7           # multiplier inflation of honest jurors (Verdict: 5x vs 1.8x)
    nudge_inflation: float = 1.0     # sensitivity: inflation also inside more/less answers
    extreme_prob: float = 0.15       # chance a maintainer answers with the maximal multiplier
    max_log_mult: float = math.log(1024)
    # voluntary behavior (per member per day)
    vol_rate_honest: float = 0.02    # spontaneous judgments by uninterested members
    vol_rate_maint: float = 0.20     # spontaneous judgments by maintainers (about their item)
    look_rate: float = 0.05          # chance a member looks at the allocation on a day
    look_top: float = 0.5            # share of looks that go by money (the rest: items the member uses)
    flag_threshold: float = 0.7      # perceived log error that makes a looker flag
    flag_cooldown: int = 14          # days before a member may flag the same item again
    response_prob: float = 0.5       # chance an invited member answers
    sabotage: bool = False           # maintainers answer other pairs toward the smaller project


@dataclass
class Policy:
    """What the designer chooses."""
    name: str = "engine"
    voluntary: bool = False          # use spontaneous judgments
    invited_per_day: int = 0         # invitations sent per day
    pair_rule: str = "random"        # random | money | flags
    update: str = "nudge"            # nudge | multiplier | huber (multiplier with clipped residual)
    huber_c: float = 0.5             # clipping of the residual for the huber rule
    step: float = 0.05               # size of one nudge (log scale)
    lr: float = 0.05                 # learning rate of the multiplier rule
    recusal: bool = True             # maintainers never judge pairs with their own item
    exclude_maintainers: bool = False  # no maintainer is ever invited
    engine_pull: float = 0.0         # daily pull of the allocation back toward the engine's level
    per_member_cap: int = 3          # judgments a member may give per day
    flag_decay: float = 1.0          # daily decay of flag scores (1 = standing flags, cleared by verdicts)
    self_flag_weight: float = 0.5    # weight of a maintainer's flag on their own item
    flag_mix: float = 0.5            # share of invitations that go to flagged items
    money_exp: float = 1.0           # pairs by share: weight share**money_exp (theory: about 0.75 to 0.8)
    escalate_at: float = 0.0         # net flag score that convenes a larger panel (0 = never)
    escalation_panel: int = 9        # judgments asked from the larger panel


def run(world: World, policy: Policy, seed: int = 0, record=False):
    rng = np.random.default_rng(seed)
    d = load_data()
    S = np.array([d["scores"][p] for p in d["personas"]])
    base = np.median(S, 0)
    m = base.size
    # calibrate the scale so that the largest share is world.top_share
    lo, hi = 1e-3, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if softmax(base * mid).max() > world.top_share:
            hi = mid
        else:
            lo = mid
    target = base * lo
    target -= target.mean()

    n = world.n_members
    persona_of = rng.integers(0, len(S), n)
    pers_dev = (S - base)[persona_of] * lo                     # tiny: LLM personas agree
    member_dev = pers_dev + rng.normal(0, world.belief_sd, (n, m))
    member_dev -= member_dev.mean(1, keepdims=True)
    maint_item = -np.ones(n, dtype=int)
    owned = rng.choice(m, world.n_maintainers, replace=False)
    maint_item[:world.n_maintainers] = owned
    is_maint = maint_item >= 0

    blind = rng.random(m) < world.blind_frac
    engine_err = rng.normal(0, world.engine_sd, m) + blind * rng.choice([-1, 1], m) * world.blind_size
    x = target + engine_err
    flags = np.zeros(m)
    last_flag = -np.full((n, m), 10**6)
    n_flags = [0, 0]
    esc = [0]
    short = []
    errs, att_used, capture, hist = [], [], [], []

    def belief(i, t):
        b = t + member_dev[i]
        if is_maint[i]:
            b = b.copy(); b[maint_item[i]] += world.maint_bias
        return b

    def answer(i, a, b, t):
        """Returns the movement of (x_a - x_b) caused by member i's answer."""
        bel = belief(i, t)
        diff = bel[a] - bel[b] + rng.normal(0, world.answer_sd)
        cur = x[a] - x[b]
        if (world.sabotage and policy.update == "nudge" and is_maint[i]
                and maint_item[i] not in (a, b)):
            return policy.step * (1.0 if x[a] < x[b] else -1.0)   # push toward the smaller one
        if policy.update == "nudge":
            gap = world.nudge_inflation * diff - cur
            if abs(gap) < 0.1:
                return 0.0
            return policy.step * np.sign(gap)
        # multiplier rule: reported log-ratio, inflated, capped, then an L2 step in log space
        rep = world.inflation * diff
        if is_maint[i] and maint_item[i] in (a, b) and rng.random() < world.extreme_prob:
            rep = world.max_log_mult * (1 if maint_item[i] == a else -1)
        rep = float(np.clip(rep, -world.max_log_mult, world.max_log_mult))
        if policy.update == "huber":
            return policy.lr * float(np.clip(rep - cur, -policy.huber_c, policy.huber_c)) * 2
        return policy.lr * (rep - cur)

    def apply(a, b, mv):
        x[a] += mv / 2; x[b] -= mv / 2

    def pick_pair(focus=None):
        share = softmax(x)
        if policy.pair_rule == "random":
            a, b = rng.choice(m, 2, replace=False); return a, b
        w_money = share ** policy.money_exp + (1.0 / m) ** policy.money_exp * 0.05
        if policy.pair_rule == "money":
            a = rng.choice(m, p=w_money / w_money.sum())
        else:  # flags: part of the invitations go to flagged items, the rest by money
            net = np.abs(flags)
            if net.sum() > 1e-6 and rng.random() < policy.flag_mix:
                a = rng.choice(m, p=net / net.sum())
            else:
                a = rng.choice(m, p=w_money / w_money.sum())
        b = rng.integers(m)
        while b == a:
            b = rng.integers(m)
        return a, b

    engine = target + engine_err
    for day in range(world.days):
        target = target + rng.normal(0, world.drift, m)
        target -= target.mean()
        prev_engine, engine = engine, target + engine_err
        x += engine - prev_engine          # the AI layer follows changes in the world
        used = np.zeros(n, dtype=int)
        att = 0
        # looking and flagging (cheap)
        lookers = np.where(rng.random(n) < world.look_rate)[0]
        cur = x - x.mean()
        shr = softmax(x)
        for i in lookers:
            if is_maint[i]:
                j = maint_item[i]
            elif rng.random() < world.look_top:
                j = rng.choice(m, p=shr)
            else:
                j = rng.integers(m)
            if day < last_flag[i, j] + world.flag_cooldown:
                continue
            bel = belief(i, target)
            e = (bel[j] - bel.mean()) - cur[j]
            if abs(e) > world.flag_threshold:
                wgt = policy.self_flag_weight if maint_item[i] == j else 1.0
                flags[j] += wgt * np.sign(e)       # signed: opposite flags cancel
                last_flag[i, j] = day
                n_flags[0 if blind[j] else 1] += 1
        # voluntary judgments
        if policy.voluntary:
            for i in range(n):
                rate = world.vol_rate_maint if is_maint[i] else world.vol_rate_honest
                k = rng.poisson(rate)
                for _ in range(min(k, policy.per_member_cap - used[i])):
                    if is_maint[i]:
                        a = maint_item[i]; b = rng.integers(m)
                        if b == a: continue
                    else:  # uninterested volunteers look at the top of the list
                        p = softmax(x); a, b = rng.choice(m, 2, replace=False, p=p)
                    apply(a, b, answer(i, a, b, target)); used[i] += 1; att += 1
        # invited judgments (sortition of attention)
        for _ in range(policy.invited_per_day):
            a, b = pick_pair()
            pool = [i for i in range(n) if used[i] < policy.per_member_cap and
                    not (policy.recusal and maint_item[i] in (a, b)) and
                    not (policy.exclude_maintainers and is_maint[i])]
            i = pool[rng.integers(len(pool))]
            if rng.random() > world.response_prob:
                continue
            apply(a, b, answer(i, a, b, target)); used[i] += 1; att += 1
            flags[a] *= 0.7; flags[b] *= 0.7     # a flagged item that got a verdict cools down
        if policy.escalate_at > 0:
            for j in np.where(np.abs(flags) >= policy.escalate_at)[0]:
                esc[0] += 1
                for _ in range(policy.escalation_panel):
                    b = rng.integers(m)
                    if b == j: continue
                    pool = [i for i in range(n) if not (policy.recusal and maint_item[i] in (j, b))]
                    i = pool[rng.integers(len(pool))]
                    apply(j, b, answer(i, j, b, target)); att += 1
                flags[j] = 0.0
        flags *= policy.flag_decay
        x += policy.engine_pull * (engine - x)
        sx, st = softmax(x), softmax(target)
        errs.append(0.5 * np.abs(sx - st).sum())
        capture.append((sx[owned] - st[owned]).sum())
        short.append(float(np.mean(sx < 0.5 * st)))
        att_used.append(att)
        if record:
            hist.append(sx.copy())
    half = world.days // 2
    out = dict(error=float(np.mean(errs[half:])), attention=float(np.mean(att_used)),
               capture=float(np.mean(capture[half:])),
               shortchanged=float(np.mean(short[half:])),
               flags_on_blind=n_flags[0], flags_other=n_flags[1], escalations=esc[0],
               engine_error=float(0.5 * np.abs(softmax(engine) - softmax(target)).sum()))
    if record:
        out["errors"] = errs; out["hist"] = hist
    return out


POLICIES = {
    "engine only": Policy("engine only"),
    "open, multipliers": Policy("open, multipliers", voluntary=True, update="multiplier", recusal=False),
    "open, nudges": Policy("open, nudges", voluntary=True, update="nudge", recusal=False),
    "panel, random pairs": Policy("panel, random pairs", pair_rule="random"),
    "panel, money-weighted": Policy("panel, money-weighted", pair_rule="money"),
    "flag and sample": Policy("flag and sample", pair_rule="flags"),
    "flag, sample, escalate": Policy("flag, sample, escalate", pair_rule="flags", escalate_at=4.0),
    "open, multipliers (huber)": Policy("open, multipliers (huber)", voluntary=True, update="huber", recusal=False),
    "panel, multipliers": Policy("panel, multipliers", pair_rule="money", update="multiplier"),
}
