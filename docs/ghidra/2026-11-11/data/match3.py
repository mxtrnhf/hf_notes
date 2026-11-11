import csv, collections, json, statistics

base = '/tmp/port163_151/'

def load(v):
    return list(csv.DictReader(open(base + f'funcs_{v}.tsv'), delimiter='\t', quoting=csv.QUOTE_NONE))

a163 = load('163'); a151 = load('151')
d163 = {r['addr']: r for r in a163}
d151 = {r['addr']: r for r in a151}

def cls(n):
    for p, c in (('FUN_', 'FUN'), ('rep_', 'rep'), ('CFUN_', 'CFUN')):
        if n.startswith(p): return c
    return 'named'
def S(r): return set(s for s in (r['strings'] or '').split('|') if s)
def C(r): return [c for c in (r['callees'] or '').split(',') if c]

n151 = collections.Counter(r['name'] for r in a151)
targets = [r for r in a163 if cls(r['name']) == 'named'
           and n151[r['name']] == 0 and r['thunk'] != 'true']
print('targets:', len(targets), flush=True)

h163 = collections.defaultdict(list); h151 = collections.defaultdict(list)
for r in a163: h163[(r['mnhash'], r['ninsn'])].append(r['addr'])
for r in a151: h151[(r['mnhash'], r['ninsn'])].append(r['addr'])

matched = {}
used151 = set()

def add(a163a, a151a, tier, ev):
    matched[a163a] = dict(addr151=a151a, tier=tier, ev=ev)
    used151.add(a151a)

# ---- tier 1: unique exact mnemonic hash + ninsn ----
t1 = []
for r in targets:
    k = (r['mnhash'], r['ninsn'])
    if int(r['ninsn']) < 12: continue
    if len(h163[k]) == 1 and len(h151.get(k, [])) == 1:
        t = d151[h151[k][0]]
        if cls(t['name']) in ('FUN', 'rep', 'CFUN'):
            t1.append((r, t))
cnt_t = collections.Counter(x[1]['addr'] for x in t1)
cnt_n = collections.Counter(x[0]['name'] for x in t1)
t1rej = 0
for r, t in t1:
    if cnt_t[t['addr']] == 1 and cnt_n[r['name']] == 1:
        add(r['addr'], t['addr'], 'hash', 'ninsn=' + r['ninsn'])
    else:
        t1rej += 1
print('tier1 hash:', len(matched), 'rejected-dup:', t1rej, flush=True)

# delta profile from tier-1 pairs (163 addr -> 151 addr, both 64-bit ints)
def A(a): return int(a, 16)
dpairs = sorted((A(k), A(v['addr151']) - A(k)) for k, v in matched.items() if v['tier'] == 'hash')

# piecewise-linear delta from bracketing tier-1 pairs; reject only gross outliers
import bisect
dx = [p[0] for p in dpairs]
def delta_ok(a163a, a151a, win=0x100000, tol=0x40000):
    x = A(a163a)
    i = bisect.bisect_left(dx, x)
    below = dpairs[i - 1] if i > 0 else None
    above = dpairs[i] if i < len(dpairs) else None
    near = [p for p in (below, above) if p and abs(p[0] - x) <= win]
    if len(near) < 2: return 'weak'
    (x0, d0), (x1, d1) = below, above
    if x1 == x0:
        d_hat = d0
    else:
        d_hat = d0 + (d1 - d0) * (x - x0) / (x1 - x0)
    delta = A(a151a) - x
    return True if abs(delta - d_hat) <= tol else False

# ---- tier 2: distinctive string sets + delta consistency ----
sidx151 = collections.defaultdict(set)
for r in a151:
    if cls(r['name']) in ('FUN', 'rep', 'CFUN') and r['addr'] not in used151:
        for s in S(r): sidx151[s].add(r['addr'])
t2 = []
for r in targets:
    if r['addr'] in matched: continue
    ss = S(r)
    if not ss: continue
    cands = None
    for s in ss:
        v = sidx151.get(s, set())
        cands = set(v) if cands is None else (cands & v)
    if cands is None or len(cands) != 1: continue
    g = d151[list(cands)[0]]
    if not (ss <= S(g)): continue
    n163i, n151i = int(r['ninsn']), int(g['ninsn'])
    if abs(n163i - n151i) > max(4, 0.15 * n163i): continue
    t2.append((r, g, len(ss)))
cnt_t = collections.Counter(x[1]['addr'] for x in t2)
cnt_n = collections.Counter(x[0]['name'] for x in t2)
t2rej = 0
for r, g, ns in t2:
    ok = delta_ok(r['addr'], g['addr'])
    if cnt_t[g['addr']] == 1 and cnt_n[r['name']] == 1 and g['addr'] not in used151 and ok is True:
        add(r['addr'], g['addr'], 'strings', f'strset={ns}')
    else:
        t2rej += 1
        if ok is not True:
            print('  T2-DELTA-REJ', r['addr'], r['name'], '->', g['addr'], 'd-ok=', ok, flush=True)
print('after tier2 strings:', len(matched), 'rejected:', t2rej, flush=True)

# ---- anchors ----
M = json.load(open('/home/maksim/Development_Highfleet/port_work/M.json'))['M']
inv = {}
for x151, y163 in M.items():
    if x151 in d151 and y163 in d163:
        inv[y163] = x151
m163 = collections.defaultdict(list)
for r in a163: m163[r['name']].append(r['addr'])
for r in a151:
    if cls(r['name']) != 'named': continue
    v = m163.get(r['name'], [])
    if len(v) == 1 and v[0] not in inv:
        inv[v[0]] = r['addr']
for k, v in matched.items(): inv[k] = v['addr151']
print('anchors inv total:', len(inv), flush=True)

# ---- tier 3: propagation by anchored callees + delta consistency ----
callers151 = collections.defaultdict(set)
cal151 = {}
for r in a151:
    cs = set(C(r))
    cal151[r['addr']] = cs
    for c in cs: callers151[c].add(r['addr'])

for rnd in range(4):
    scores = {}
    pool_n = collections.defaultdict(list)
    for r in a151:
        if cls(r['name']) in ('FUN', 'rep', 'CFUN') and r['addr'] not in used151:
            pool_n[int(r['ninsn'])].append(r['addr'])
    for r in targets:
        if r['addr'] in matched: continue
        twins = {}
        for c in C(r):
            t = inv.get(c)
            if t and t in d151: twins[c] = t
        if len(twins) < 3: continue
        T = set(twins.values())
        byrare = sorted(T, key=lambda t: len(callers151.get(t, ())))
        cand = set(callers151.get(byrare[0], ()))
        for t in byrare[1:4]:
            cand &= callers151.get(t, set())
        sS = S(r)
        best = []
        n163i = int(r['ninsn']); sz163 = int(r['size'])
        for ga in cand:
            if ga in used151: continue
            g = d151[ga]
            if cls(g['name']) not in ('FUN', 'rep', 'CFUN'): continue
            ni, si = int(g['ninsn']), int(g['size'])
            if abs(ni - n163i) > max(6, 0.25 * n163i): continue
            if not (0.7 <= si / max(sz163, 1) <= 1.4): continue
            hit = len(T & cal151[ga])
            if hit < 3 or hit < 0.75 * len(T): continue
            if sS and S(g) and not (sS & S(g)): continue
            best.append((hit, ga))
        if not best: continue
        best.sort(key=lambda z: (-z[0], z[1]))
        if len(best) >= 2 and best[0][0] == best[1][0]: continue
        scores[r['addr']] = (best[0][1], best[0][0], len(T))
    added = 0
    nam = collections.Counter(d163[addr]['name'] for addr in scores)
    tgt = collections.Counter(v[0] for v in scores.values())
    for addr, (ga, hit, tot) in scores.items():
        if tgt[ga] != 1 or nam[d163[addr]['name']] != 1: continue
        ok = delta_ok(addr, ga)
        if ok is not True:
            print('  T3-DELTA-REJ', addr, d163[addr]['name'], '->', ga, 'd-ok=', ok, flush=True)
            continue
        add(addr, ga, f'prop{rnd}', f'callee {hit}/{tot}')
        inv[addr] = ga
        added += 1
    print('round', rnd, 'added', added, 'total', len(matched), flush=True)
    if not added: break

json.dump(matched, open(base + 'matched.json', 'w'), indent=0)
t = collections.Counter(v['tier'] for v in matched.values())
print('FINAL', len(matched), dict(t), flush=True)
pl = sum(1 for k in matched if int(d163[k]['hasplate'] or 0) > 30)
print('with plates to port:', pl, flush=True)
