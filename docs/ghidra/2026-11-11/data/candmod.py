#!/usr/bin/env python3
"""For each open mod-referenced 1.163 function, list unnamed 1.151 candidate
functions by interpolated spatial delta and instruction-count window."""
import bisect
import json

# load verified pairs for delta interpolation
pairs163, pairs151 = [], []
pairset = {}
for path in ['/tmp/port163_151/matched.tsv', '/tmp/port163_151/matched2.tsv',
             '/tmp/port163_151/matched3.tsv']:
    with open(path) as f:
        f.readline()
        for line in f:
            a163, a151, tier, ev = line.rstrip('\n').split('\t')
            a163 = int(a163, 16); a151 = int(a151, 16)
            pairset[a163] = a151
pairs = sorted(pairset.items())
sorted163 = [p[0] for p in pairs]
DELTAS = [(a163, a151 - a163) for a163, a151 in pairs]

def interp_delta(addr163):
    """Piecewise-linear interpolated delta at addr163 (clamped at the ends)."""
    idx = bisect.bisect_right(sorted163, addr163) - 1
    if idx < 0:
        return DELTAS[0][1]
    if idx >= len(DELTAS) - 1:
        return DELTAS[-1][1]
    a0, d0 = DELTAS[idx]
    a1, d1 = DELTAS[idx + 1]
    if a1 == a0:
        return d0
    t = (addr163 - a0) / (a1 - a0)
    return d0 + t * (d1 - d0)

# 151 function inventory
f151 = []
with open('/tmp/port163_151/funcs_151.tsv') as f:
    h = f.readline().rstrip('\n').split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        d = dict(zip(h, p))
        f151.append((int(d['addr'],16), d['name'], d['namesrc'], int(d['size']), int(d['ninsn'])))
f151.sort()
f151_entries = [f[0] for f in f151]

OPEN = [
    # (addr163, name163, ninsn)
    (0x1400625a0, 'AiShip_BuildThreatList', 538),
    (0x140049470, 'checkShipPartFlagActive', 20),
    (0x1402cc260, 'battleManagerTick', 299),
    (0x1402d6e90, 'deployFromReserve', 143),
    (0x1402a7e30, 'Profile_SetControlledShip', 73),
    (0x140194de0, 'SetLink', 33),
    (0x140292a90, 'Get_Profile?', 3),
    (0x14020ef30, 'rep_1401f3c10_APP:MoveVolume', 390),
    (0x1402d7620, 'buildPrecombatScreen', 1133),
    (0x1402d73a0, 'buildSquadPrecombatScreen', 134),
    (0x140275850, 'TarkhanGUIDispatchOperator', 1941),
    (0x140334094, 'New', 20),
    (0x14012a910, 'GUI_2', 108),
    (0x1400520b0, 'setXposYpos', 68),
    (0x14001be50, 'SetBackground?', 74),
    (0x1401a9170, 'FindGuiElement', 45),
    (0x14018dbf0, 'SomethingInputTask', 579),
    (0x14012f120, '!ClickFunc', 13172),
    (0x140078b40, 'AiShip_ChooseTarget', 691),
    (0x1402e30e0, 'playSFXSound?', 253),
    (0x140083b50, 'checkD3DEngineStatus?', 49),
    (0x1401703e0, 'LoadNameIntoMedia', 17),
    (0x14016eb40, 'displayLableRotation?', 266),
    (0x14026f880, 'ammoSelectButtonPress?', 63),
    (0x14007eb50, 'CreatureUpdate', 900),
    (0x140062f90, 'AiShipTick', 2594),
    (0x14002eed0, 'FireFlareLauncher', 253),
    (0x140048fc0, 'Node_GetRootPart', 15),
    (0x140281e00, 'GetStats', 13),
    (0x14020fb80, 'magnitudeCreatureBodyVector', 56),
    (0x140033b90, 'creatureLogic', 5422),
    (0x14002ff60, 'LaunchZenithAtOwnerTarget', 88),
    (0x1400486e0, 'returnMass', 2),
    (0x14000d6f70, 'displayinShipworks?', 3155),
]

OUT = {}
for a163, name, n163 in OPEN:
    d = interp_delta(a163)
    expect = a163 + d
    lo, hi = expect - 0x40000, expect + 0x40000
    cands = []
    i = bisect.bisect_left(f151_entries, lo)
    while i < len(f151) and f151[i][0] <= hi:
        entry, fname, src, size, n151 = f151[i]
        if src in ('DEFAULT', 'ANALYSIS') or fname.startswith('FUN_') or fname.startswith('rep_'):
            if n151 and abs(n151 - n163) <= max(12, int(n163 * 0.5)):
                cands.append((entry, fname, n151, round(entry - a163, -1)))
        i += 1
    OUT[f"{a163:x}"] = dict(name163=name, n163=n163, expect=round(expect, -1), delta=round(d, -1),
                            ncand=len(cands),
                            cands=[dict(a=f"{e:x}", n=n151, d=round(e - a163, -1), nm=fname) for e, fname, n151, _ in cands])

print(json.dumps(OUT, indent=1))
