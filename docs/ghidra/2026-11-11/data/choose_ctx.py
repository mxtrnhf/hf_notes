#!/usr/bin/env python3
"""Neighborhood pull: print aligned ChooseTarget instructions around the
retimer init (163 idx ~25-35), the weapons reads (~605-643) and the +0xb28
write at idx ~643+; show both sides to resolve the moved offsets."""
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

# ChooseTarget is section 2 (index 1)
e163, n163, ins163 = F163[1]
e151, n151, ins151 = F151[1]
pairs = lcs_align(ins163, ins151)
amap = {i: j for i, j in pairs}

def show(rng163):
    print("163 idx addr text -> aligned 151")
    for i in rng163:
        j = amap.get(i)
        t163 = ins163[i][3][:64] if i < len(ins163) else '?'
        if j is None:
            print(f"  {i:3d} {ins163[i][1]} {t163}")
            continue
        print(f"  {i:3d} {ins163[i][1]} {t163}")
        print(f"      -> {ins151[j][1]} {ins151[j][3][:64]}")

print("=== retimer init block (idx 23..33) ===")
show(range(23, 34))
print("\n=== weapons/+0xb28-at-643 block (idx 602..650: aligned) ===")
show(range(602, 651))
