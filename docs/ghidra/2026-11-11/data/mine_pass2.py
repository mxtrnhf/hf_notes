#!/usr/bin/env python3
"""Second mining pass:
  1. globals via raw absolute addresses in operand text (151 format);
  2. targeted context pull for still-ambiguous mod fields: for each aligned
     anchor pair, print the aligned instruction texts where the 163 text
     contains one of the ambiguous offsets."""
import re, collections

TXT = '/tmp/port163_151/'

def load_ins(path):
    out = []
    cur = None
    for line in open(path):
        line = line.rstrip('\n')
        if line.startswith('#'):
            parts = line.split()
            cur = (parts[1], parts[2] if len(parts) > 2 else '?', [])
            out.append(cur)
            continue
        p = line.split('\t')
        if len(p) < 4:
            continue
        cur[2].append((int(p[0]), p[1], p[2], p[3]))
    return out

F163 = load_ins(TXT + 'ins163all.tsv')
F151 = load_ins(TXT + 'ins151all.tsv')

def lcs_align(a, b):
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return []
    am = [x[2] for x in a]
    bm = [x[2] for x in b]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        ai_ = am[i-1]
        row = dp[i]; prev = dp[i-1]
        for j in range(1, m + 1):
            if ai_ == bm[j-1]:
                row[j] = prev[j-1] + 1
            else:
                row[j] = row[j-1] if row[j-1] >= prev[j] else prev[j]
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        if am[i-1] == bm[j-1] and dp[i][j] == dp[i-1][j-1] + 1:
            pairs.append((i-1, j-1))
            i -= 1; j -= 1
        elif dp[i-1][j] >= dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    return list(reversed(pairs))

GVOTES = collections.defaultdict(collections.Counter)
AMB = ['0xbf0', '0xbf4', '0xb28', '0x15e8', '0x15ec', '0x848',
       '0xbbd', '0xbc0', '0xc18', '0xc19', '0xb00', '0xbdc', '0xc78']
ambhits = []

for k in range(len(F163)):
    e163, n163, ins163 = F163[k]
    e151, n151, ins151 = F151[k]
    if n163 == '?' or not ins163 or not ins151:
        continue
    pairs = lcs_align(ins163, ins151)
    cover = len(pairs) / max(1, min(len(ins163), len(ins151)))
    if cover < 0.5:
        continue
    for i, j in pairs:
        t163 = ins163[i][3]
        t151 = ins151[j][3]
        g163 = re.findall(r'0x(1(?:40|43|47|48)[0-9a-f]{6})\b', t163)
        g151 = re.findall(r'0x(1(?:40|43|47|48)[0-9a-f]{6})\b', t151)
        if len(g163) == 1 and len(g151) == 1 and ('0x' + g163[0]) in t163:
            GVOTES[g163[0]][g151[0]] += 1
        for off in AMB:
            if ('+ ' + off) in t163:
                ambhits.append((e163, ins163[i][1], t163, ins151[j][1], t151, n163))
            elif ('+' + off[2:]) in t163.replace(' ', ''):
                ambhits.append((e163, ins163[i][1], t163, ins151[j][1], t151, n163))

print("global pairs (direct [addr] refs), decisive votes:")
res_globals = {}
for g163, cnt in sorted(GVOTES.items()):
    tot = sum(cnt.values())
    g151, n = cnt.most_common(1)[0]
    if tot >= 2 and n >= 0.6 * tot:
        res_globals[g163] = (g151, n, tot)
        print(f"  0x{g163} -> 0x{g151}  votes {n}/{tot}")

print("\nambiguous-field context (163 instruction -> aligned 151 instruction):")
seen = set()
for e163, a163, t163, a151, t151, fn in ambhits:
    key = (a163, a151)
    if key in seen:
        continue
    seen.add(key)
    print(f"  [{fn}] {a163}: {t163[:74]}")
    print(f"        {a151}: {t151[:74]}")

import json
json.dump({k: dict(a=v[0], votes=v[1], total=v[2]) for k, v in res_globals.items()},
          open(TXT + 'globals_map.json', 'w'), indent=1)
