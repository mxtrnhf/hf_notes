#!/usr/bin/env python3
"""Capped 1.151 candidate list per open target, written as flat file for the
Ghidra mnemonic dump: one candidate per line 'addr n163'."""
import bisect
import json

d = json.load(open('/tmp/port163_151/candmod.json'))

# widen windows for the big changed functions; recompute from funcs_151 with
# looser ninsn ratio: [0.3x, 2x] for big ones, [1, 4x] for tiny ones
# 151 addresses already matched to some 163 function: exclude, they cannot be
# twins of an OPEN 163 function
paired151 = set()
for path in ['/tmp/port163_151/matched.tsv', '/tmp/port163_151/matched2.tsv',
             '/tmp/port163_151/matched3.tsv']:
    with open(path) as f:
        f.readline()
        for line in f:
            _, a151, _, _ = line.rstrip('\n').split('\t')
            paired151.add(int(a151, 16))

f151 = []
with open('/tmp/port163_151/funcs_151.tsv') as f:
    h = f.readline().rstrip('\n').split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        dd = dict(zip(h, p))
        f151.append((int(dd['addr'],16), dd['name'], dd['namesrc'], int(dd['size']), int(dd['ninsn'])))
f151.sort()
entries = [f[0] for f in f151]

OPEN_MAP = {v['name163']: k for k, v in d.items()}
NASDAQ = None
# recompute with target-specific windows: reuse candmod expect
cands = []
for k, v in d.items():
    a163 = int(k, 16)
    n163 = v['n163']
    if n163 >= 1000:
        nlo, nhi = int(n163 * 0.35), int(n163 * 1.8)
    elif n163 >= 100:
        nlo, nhi = int(n163 * 0.3), int(n163 * 2.5)
    elif n163 >= 40:
        nlo, nhi = int(n163 * 0.4), int(n163 * 3)
    else:
        nlo, nhi = 1, max(8, n163 * 4)
    window = 0x60000 if n163 >= 500 else 0x40000
    expect = int(round(v['expect']))
    lo, hi = expect - window, expect + window
    i = bisect.bisect_left(entries, lo)
    lst = []
    while i < len(f151) and f151[i][0] <= hi:
        entry, fname, src, size, n151 = f151[i]
        if entry not in paired151 and nlo <= n151 <= nhi:
            lst.append((abs(entry - expect), entry, n151, fname))
        i += 1
    lst.sort()
    lst = lst[:80]
    for _, entry, n151, fname in lst:
        cands.append(f"{entry:x} {n163}")
    print(f"{k} {v['name163']}: {len(lst)} candidates (window {window:#x}, ninsn [{nlo},{nhi}])")

# dedupe addresses: same 151 fn can be candidate for multiple targets; keep
# union with the set of targets it belongs to
from collections import defaultdict
targets = defaultdict(set)
uniq = set()
for line in cands:
    a, n = line.split()
    uniq.add(a)
with open('/tmp/port163_151/cand151_addrs.txt', 'w') as f:
    for a in sorted(uniq):
        f.write(a + '\n')
print('\nunique candidate addresses:', len(uniq))
