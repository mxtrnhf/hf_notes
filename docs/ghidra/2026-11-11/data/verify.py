#!/usr/bin/env python3
"""Verify specific pairing hypotheses by LCS over the mnemonic dumps."""
import sys

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

PAIRS = [
    ('1402a7e30', 'Profile_SetControlledShip', ['140284160']),
    ('1402a7e20', 'Profile_SetPlayerShip(dump missing)', []),
    ('140078b40', 'AiShip_ChooseTarget', ['140074bb0']),
    ('14025afd0', 'SetLevelSeriaToLoad?', ['140205fc0','1402073c0','140221b50','14022b6a0','140239190']),
    ('1402d5910', 'PlayRadioSounds?', ['1402abb30']),
    ('1402d73a0', 'buildSquadPrecombatScreen', ['140135810']),
    ('140334094', 'New', []),
    # leftovers of battleManagerTick callee alignment
    ('', '', ['1402a8540','1402a5820','1402a4d20','1400704d0','1402924d0','1402cbc60','1402d22e0','1402cd9a0','140074080']),
]

for a163, name163, cands in PAIRS:
    if a163:
        t = mn163.get(a163)
        if not t:
            print(f"{name163} {a163}: no 163 dump")
            continue
        print(f"\n{name163} ({a163}, {t[1]}i):")
        for c in cands:
            cc = mn151.get(c)
            if not cc:
                print(f"  {c}: no 151 dump")
                continue
            L = lcs_tokens(t[2], cc[2])
            mins = min(len(t[2]), len(cc[2]))
            print(f"  {c} {cc[0][:38]:38s} {cc[1]:5d}i  lcs {L}/{mins} = {L/mins:.3f}")
    else:
        print("\n151-side battleManagerTick leftovers:")
        for c in cands:
            cc = mn151.get(c)
            if cc:
                print(f"  {c}  {cc[0][:44]:44s} {cc[1]:5d}i")
