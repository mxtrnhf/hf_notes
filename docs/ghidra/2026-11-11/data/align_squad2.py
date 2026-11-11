#!/usr/bin/env python3
"""Fine-grained alignment around the dispatcher seams of the inlined squad
builder: locate the 1.151 counterpart addresses of the B1/B2 TGDO seams."""
TXT = '/tmp/port163_151/'

def load(path):
    seqs = {}
    fn = None
    for line in open(path):
        if line.startswith('#'):
            fn = line.split()[1]
            seqs[fn] = []
            continue
        p = line.rstrip('\n').split('\t')
        if len(p) < 3:
            continue
        seqs[fn].append((int(p[0]), p[1], p[2], p[3] if len(p) > 3 else ''))
    return seqs

s163 = load(TXT + 'ins_squad163.tsv')
s151 = load(TXT + 'ins_prec151.tsv')
a = s163['1402d73a0']
b = s151['1402ad2e0']

def lcs_align(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        ai = a[i-1][2]
        row = dp[i]; prev = dp[i-1]
        for j in range(1, m + 1):
            if ai == b[j-1][2]:
                row[j] = prev[j-1] + 1
            else:
                row[j] = row[j-1] if row[j-1] >= prev[j] else prev[j]
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i-1][2] == b[j-1][2] and dp[i][j] == dp[i-1][j-1] + 1:
            pairs.append((i-1, j-1))
            i -= 1; j -= 1
        elif dp[i-1][j] >= dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    return list(reversed(pairs))

pairs = lcs_align(a, b)
amap = {i: j for i, j in pairs}

print("aligned pairs for 163 idx 60..133 (around the seams):")
for i, j in pairs:
    if i >= 60:
        mark = ''
        txt = a[i][3]
        if 'CALL' in a[i][2] and ('dispatch' in txt or '275850' in txt):
            mark = '   <<< TGDO seam'
        if 'CALL' in a[i][2] and ('1fc770' in txt or 'secondary' in txt):
            mark = '   <<< secondaryPrecombatButtons'
        print(f"  idx {i:3d} {a[i][1]} {a[i][2]:8s} -> idx {j:4d} {b[j][1]} {b[j][2]:8s}{mark}")

print("\nunmatched 163 instructions (not aligned):")
used = set(i for i, _ in pairs)
for idx, addr, mn, text in a:
    if idx not in used:
        print(f"  idx {idx:3d} {addr} {mn} {text[:80]}")

# neighbors of the TGDO calls in 151
print("\n151 code around the TGDO call 1402ae333 and secondaryPrecombatButtons call 1402ad48e:")
for idx, addr, mn, text in b:
    if mn == 'CALL' and ('253b80' in text or '1401e22f0' in text or 'dispatch' in text.lower()):
        print(f"  idx {idx} {addr} {text[:100]}")
