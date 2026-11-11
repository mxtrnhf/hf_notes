import csv, collections, json
base = '/tmp/port163_151/'
def load(v):
    return list(csv.DictReader(open(base + f'funcs_{v}.tsv'), delimiter='\t', quoting=csv.QUOTE_NONE))
a163 = load('163'); a151 = load('151')
d163 = {r['addr']: r for r in a163}; d151 = {r['addr']: r for r in a151}
def cls(n):
    for p, c in (('FUN_', 'FUN'), ('rep_', 'rep'), ('CFUN_', 'CFUN')):
        if n.startswith(p): return c
    return 'named'
def C(r): return [c for c in (r['callees'] or '').split(',') if c]
def S(r): return set(s for s in (r['strings'] or '').split('|') if s)

# rebuild tier-1 rejected-dup list (same logic as match3)
n151 = collections.Counter(r['name'] for r in a151)
matched = json.load(open(base + 'matched.json'))
used = {v['addr151'] for v in matched.values()}
h163 = collections.defaultdict(list); h151 = collections.defaultdict(list)
for r in a163: h163[(r['mnhash'], r['ninsn'])].append(r['addr'])
for r in a151: h151[(r['mnhash'], r['ninsn'])].append(r['addr'])
t1 = []
for r in a163:
    if cls(r['name']) != 'named' or n151[r['name']] != 0 or r['thunk'] == 'true': continue
    k = (r['mnhash'], r['ninsn'])
    if int(r['ninsn']) < 12: continue
    if len(h163[k]) == 1 and len(h151.get(k, [])) == 1:
        t = d151[h151[k][0]]
        if cls(t['name']) in ('FUN', 'rep', 'CFUN'):
            t1.append((r, t))
cnt_t = collections.Counter(x[1]['addr'] for x in t1)
cnt_n = collections.Counter(x[0]['name'] for x in t1)
print('=== tier1 dup rejects (round 1) ===')
for r, t in t1:
    if cnt_t[t['addr']] == 1 and cnt_n[r['name']] == 1: continue
    print(' 163', r['addr'], r['name'], '| twin:', t['addr'], t['name'], '| group163:', [d163[a]['name'] for a in h163[(r['mnhash'], r['ninsn'])]], '| taken-dup:', cnt_t[t['addr']], cnt_n[r['name']])

# aircraftStateHandler: local search in aircraft cluster
M = json.load(open('/home/maksim/Development_Highfleet/port_work/M.json'))['M']
inv = {}
for x151, y163 in M.items():
    if x151 in d151 and y163 in d163: inv[y163] = x151
m2 = json.load(open(base + 'matched.json'))
for k, v in m2.items(): inv[k] = v['addr151']
src = d163['000000014000fbc0']
twins = [inv[c] for c in C(src) if c in inv]
print('=== aircraftStateHandler twins:', twins)
lo, hi = 0x14000e800, 0x140010400
best = []
for r in a151:
    a = int(r['addr'], 16)
    if not (lo <= a <= hi): continue
    if cls(r['name']) not in ('FUN', 'rep', 'CFUN'): continue
    if r['addr'] in used: continue
    cs = set(C(r))
    hit = sum(1 for t in twins if t in cs)
    best.append((hit, r['addr'], r['name'], r['ninsn'], r['size']))
best.sort(reverse=True)
print('cluster candidates by anchored-callee overlap (163 ninsn=%s, size=%s):' % (src['ninsn'], src['size']))
for b in best[:8]: print('  hit=%d %s %s ninsn=%s size=%s' % b)
