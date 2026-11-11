#!/usr/bin/env python3
"""Score 1.151 candidates per open 1.163 target using:
   - string-reference text overlap (Jaccard + subset ratio)
   - mapped-callee overlap (163 callees mapped through verified pairs)
Prints top candidates per target."""
import json
from collections import Counter

TXT = '/tmp/port163_151/'

def load_funcs(path):
    out = {}
    with open(path) as f:
        h = f.readline().rstrip('\n').split('\t')
        for line in f:
            p = line.rstrip('\n').split('\t')
            d = dict(zip(h, p))
            out[int(d['addr'],16)] = d
    return out

f163 = load_funcs(TXT + 'funcs_163.tsv')
f151 = load_funcs(TXT + 'funcs_151.tsv')

pair163to151 = {}
for path in [TXT+'matched.tsv', TXT+'matched2.tsv', TXT+'matched3.tsv']:
    with open(path) as f:
        f.readline()
        for line in f:
            a,b,t,_ = line.rstrip('\n').split('\t')
            pair163to151[int(a,16)] = int(b,16)

d = json.load(open(TXT + 'candmod.json'))

def strings_set(d):
    if not d['strings']:
        return set()
    return set(s.strip() for s in d['strings'].split('|') if s.strip())

def callees_set(d):
    if not d['callees']:
        return set()
    return set(a for a in d['callees'].split(',') if a)

results = {}
for k, v in d.items():
    a163 = int(k, 16)
    t = f163.get(a163)
    if not t:
        continue
    tstrings = strings_set(t)
    tcallees = callees_set(t)
    tcalled_mapped = set()
    for ca in tcallees:
        try:
            a = int(ca, 16)
        except ValueError:
            continue
        if a in pair163to151:
            tcalled_mapped.add(pair163to151[a])
    n163 = v['n163']
    if n163 >= 1000:
        nlo, nhi = int(n163*0.35), int(n163*1.8)
    elif n163 >= 100:
        nlo, nhi = int(n163*0.3), int(n163*2.5)
    elif n163 >= 40:
        nlo, nhi = int(n163*0.4), int(n163*3)
    else:
        nlo, nhi = 1, max(8, n163*4)
    window = 0x60000 if n163 >= 500 else 0x40000
    expect = int(round(v['expect']))
    scored = []
    a15_entries = [int(x, 16) for x in open(TXT+'cand151_addrs.txt').read().split()]
    for a151 in a15_entries:
        if not (expect - window <= a151 <= expect + window):
            continue
        c = f151.get(a151)
        if not c:
            continue
        n151 = int(c['ninsn'])
        if not (nlo <= n151 <= nhi):
            continue
        cstrings = strings_set(c)
        inter = tstrings & cstrings
        jac = len(inter) / len(tstrings | cstrings) if (tstrings | cstrings) else 0.0
        subset = len(inter) / len(tstrings) if tstrings else 0.0
        ccallees = callees_set(c)
        cm = set()
        for ca in ccallees:
            try:
                cm.add(int(ca,16))
            except ValueError:
                pass
        callee_hit = len(tcalled_mapped & cm) / max(1, len(tcalled_mapped))
        dn = abs(n151 - n163) / max(1, n163)
        ddev = abs(a151 - expect)
        score = 3.0*subset + 2.0*jac + 2.5*callee_hit
        scored.append((dict(a=f"{a151:x}", nm=c['name'], n=n151, jac=round(jac,3),
                            subset=round(subset,3), calee=round(callee_hit,3),
                            ddev=ddev, dn=round(dn,2), score=round(score,3))))
    scored.sort(key=lambda x: -x['score'])
    results[k] = dict(name163=v['name163'], n163=n163, top=scored[:8])

with open(TXT + 'scored.json', 'w') as f:
    json.dump(results, f, indent=1)

for k, v in results.items():
    print(f"\n{v['name163']} ({k})")
    for s in v['top']:
        print(f"  {s['a']}  score {s['score']:.2f}  subset {s['subset']} jac {s['jac']} callees {s['calee']}"
              f"  dn {s['dn']}  {s['nm'][:36]}")
