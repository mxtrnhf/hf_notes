#!/usr/bin/env python3
"""Refine the no-twin verdicts: exact LCS for the accepted pairs, and
caller-based disambiguation for the String_Tidy ICF fold group."""
import csv, collections

TXT = '/tmp/port163_151/'

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

CHECKS = [
    ('1401c3bd0', 'Hull_CreateAntennaChain', ['140047e60']),
    ('14004af00', 'Vector8_PushBackRealloc', ['1400b4dd0', '140070630', '140070610', '1402194b0']),
    ('140061dc0', 'LinkedList_ClearFree', ['1400eaef0', '1400eae70']),
    ('14015ccb0', 'RbTree_ClearFreeResetHeader', ['1401ac200', '14017d150']),
    ('1401adfc0', 'Vec2_WorldToScreen', ['14019e6e0']),
    ('14000fbc0', 'aircraftStateHandler', ['14000f890']),
    ('140006d70', 'String_Tidy', ['14005c210', '140197890', '140196f60', '140193c10',
                                   '140180de0', '140097850', '140017dc0']),
]
for a163, name, cands in CHECKS:
    t = t163[a163]
    print(f"\n{name} ({a163}, {t[1]}i):")
    for c in cands:
        cc = all151.get(c)
        if not cc:
            continue
        L = lcs_tokens(t[2], cc[2])
        print(f"  {c} {cc[0][:44]:44s} {cc[1]:4d}i  LCS {L}/{min(t[1], cc[1])} = {L/min(t[1], cc[1]):.3f}")

# String_Tidy caller disambiguation: mapped 163 callers of String_Tidy ->
# which of the 25i fold members they call in 151
def load_funcs(path):
    out = {}
    with open(path) as f:
        h = f.readline().rstrip('\n').split('\t')
        for line in f:
            p = line.rstrip('\n').split('\t')
            d = dict(zip(h, p))
            out[d['addr']] = d
    return out

f163 = load_funcs(TXT + 'funcs_163.tsv')
f151 = load_funcs(TXT + 'funcs_151.tsv')
pair = {}
import json
for path in [TXT + 'matched.json', TXT + 'matched2.json', TXT + 'matched3.json']:
    pair.update({k: v['addr151'] for k, v in json.load(open(path)).items()})

def callers163of(target):
    res = set()
    for a, r in f163.items():
        cs = (r['callees'] or '').split(',')
        if target in cs:
            res.add(a)
    return res

MEMBERS = ['000000014005c210', '0000000140197890', '0000000140196f60', '0000000140193c10',
           '0000000140180de0', '0000000140097850', '0000000140017dc0']
print('\nString_Tidy caller disambiguation:')
callers = callers163of('0000000140006d70')
print(f'  163 callers: {len(callers)}, mapped: {sum(1 for c in callers if c in pair)}')
votes = collections.Counter()
for c163 in callers:
    c151 = pair.get(c163)
    if not c151:
        continue
    r151 = f151.get(c151)
    if not r151:
        continue
    cs151 = set((r151['callees'] or '').split(','))
    for m in MEMBERS:
        if m in cs151:
            votes[m] += 1
for m, n in votes.most_common():
    print(f'  member {m} ({f151[m]["name"][:44]}, {f151[m]["ninsn"]}i): {n} mapped callers')
