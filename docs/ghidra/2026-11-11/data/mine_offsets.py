#!/usr/bin/env python3
"""Mine field-offset pairs (163 offset -> 151 offset) and data-global pairs
(163 label/DAT -> 151 DAT) from aligned twin instructions.

Each anchor pair was dumped as instruction listings (index, addr, mnemonic,
operand text). We LCS-align on mnemonics, then for aligned pairs extract:
  - displacement immediates like +0xad4 / [rsp+0x28] -> vote off163 -> off151
  - referenced global labels / DAT_ addresses -> vote dat163 -> dat151
Votes are aggregated across all anchor functions; a mapping is accepted when
it has a strict majority of consistent votes.
"""
import re, collections

TXT = '/tmp/port163_151/'

def load_ins(path):
    """returns ordered list of (entry, [(idx, addr, mnem, text)])"""
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
    """LCS over mnemonic lists with traceback -> (i, j) pairs."""
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

DISP_RE = re.compile(r'0x([0-9a-f]+)')

def disps(text):
    """Field-like displacements: hex immediates in bracketed memory operands."""
    out = []
    for m in re.finditer(r'\[([^\]]+)\]', text):
        for h in DISP_RE.finditer(m.group(1)):
            v = int(h.group(1), 16)
            if 0x20 <= v <= 0x4000:
                out.append(v)
    return out

def globals163(text):
    out = []
    for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)_(140[0-9a-f]{6}|147[0-9a-f]{6}|143[0-9a-f]{6}|148[0-9a-f]{6})\b', text):
        out.append(m.group(0))
    for m in re.finditer(r'\b(DAT_[0-9a-f]{9,})\b', text):
        out.append(m.group(1))
    return out

def globals151(text):
    return re.findall(r'\b(DAT_[0-9a-f]{9,})\b', text)

offvotes = collections.defaultdict(collections.Counter)
gvotes = collections.defaultdict(collections.Counter)
perpair = {}

for k in range(len(F163)):
    e163, n163, ins163 = F163[k]
    e151, n151, ins151 = F151[k]
    if n163 == '?' or not ins163 or not ins151:
        continue
    pairs = lcs_align(ins163, ins151)
    cover = len(pairs) / max(1, min(len(ins163), len(ins151)))
    perpair[e163] = (len(ins163), len(ins151), cover)
    if cover < 0.5:
        continue
    for i, j in pairs:
        t163 = ins163[i][3]
        t151 = ins151[j][3]
        d163s = disps(t163)
        d151s = disps(t151)
        if len(d163s) == 1 and len(d151s) == 1 and d163s[0] != d151s[0]:
            offvotes[d163s[0]][d151s[0]] += 1
        g163s = globals163(t163)
        g151s = globals151(t151)
        if len(g163s) == 1 and len(g151s) == 1:
            gvotes[g163s[0]][g151s[0]] += 1

print("pair alignment coverage:")
for e, (a, b, c) in perpair.items():
    print(f"  {e}: {a}i vs {b}i cover {c:.2f}")

print("\noffset migrations with majority votes (>=2 votes, decisive):")
res_offsets = {}
for off163, cnt in sorted(offvotes.items()):
    tot = sum(cnt.values())
    off151, n = cnt.most_common(1)[0]
    if n >= 2 and n >= 0.6 * tot:
        res_offsets[off163] = (off151, n, tot)
        mark = '' if off163 == off151 else '  CHANGED'
        print(f"  +0x{off163:x} -> +0x{off151:x}   votes {n}/{tot}{mark}")

print("\nambiguous offset votes (majority < 0.6, shown for review):")
for off163, cnt in sorted(offvotes.items()):
    tot = sum(cnt.values())
    off151, n = cnt.most_common(1)[0]
    if not (n >= 2 and n >= 0.6 * tot) and tot >= 2:
        print(f"  +0x{off163:x}: " + ", ".join(f"0x{k:x}x{v}" for k, v in cnt.most_common(4)))

print("\nglobal pairs with decisive votes:")
res_globals = {}
for g163, cnt in sorted(gvotes.items()):
    tot = sum(cnt.values())
    g151, n = cnt.most_common(1)[0]
    if n >= 2 and n >= 0.6 * tot:
        res_globals[g163] = (g151, n, tot)
        print(f"  {g163} -> {g151}   votes {n}/{tot}")

import json
json.dump(dict(
    offsets={f"{k:x}": dict(off=f"{v[0]:x}", votes=v[1], total=v[2]) for k, v in res_offsets.items()},
    globals={k: dict(a=v[0], votes=v[1], total=v[2]) for k, v in res_globals.items()},
    coverage={e: dict(n163=a, n151=b, cover=round(c, 3)) for e, (a, b, c) in perpair.items()},
), open(TXT + 'mined_map.json', 'w'), indent=1)
