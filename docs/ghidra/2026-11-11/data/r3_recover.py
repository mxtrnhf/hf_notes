#!/usr/bin/env python3
"""Sandboxed copy of round3.py (base switched to a scratch dir) that only serves
to recover the P3-DELTA-REJ / C3-DELTA-REJ lists; writes its outputs inside
the sandbox, never touching the record files."""
import csv, collections, json, bisect

base = '/tmp/port163_151/r3sandbox/'
def load(v):
    return list(csv.DictReader(open(base + f'funcs_{v}.tsv'), delimiter='\t', quoting=csv.QUOTE_NONE))
a163 = load('163'); a151 = load('151')
d163 = {r['addr']: r for r in a163}; d151 = {r['addr']: r for r in a151}
def norm(a): return a.rjust(16, '0')
def cls(n):
    for p, c in (('FUN_', 'FUN'), ('rep_', 'rep'), ('CFUN_', 'CFUN')):
        if n.startswith(p): return c
    return 'named'
def S(r): return set(s for s in (r['strings'] or '').split('|') if s)
def C(r): return [c for c in (r['callees'] or '').split(',') if c]
def A(x): return int(x, 16)

matched = json.load(open(base + 'matched.json'))
matched2 = json.load(open(base + 'matched2.json'))
allm = dict(matched); allm.update(matched2)
used151 = {v['addr151'] for v in allm.values()}
n151 = collections.Counter(r['name'] for r in a151)

M = json.load(open('/home/maksim/Development_Highfleet/port_work/M.json'))['M']
inv = {}
okm = 0
for x151, y163 in M.items():
    k151, k163 = norm(x151), norm(y163)
    if k151 in d151 and k163 in d163:
        inv[k163] = k151; okm += 1
print('prior-M anchors loaded:', okm)
m163 = collections.defaultdict(list)
for r in a163: m163[r['name']].append(r['addr'])
for r in a151:
    if cls(r['name']) == 'named' and len(m163.get(r['name'], [])) == 1:
        inv.setdefault(m163[r['name']][0], r['addr'])
for k, v in allm.items(): inv[k] = v['addr151']
print('total anchors:', len(inv))

dpairs = sorted((A(k), A(v['addr151']) - A(k)) for k, v in allm.items())
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

matched3 = {}
targets = [r for r in a163 if cls(r['name']) == 'named' and n151[r['name']] == 0
           and r['thunk'] != 'true' and r['addr'] not in allm]

callers151 = collections.defaultdict(set)
cal151 = {}
for r in a151:
    cs = set(C(r))
    cal151[r['addr']] = cs
    for c in cs: callers151[c].add(r['addr'])

for rnd in range(6):
    scores = {}
    for r in targets:
        if r['addr'] in matched3: continue
        twins = {c: inv[c] for c in C(r) if c in inv}
        if len(twins) < 3: continue
        T = set(twins.values())
        byrare = sorted(T, key=lambda t: len(callers151.get(t, ())))
        cand = set(callers151.get(byrare[0], ()))
        for t in byrare[1:4]:
            cand &= callers151.get(t, set())
        if not cand: continue
        sS = S(r)
        best = []
        n163i = int(r['ninsn']); sz163 = int(r['size'])
        for ga in cand:
            if ga in used151 or ga in {v['addr151'] for v in matched3.values()}: continue
            g = d151[ga]
            if cls(g['name']) not in ('FUN', 'rep', 'CFUN'): continue
            ni, si = int(g['ninsn']), int(g['size'])
            if abs(ni - n163i) > max(8, 0.3 * n163i): continue
            if not (0.65 <= si / max(sz163, 1) <= 1.5): continue
            hit = len(T & cal151[ga])
            if hit < 3 or hit < 0.75 * len(T): continue
            if sS and S(g) and not (sS & S(g)): continue
            best.append((hit, ga))
        if not best: continue
        best.sort(key=lambda z: (-z[0], z[1]))
        if len(best) >= 2 and best[0][0] == best[1][0]: continue
        scores[r['addr']] = (best[0][1], best[0][0], len(T), [d163[c]['name'] for c in twins][:4])
    added = 0
    namx = collections.Counter(d163[a]['name'] for a in scores)
    tgtx = collections.Counter(v[0] for v in scores.values())
    for addr, (ga, hit, tot, evn) in scores.items():
        if tgtx[ga] != 1 or namx[d163[addr]['name']] != 1: continue
        ok = delta_ok(addr, ga)
        if ok is not True:
            print('  P3-DELTA-REJ', addr, d163[addr]['name'], '->', ga)
            continue
        matched3[addr] = dict(addr151=ga, tier=f'prop3r{rnd}', ev=f'callee {hit}/{tot} via {",".join(evn[:3])}')
        inv[addr] = ga
        used151.add(ga)
        added += 1
    print('prop3 round', rnd, 'added', added, 'total', len(matched3))
    if not added: break

callers163 = collections.defaultdict(set)
for r in a163:
    for c in C(r): callers163[c].add(r['addr'])
for rnd in range(4):
    gains = collections.defaultdict(collections.Counter)
    by_n = collections.defaultdict(list)
    for r in a151:
        if cls(r['name']) in ('FUN', 'rep', 'CFUN') and r['addr'] not in used151 and r['addr'] not in {v['addr151'] for v in matched3.values()}:
            by_n[int(r['ninsn'])].append(r)
    for r in targets:
        if r['addr'] in matched3: continue
        cs = callers163.get(r['addr'], set())
        mapped_callers = {inv[c] for c in cs if c in inv}
        if len(mapped_callers) < 3: continue
        n163i = int(r['ninsn']); sz163 = int(r['size'])
        cands = []
        for dn in range(-8, 9):
            cands.extend(by_n.get(n163i + dn, []))
        sS = S(r)
        for g in cands:
            gcalls = callers151.get(g['addr'], set())
            hit = len(mapped_callers & gcalls)
            if hit < 3: continue
            if sS and S(g) and not (sS & S(g)): continue
            si = int(g['size'])
            if not (0.65 <= si / max(sz163, 1) <= 1.5): continue
            gains[r['addr']][g['addr']] = hit
    added = 0
    namx = collections.Counter(d163[a]['name'] for a in gains)
    tgtx = collections.Counter((v.most_common(1)[0][0] if v else '') for v in gains.values())
    for addr, c in gains.items():
        if not c: continue
        ga, hit = c.most_common(1)[0]
        if len(c) >= 2 and c.most_common(2)[1][1] == hit: continue
        if tgtx[ga] != 1 or namx[d163[addr]['name']] != 1: continue
        ok = delta_ok(addr, ga)
        if ok is not True:
            print('  C3-DELTA-REJ', addr, d163[addr]['name'], '->', ga, ' hit', hit)
            continue
        matched3[addr] = dict(addr151=ga, tier=f'caller3r{rnd}', ev=f'callers {hit}')
        inv[addr] = ga
        used151.add(ga)
        added += 1
    print('caller3 round', rnd, 'added', added, 'total', len(matched3))
    if not added: break

json.dump(matched3, open(base + 'matched3.json', 'w'), indent=0)
t = collections.Counter(v['tier'] for v in matched3.values())
print('FINAL', len(matched3), dict(t))
