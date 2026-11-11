#!/usr/bin/env python3
"""Score 1.151 candidates vs open 1.163 targets by shared 8-gram mnemonic
fingerprints, then run full LCS on the top 3 of each target for confirmation."""
import json
from collections import Counter

TXT = '/tmp/port163_151/'
K = 8

def load_mn(path):
    out = {}
    for line in open(path):
        p = line.rstrip('\n').split('\t')
        if len(p) < 4:
            continue
        out[p[0]] = (p[1], int(p[2]), p[3].split(' ') if p[3] else [])
    return out

mn163 = load_mn(TXT + 'mn163.tsv')
mn151 = load_mn(TXT + 'mn151.tsv')

def grams(seq):
    if len(seq) < K:
        return Counter([tuple(seq)]) if seq else Counter()
    return Counter(tuple(seq[i:i+K]) for i in range(len(seq) - K + 1))

def shared(c1, c2):
    return sum((c1 & c2).values())

def bands(n163):
    if n163 >= 1000:
        return int(n163*0.35), int(n163*1.8)
    if n163 >= 100:
        return int(n163*0.3), int(n163*2.5)
    if n163 >= 40:
        return int(n163*0.4), int(n163*3)
    return 1, max(8, n163*4)

def lcs_tokens(a, b):
    """Longest common subsequence length over token lists (row-DP)."""
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y:
                cur[j] = prev[j-1] + 1
            elif cur[j-1] >= prev[j]:
                cur[j] = cur[j-1]
            else:
                cur[j] = prev[j]
        prev = cur
    return prev[-1]

candmod = json.load(open(TXT + 'candmod.json'))
results = {}
for k, v in candmod.items():
    a163 = k
    t = mn163.get(a163)
    if not t or not t[2]:
        continue
    name163, n163_target, seq163 = t
    g163 = grams(seq163)
    nlo, nhi = bands(len(seq163))
    window = 0x60000 if len(seq163) >= 500 else 0x40000
    expect = int(round(v['expect']))
    scored = []
    for a151, (nm151, n151, seq151) in mn151.items():
        a = int(a151, 16)
        if not (expect - window <= a <= expect + window):
            continue
        if not (nlo <= n151 <= nhi):
            continue
        g151 = grams(seq151)
        sh = shared(g163, g151)
        mins = min(len(seq163), len(seq151))
        if sh == 0 or mins == 0:
            continue
        sim = sh / max(1, min(len(seq163) - K + 1, len(seq151) - K + 1, mins))
        scored.append((sim, a151, nm151, n151, sh, mins))
    scored.sort(reverse=True)
    top = scored[:3]
    confirmed = []
    for sim, a151, nm151, n151, sh, mins in top:
        L = lcs_tokens(seq163, mn151[a151][2])
        confirmed.append(dict(a=a151, nm=nm151, n=n151, sim=round(sim,3),
                              sharedgrams=sh, lcs=L,
                              lcs_over_min=round(L/mins, 3), minlen=mins))
    results[k] = dict(name=name163, targetn=int(n163_target), top=confirmed)

with open(TXT + 'mn_scored.json', 'w') as f:
    json.dump(results, f, indent=1)

for k, v in results.items():
    print(f"\n{v['name']} ({k}, {v['targetn']}i)")
    for c in v['top']:
        flag = ''
        if c['lcs_over_min'] >= 0.93:
            flag = '  <<< SAME-BODY'
        elif c['lcs_over_min'] >= 0.55:
            flag = '  ~ likely twin'
        print(f"  {c['a']}  {c['nm'][:34]:34s} n={c['n']:5d} sim {c['sim']:.3f}  lcs {c['lcs']}/{c['minlen']} = {c['lcs_over_min']:.3f}{flag}")
