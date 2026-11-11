#!/usr/bin/env python3
"""Inlining / twin check for every 'no twin' reject.

For each reject (163 function):
  1. content-check the rejected candidate (LCS - if high, the spatial rule
     was wrong and the pair stands);
  2. containment scan over ALL 151 functions (shared 8-grams / target grams),
     report top holders - the squad-precombat inlining pattern.
"""
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

t163 = load_mn(TXT + 'mn163d.tsv')
all151 = load_mn(TXT + 'mn_all151.tsv')

def grams(seq):
    if len(seq) < K:
        return Counter([tuple(seq)]) if seq else Counter()
    return Counter(tuple(seq[i:i+K]) for i in range(len(seq) - K + 1))

def shared(c1, c2):
    return sum((c1 & c2).values())

def lcs_tokens(a, b):
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

PAIRS = {
    '14000a360': ('Aircraft_CollectActiveCraft', '14026d620'),
    '1401c3bd0': ('Hull_CreateAntennaChain', '140047e60'),
    '140292ab0': ('Profile_GetActive', '14007d750'),
    '140006d70': ('String_Tidy', '14005c210'),
    '14004af00': ('Vector8_PushBackRealloc', '1400b4dd0'),
    '140061dc0': ('LinkedList_ClearFree', '1400eaef0'),
    '140124eb0': ('Trail_DrawLayer', '140080b70'),
    '14015ccb0': ('RbTree_ClearFreeResetHeader', '1401ac200'),
    '1401adfc0': ('Vec2_WorldToScreen', '140243ba0'),
    '1402ee440': ('Gfx_BuildFullscreenProjection', '14007ef50'),
    '14000fbc0': ('aircraftStateHandler', '1400d51d0'),
}

for a163, (name, cand) in PAIRS.items():
    t = t163.get(a163)
    if not t or not t[2]:
        print(f"\n{name} {a163}: no dump")
        continue
    seq163 = t[2]
    g163 = grams(seq163)
    n163i = t[1]
    print(f"\n=== {name} ({a163}, {n163i}i) rejected candidate {cand}")
    c = all151.get(cand)
    if c and c[2]:
        L = lcs_tokens(seq163, c[2])
        print(f"  candidate: {c[0]} {c[1]}i  LCS {L}/{min(n163i, c[1])} = {L/min(n163i, c[1]):.3f}")
    hits = []
    for a151, (nm, n151i, seq151) in all151.items():
        if not seq151:
            continue
        sh = shared(g163, grams(seq151))
        if sh == 0:
            continue
        cont_t = sh / max(1, len(seq163) - K + 1) if len(seq163) >= K else 0
        hits.append((cont_t, a151, nm, n151i, sh))
    hits.sort(reverse=True)
    for cont_t, a151, nm, n151i, sh in hits[:6]:
        tag = ''
        if cont_t >= 0.85:
            tag = '  <<< CONTAINS nearly all'
        elif cont_t >= 0.5:
            tag = '  ~ partial'
        print(f"  contains {cont_t:.3f}: {a151} {nm[:42]:42s} {n151i:5d}i shared8g={sh}{tag}")
