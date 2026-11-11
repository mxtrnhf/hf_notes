#!/usr/bin/env python3
"""Align 1.163 buildSquadPrecombatScreen against 1.151 mainPrecombatScreen with
traceback, to test the inlining hypothesis and locate the inlined region."""
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
    """DP with traceback: returns list of (i, j) aligned index pairs."""
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
print(f"squad 134i? actual {len(a)}; precombat 1060i? actual {len(b)}")
print(f"aligned pairs: {len(pairs)} / {len(a)} = {len(pairs)/len(a):.3f}")
# longest contiguous run (with small gap tolerance)
runs = []
start = 0
for k in range(1, len(pairs) + 1):
    if k == len(pairs) or pairs[k][0] != pairs[k-1][0] + 1 or pairs[k][1] != pairs[k-1][1] + 1:
        if k - start >= 20:
            runs.append((start, k))
        start = k
print("\ncontiguous runs >= 20 aligned instructions:")
for s, e in runs:
    i0, j0 = pairs[s]
    i1, j1 = pairs[e-1]
    print(f"  163 idx {i0}..{i1} ({a[i0][1]}..{a[i1][1]})  ->  151 idx {j0}..{j1} ({b[j0][1]}..{b[j1][1]})"
          f"   len {e-s}")

# where do the TGDO seams map?
print("\n163 TGDO seam instructions (CALL with target):")
for idx, addr, mn, text in a:
    if mn == 'CALL' and 'dispatch' in (text or '').lower() or mn == 'CALL' and ('253b80' in (text or '') or '275850' in (text or '')):
        print(' ', addr, text[:110])
print("\n163 secondaryPrecombatButtons call:")
for idx, addr, mn, text in a:
    if mn == 'CALL' and ('secondary' in (text or '') or '1fc770' in (text or '')):
        print(' ', addr, text[:110])
