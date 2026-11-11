#!/usr/bin/env python3
"""Second verification batch: level-seria loader family, radio sounds, GUI New."""
TXT = '/tmp/port163_151/'

def load_mn(path):
    out = {}
    for line in open(path):
        p = line.rstrip('\n').split('\t')
        if len(p) < 4:
            continue
        out[p[0]] = (p[1], int(p[2]), p[3].split(' ') if p[3] else [])
    return out

mn163 = load_mn(TXT + 'mn163.tsv')
mn163.update(load_mn(TXT + 'mn163c.tsv'))
mn151 = load_mn(TXT + 'mn151.tsv')

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

def check(a163, cands):
    t = mn163.get(a163)
    if not t:
        print(f"{a163}: no 163 dump")
        return
    print(f"{t[0]} ({a163}, {t[1]}i):")
    for c in cands:
        cc = mn151.get(c)
        if not cc:
            print(f"  {c}: no 151 dump")
            continue
        L = lcs_tokens(t[2], cc[2])
        mins = min(len(t[2]), len(cc[2]))
        print(f"  {c} {cc[0][:40]:40s} {cc[1]:4d}i  lcs {L}/{mins} = {L/mins:.3f}")

check('14025afd0', ['140205fc0', '1402073c0', '140221b50', '14022b6a0', '140239190'])
check('1402d5910', ['1402abb30'])

# GUI New twin: sizes of mainPrecombatScreen callees
import subprocess
rows = []
for a in ['00000001400045e0', '0000000140186ec0', '0000000140186f10', '00000001400453 b0'.replace(' ',''),
          '0000000140006830', '00000001401b07a0', '00000001402475e0', '00000001401a 21c0'.replace(' ',''),
          '0000000140121c30', '0000000140214610', '000000014019e7b0', '0000000140063d80']:
    rows.append(a)
print('\nNew (140334094, 20i) vs possible wrappers:')
for c in ['1400045e0', '140 186ec0'.replace(' ',''), '140186f10', '1400053eb0', '140006830']:
    cc = mn151.get(c)
    if cc:
        L = lcs_tokens(mn163['140334094'][2], cc[2])
        mins = min(20, len(cc[2]))
        print(f"  {c} {cc[0][:36]:36s} {cc[1]:4d}i  lcs {L}/{mins}")
