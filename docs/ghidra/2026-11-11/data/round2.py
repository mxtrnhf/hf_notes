import csv, collections, json, bisect

base = '/tmp/port163_151/'
def load(v):
    return list(csv.DictReader(open(base + f'funcs_{v}.tsv'), delimiter='\t', quoting=csv.QUOTE_NONE))
a163 = load('163'); a151 = load('151')
d163 = {r['addr']: r for r in a163}; d151 = {r['addr']: r for r in a151}
def cls(n):
    for p, c in (('FUN_', 'FUN'), ('rep_', 'rep'), ('CFUN_', 'CFUN')):
        if n.startswith(p): return c
    return 'named'
def S(r): return set(s for s in (r['strings'] or '').split('|') if s)
def C(r): return [c for c in (r['callees'] or '').split(',') if c]
def A(x): return int(x, 16)

matched = json.load(open(base + 'matched.json'))
used151 = {v['addr151'] for v in matched.values()}
n151 = collections.Counter(r['name'] for r in a151)

M = json.load(open('/home/maksim/Development_Highfleet/port_work/M.json'))['M']
inv = {}
for x151, y163 in M.items():
    if x151 in d151 and y163 in d163: inv[y163] = x151
m163 = collections.defaultdict(list)
for r in a163: m163[r['name']].append(r['addr'])
for r in a151:
    if cls(r['name']) == 'named' and len(m163.get(r['name'], [])) == 1:
        inv.setdefault(m163[r['name']][0], r['addr'])
for k, v in matched.items(): inv[k] = v['addr151']

dpairs = sorted((A(k), A(v['addr151']) - A(k)) for k, v in matched.items())
dx = [p[0] for p in dpairs]
def delta_ok(a163a, a151a, win=0x100000, tol=0x40000):
    x = A(a163a)
    i = bisect.bisect_left(dx, x)
    below = dpairs[i - 1] if i > 0 else None
    above = dpairs[i] if i < len(dpairs) else None
    near = [p for p in (below, above) if p and abs(p[0] - x) <= win]
    if len(near) < 2: return 'weak'
    (x0, d0), (x1, d1) = below, above
    d_hat = d0 if x1 == x0 else d0 + (d1 - d0) * (x - x0) / (x1 - x0)
    return abs((A(a151a) - x) - d_hat) <= tol

matched2 = {}
def add(a163a, a151a, tier, ev):
    matched2[a163a] = dict(addr151=a151a, tier=tier, ev=ev)

# ---- tier group: uniform-named ICF groups ----
g163 = collections.defaultdict(list); g151 = collections.defaultdict(list)
for r in a163:
    if cls(r['name']) == 'named': g163[(r['mnhash'], r['ninsn'])].append(r)
for r in a151:
    if cls(r['name']) in ('FUN', 'rep', 'CFUN') and r['addr'] not in used151:
        g151[(r['mnhash'], r['ninsn'])].append(r)
for k, members in g163.items():
    if len({m['name'] for m in members}) != 1: continue
    name = members[0]['name']
    if k not in g151: continue
    tw = g151[k]
    if any(t['addr'] in used151 for t in tw): continue
    if len(tw) != len(members): continue
    if n151[name] > 0: continue
    em = sorted(m['addr'] for m in members); et = sorted(t['addr'] for t in tw)
    for a, b in zip(em, et):
        add(a, b, 'group', f'icf{len(tw)}')
print('tier group added:', len(matched2), flush=True)
used151 |= {v['addr151'] for v in matched2.values()}
for k, v in matched2.items(): inv[k] = v['addr151']

# ---- tier strings2: subset string matching + anchored-call support ----
sidx151 = collections.defaultdict(set)
for r in a151:
    if cls(r['name']) in ('FUN', 'rep', 'CFUN') and r['addr'] not in used151:
        for s in S(r): sidx151[s].add(r['addr'])
targets = [r for r in a163 if cls(r['name']) == 'named' and n151[r['name']] == 0
           and r['thunk'] != 'true' and r['addr'] not in matched and r['addr'] not in matcheded2] if False else [
           r for r in a163 if cls(r['name']) == 'named' and n151[r['name']] == 0
           and r['thunk'] != 'true' and r['addr'] not in matched and r['addr'] not in matched2]
t2 = []
for r in targets:
    ss = S(r)
    if not ss: continue
    cands = None
    for s in ss:
        v = sidx151.get(s, set())
        cands = set(v) if cands is None else (cands & v)
    if not cands: continue
    scored = []
    for ga in cands:
        g = d151[ga]
        ov = len(ss & S(g))
        if ov < max(1, int(0.6 * len(ss))): continue
        twins = {inv[c] for c in C(r) if c in inv}
        hitc = sum(1 for c in C(g) if c in twins)
        nc = max(len([c for c in C(r) if c in inv]), 1)
        n163i = int(r['ninsn']); n151i = int(g['ninsn'])
        if abs(n163i - n151i) > max(8, 0.35 * n163i): continue
        sz = int(g['size']) / max(int(r['size']), 1)
        if not (0.6 <= sz <= 1.6): continue
        score = ov / max(len(ss | S(g)), 1) * 0.6 + min(hitc / nc, 1.0) * 0.4
        ok = delta_ok(r['addr'], g['addr'])
        if ok is True: scored.append((score, ga, ov, hitc, nc))
        else: print('  T2-DELTA-REJ', r['addr'], r['name'], '->', g['addr'], flush=True)
    if not scored: continue
    scored.sort(reverse=True)
    if len(scored) >= 2 and scored[0][0] < scored[1][0] * 1.25: continue
    t2.append((r, scored[0]))
cnt_n = collections.Counter(x[0]['name'] for x in t2)
cnt_t = collections.Counter(x[1][1] for x in t2)
for r, (score, ga, ov, hitc, nc) in t2:
    if cnt_n[r['name']] == 1 and cnt_t[ga] == 1 and ga not in used151:
        add(r['addr'], ga, 'strings2', f'str={ov} callee={hitc}/{nc}')
print('after strings2:', len(matched2), flush=True)
used151 |= {v['addr151'] for v in matched2.values()}
for k, v in matched2.items(): inv[k] = v['addr151']

# ---- tier prop2: relaxed propagation ----
callers151 = collections.defaultdict(set)
cal151 = {}
for r in a151:
    cs = set(C(r))
    cal151[r['addr']] = cs
    for c in cs: callers151[c].add(r['addr'])
for rnd in range(5):
    scores = {}
    for r in targets:
        if r['addr'] in matched2: continue
        twins = {c: inv[c] for c in C(r) if c in inv}
        if len(twins) < 2: continue
        T = set(twins.values())
        byrare = sorted(T, key=lambda t: len(callers151.get(t, ())))
        cand = set(callers151.get(byrare[0], ()))
        for t in byrare[1:3]:
            cand &= callers151.get(t, set())
        sS = S(r)
        best = []
        n163i = int(r['ninsn']); sz163 = int(r['size'])
        for ga in cand:
            if ga in used151: continue
            g = d151[ga]
            if cls(g['name']) not in ('FUN', 'rep', 'CFUN'): continue
            ni, si = int(g['ninsn']), int(g['size'])
            if abs(ni - n163i) > max(10, 0.4 * n163i): continue
            if not (0.6 <= si / max(sz163, 1) <= 1.6): continue
            hit = len(T & cal151[ga])
            if hit < 2 or hit < 0.7 * len(T): continue
            if sS and S(g) and not (sS & S(g)): continue
            best.append((hit, ga))
        if not best: continue
        best.sort(key=lambda z: (-z[0], z[1]))
        if len(best) >= 2 and best[0][0] == best[1][0] and best[0][0] <= 3: continue
        if len(best) >= 3 and best[0][0] == best[1][0]: continue
        scores[r['addr']] = (best[0][1], best[0][0], len(T))
    added = 0
    namx = collections.Counter(d163[a]['name'] for a in scores)
    tgtx = collections.Counter(v[0] for v in scores.values())
    for addr, (ga, hit, tot) in scores.items():
        if tgtx[ga] != 1 or namx[d163[addr]['name']] != 1 or ga in used151: continue
        ok = delta_ok(addr, ga)
        if ok is not True:
            print('  T3-DELTA-REJ', addr, d163[addr]['name'], '->', ga, flush=True)
            continue
        add(addr, ga, f'prop2r{rnd}', f'callee {hit}/{tot}')
        inv[addr] = ga
        used151.add(ga)
        added += 1
    print('prop2 round', rnd, 'added', added, 'total', len(matched2), flush=True)
    if not added: break

json.dump(matched2, open(base + 'matched2.json', 'w'), indent=0)
t = collections.Counter(v['tier'] for v in matched2.values())
print('FINAL ROUND2', len(matched2), dict(t), flush=True)
pl = sum(1 for k in matched2 if int(d163[k]['hasplate'] or 0) > 30)
print('with plates:', pl)
