# Unnamed-function sweep, batch 5, 2026-10-29 — agent 6

Range: `0x140070000–0x14011FFFF` (engine / render / audio / resource; large map,
encounter and editor leftovers). Program `Highfleet.exe.unpacked.exe` v1.163,
project `HighfleetServer`.

Scope note: at the start the range held **34 `FUN_*` and 367 `rep_*`**. Batch 3
agent 2 and batch 4 agent 4 had already worked the same window, so most of the
large routines named in the assignment (`StrategicFleet_TryDetectContact`,
`Fleet_BuildManeuverPath`, `AircraftGroup_FindAttackTarget`,
`Escadra_MergeAdjacentFleet`, `Scene_InitializeForMode`,
`Dialog_ExecuteChoiceActions`, `Shipworks_BuildResultCards`, ...) were already
done and were not touched. **6 `FUN_*` were renamed** with
`rename_function_by_address` and given a doc-style plate
(summary / Algorithm / Parameters / Returns); **28 `FUN_*` remain** and all
367 `rep_*` were left alone (§4 policy: they are ICF replicas of already-named
targets). Nothing was created — no real vtable/pointer target in this range
lacked a function object, and the "DATA xref into `0x1480xxxx`" pattern that
looks like a vtable is really `.pdata` (see Observations).

## Renames

| addr | new name | description |
|---|---|---|
| 0x1400702a0 | `Creature_SumOffensiveScore` | +0x15e8 + +0x15ec + +0x15f0 + +0x15f4: the gun-score / Zenith / bomb / aircraft counters; the offensive share of the +0x15f8 combat value |
| 0x140070620 | `Creature_ComputeFuelRange` | (fuel +0x1638 / fuel-need +0x1650) * map speed +0x1614 / 1000; the fleet-interception candidate sort key (caller 0x14020e180) |
| 0x140073450 | `Creature_HasTWRStat` | design name == `Titan` or +0x1604 (battle TWR) != 0; 1.163 twin of 1.151 `hasTWRStat?`, used to screen strategic-missile targets |
| 0x1400734a0 | `Creature_HasMoreThanFiveZenithLaunchers` | `(end+0x13e0 - begin+0x13d8)/0x18 > 5`; marks a missile boat for the map icon chooser 0x140245180 |
| 0x1400738d0 | `Creature_SetSensorPartsEnabled` | writes 1.0 to part `+0x80c` (the enabled/armed flag) for every part of the `+0x1498` sensor list |
| 0x140079790 | `Profile_StartWaveTimerForCreature` | finds the player slot owning the creature and, if its per-slot `DAT_147fc7020` timer is 0, sets it to 4.0 (called from `RemoveLostAIShip`) |

Evidence that made these nameable (all `[code]`):

* `+0x15e8..+0x15f4` are incremented in `Creature_AccumulatePartStats`
  (`0x140071380`) inside the weapon branch (`+0x15e8 += 2 * Stats+0xec`),
  the Zenith branch (logic id 1 / 0x84, `+0x15ec`), the bomb branch
  (`m_category` bit 21, `+0x15f0`) and the aircraft branch (logic id 500,
  `+0x15f4`). `CalculateStats` (`0x14007fcf0`, lines after the mass terms)
  adds those four to the fuel term and `0.25 * +0x1604` to build `+0x15f8`.
* `+0x1614` is written by `CalculateStats` as `50 * sqrt(+0x160c - 1)` clamped
  at 0, i.e. the map speed of `findings/ship-profiles.md`. `+0x1638` is the
  double fuel total and `+0x1650` the double fuel-need total (both accumulated
  from Stats `+0xc8` / `+0xd0` in the same pass). The caller
  `0x14020e180` stores the return value into candidate `+0xf8` and then tests
  `(total fuel / total need) * min speed >= required`, confirming the range
  reading.
* `0x140073450` is the function already documented in
  `findings/strategic-missile-target-assignment.md` (Path A); the name only
  records what that page established.
* `+0x13d8` is the Zenith launcher list (`structures.md`, game-verified), and
  the only caller (0x140245180) is the strategic-map marker chooser where this
  test selects the "missile ship" icon.
* `+0x80c` is the part enabled flag used by the gun reload, launcher and flare
  gates (`findings/guns-aim-reload-fire.md`, `findings/ai/ai-flares.md`);
  `+0x1498` is the per-category sensor list from `findings/ai/ai-telemetry.md`.
* `DAT_147fc7020` is the per-player-slot scene/wave timer (30 s between waves,
  4.0 s death delay written by `Creature_Die` 0x14006aab0,
  `findings/battle-ally.md`, `findings/ship-removal-and-battle-result.md`).

## Skipped / open (28 `FUN_*` remain)

* **0x140073340** (26) - `if ([+0x48] && 40.0 <= +0x15f8)` style test against
  the combat value with a 40.0 threshold (`0x140354834`). **The return value is
  undefined on the "true" path**: the bytes are `32 c0 c3` (XOR AL,AL; RET)
  reached only when `+0x15f8 < 40`, while the `>= 40` path falls straight into
  RET without setting AL, yet callers do `TEST AL,AL`. In practice AL is the
  low byte of the creature pointer, i.e. usually non-zero, so it behaves like
  "alive and combat value >= 40" — but the threshold is not understood well
  enough for an honest name. Nine call sites (Body_Explode, BulletImpact,
  World_ThermalPass, SCR_BOMBERS, deployFromReserve, Physics_ProcessContactRecord,
  Battle_SpawnQueuedShipForSlot, ...).
* **0x140073530** (38) - kills/clears the object at `+0x48` via vtable +0x48.
  `+0x48` is a state int on Creature and a child pointer here, so the owning
  class is unknown.
* **0x140078930** (513) - `CalculateStats`, frees the `+0x1558` Link list and
  rebuilds it from parts with `+0x888 != 0`, sorted by `SortInsertionByInt88C`
  on `+0x88c`, also writing `+0x1560` into a part field. `+0x888/+0x88c` role
  unknown (`findings/sensors-and-crew.md` says unknown too).
* **0x140079ed0** (649) - caches three floats in `+0xd18/+0xd1c/+0xd20`, then
  picks the min-x and max-x part of the `+0x13a8` (gun-group-0) list by body
  `+0x128` and writes the three floats into those two parts. Looks like gun
  convergence, but the two target fields are not identified; called from
  `CreatureUpdate`.
* **0x140083450 / 0x1400834e0 / 0x1400835a0** (137 / 182 / 177) - three
  siblings that forward 1-2 positions to the quad draw helper
  (`rep_14007e8a0`); differ only in the source object (`+0x228` vs argument).
* **0x140083760** (54), **0x140085e80** (36), **0x140085eb0** (144) - forwards
  to a child vtable (+0x1a8 / +0x40 / +0x58 with `Render_SetBlendState`) gated
  on the hidden byte `+0x1c5`. Owning render class not established.
* **0x140083d60** (5) - returns byte `+0x10`; trivial getter.
* **0x140088950** (21) - 0x28-byte object init (stores [0], zeroes [1],[3],[4]).
* **0x140092e70** (44) - releases the object at `+0x38` through vtable +0x20
  with the `ptr != this` "deleting" flag, then clears the field.
* **0x1400a07a0** (178) - detach/clear sequence over a GUI binding object.
* **0x1400a2fb0** (62) - zeroes `+0x68..+0x88`, `+0xe8` and clears the
  `std::string` at `+0xd8`; class unknown.
* **0x1400a6210** (24) - predicate `+0xf8 == 0 && +0xf6 != 0`.
* **0x1400bc5c0** (32) - editor-only no-arg handler: `if (IsInEditor)
  call <mode handler>; return 1`. The callee is ICF-misnamed (see below) and
  the mode is not in the body.
* **0x1400bee20** (58) - zeroes `+0x128` on every `+0x8c0` element whose byte
  `+0x71` is set.
* **0x1400e8140** (67) - deleting destructor with a Link at `+0xa48`; the
  owning class (>= 0xa60 bytes, no matching documented size) is not certain.
* **0x1400e85a0** (20) - thunk to `_invalid_parameter_noinfo_noreturn`.
* **0x1400f51c0** (52) - returns vtable +0x1d0 of a nested object or 1.0.
* **0x1400f8da0** (12) - tail call to `rep_140204600` (misnamed
  `_Init_thread_footer`) with `this+0x520`.
* **0x1400fdec0** (61) - clears `+0x1d0`, a word at `+0x1a4`, `+0x1b8` and the
  `std::string` at `+0x1a8`; class unknown.
* **0x14010f1a0** (69) - global vector trim through a misnamed CRT target.
* **0x1401102c0** (117) - state 5 / 7 select from
  `dist*1000/+0x494 < 7200`; the 5/7 pair is still not pinned (b4 left it).
* **0x140110340** (180) - stores `+0x2a8` and two HGE randoms into
  `+0x2ac/+0x2b0`; HGE +0x100/+0x108/+0x110 slots undocumented.
* **0x140118699** (7) - INT3 padding, not a real function.
* **0x14011bbc0** (8) - returns `&DAT_1403ef5f8`; the only readers are the
  ICF replica named `sscanf` (0x14011bbf1) and `FUN_14033536c`, so the global's
  meaning is still unknown.

`rep_*` (367): untouched. One is worth knowing about — the editor no-arg
handler above calls `rep_1400bc6b0_..._invalid_parameter_noinfo_noreturn`
(entry `0x1400c12a0`, 3236 bytes), i.e. an ICF replica that is really the
editor's mouse-mode handler; the embedded name is wrong but the semantics are
not recoverable from the replica name, so it was reported on the blackboard
rather than renamed.

## Observations for the rest of the batch

1. **`0x1480xxxx` "data xrefs" are `.pdata`, not vtables.** The dwords in
   `0x14807a000`-`0x14807b200` are `_IMAGE_RUNTIME_FUNCTION_ENTRY` triples
   (begin RVA / end RVA / unwind RVA), e.g. at `0x14807aebc`:
   `0x70650, 0x70cb2, 0x387a88`. That is why the xref addresses are not
   8-aligned. `get_function_xrefs` reporting `[DATA]` from `0x14807xxxx` is
   **not** evidence of a vtable slot; do not create/rename on that basis.
2. `CalculateStats` (`0x14007fcf0`) writes the whole display block
   `+0x15f8` (combat value), `+0x1600` (mass/thrust rating), `+0x1604` (battle
   TWR), `+0x1608` (map thrust TWR), `+0x160c` (map TWR with map engines),
   `+0x1610`, `+0x1614` (map speed), `+0x1618`/`+0x161c` and `+0x1624`
   (fuel ratio `+0x1638/+0x1648`). Useful for anyone naming accessors of that
   cluster.
