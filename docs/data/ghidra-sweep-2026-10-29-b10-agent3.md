# Ghidra sweep batch 10, agent 3 — remaining `rep_*` in `0x140000000–0x1400FFFFF` (Q1)

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`). 1.151 never touched.

Scope: live `rep_*` functions with entry in the range, minus every address in
`docs/data/funclet-ownership-2026-10-29.tsv` (`funclet_addr` + `owner_addr`), minus the
three withheld agent-6 names. Live enumeration at start: **389** `rep_*` in the range;
**342** in scope (47 excluded as funclet/owner addresses). This is exactly the 342 rows
batch 9 agent 4 left stale (`b9a4_rem.json` minus the two functions it renamed), so this
pass is a second, deeper attempt at the same tail rather than a disjoint slice.

**342 audited. 10 renamed + plated. 332 stale labels remain, 14 of them re-recorded with
sharper identities this pass. 0 unreadable. 0 byte-identical named twins.**

No `save_program`, no tags, no README/STATUS edits, no commits, no `create_function`.

| | before | after |
|---|---|---|
| `rep_*` in range | 389 | 378 |
| `rep_*` in scope | 342 | 332 |
| renamed + plated this pass | — | 10 |
| q1 rows appended | — | 24 (10 renamed + 14 sharpened stale) |

## Method

1. Re-enumerated the live set against the funclet-ownership map (342) and diffed it with
   `b9a4_rem.json`: identical except the two batch-9 renames, confirming the scope.
2. Rebuilt an exact-body SHA-1 table for **all 5,422** function objects and regroups by
   hash. Result: **0 in-scope `rep_*` shares an exact body with any out-of-scope (named)
   function** — the "replica" hypothesis is still false after batch 9's renames; no name
   can be transferred by body identity.
3. Triaged by body size and distinctive callees, then decompiled 44 bodies (batches of
   ≤10 plus a decompiler-script dump under `decomp/`), skipping the generic
   `vector`/RbTree/string machinery that batch 9 already characterised.
4. Every rename is proved from the body (state fields, Box2D field writes, unique callee
   triple, or caller set), never from the embedded FID label. Names checked against the
   full function-name list for exact and token-subset (rule 8) collisions before applying.

## Renames (10) — all with doc plates

| addr | new name | proof |
|---|---|---|
| 0x140051e20 | `Body_SetLinearVelocity` | writes `+0x130/+0x134`, NaN-checks, then `b2Body.m_linearVelocity` (`+0x40/+0x44`) after waking the body; callers FireShell / Body_TearOffFromFrame / Ship_ClampPartsAndVelocity |
| 0x140051c40 | `Body_SetDensity` | `b2Body_SetType(0/2)` from density-zero test, rewrites fixture density (`Body_GetFixtureDensity()*0.05`), `b2Body_ResetMassData`, refreshes `+0x1d8` mass |
| 0x1400ec840 | `Escadra_TryMergeNearbyFleets` | same-side set (mask `0x147`) within `DAT_140354770`, plus stacked fleets at equal position; `Escadra_MergeAdjacentFleet`, `MapUi_SelectFleet` for player merges; sole caller `UpdateStrategicFleet` |
| 0x140073200 | `Creature_EnsureHistoryDesign` | guarded by `+0x19c0==0`; `Scene_CloneNodeSubtreeByName` / `HistoryDesign_CreateFromCreature`, appends link to `+0x19b8`; callers `Scene_InitializeForMode`, `Battle_ApplySurvivorState` |
| 0x1400fdf00 | `Escadra_ReportRadioEvent` | facing/distance gate vs `PLAYER_ESCADRA_`, `somethingRadio(event)` into string `+0x1a8`, pending flag `+0x1a5`, cooldown `+0x1c8`; strategic-AI callers |
| 0x140009db0 | `Aircraft_ApplyFlightForces` | normalises body velocity, steers `+0x70`, `powf` thrust/lift, applies force via body vtable `+0x190` and torque `+0x1a0`; called from `AircraftLogic_Tick` |
| 0x1400f5280 | `StrategicFleet_FindNearestHostileEscadra` | Profile fleet scan, ships `+0x2e8>1`, speed `+0x248!=0`, hostile side via vtable `+0x178`, skips already-targeted `+0x68`, min `Object_DistanceAt150`; caller `StrategicFleet_UpdateAIState` |
| 0x1400ea980 | `Creature_DistributeFuel` | proportional split of a fuel budget over missile spare capacity, `Creature::add_fuel`, fractional carry `+0x498`; sibling of `Creature_DistributeRepairPoints` |
| 0x1400f3dd0 | `Loadout_BuildAmmoIndex` | inserts loadout name (`+0x3f8`) into global `PLANE_LOADOUTS` with `compareEscadraString`, resolves each ammo via `FindAmmoIndex` |
| 0x14000e530 | `Aircraft_SetInterceptSolution` | fills solution block (`+0x2c` dist, `+0x30` valid, `+0x34` time, `+0x38` point, `+0x40` heading) from `ComputeInterceptPoint`; called from every `AircraftLogic_Mode*` |

No already-named function in this slice was proved wrong/misleading, so no
`-> rename` protocol post was needed.

## Sharper stale identities (14 re-recorded, no rename)

* `0x1400fe160` — three-pool weighted refill applied per missile via
  `rep_14005e820_GetStats`; called by `Creature_DistributeRepairPoints`,
  `addReinforceingShips`, `App_ReloadSeria` → `Creature_ApplyRefillToParts`.
* `0x1400f9460` — escadra-level refill: consumes budget `+0x4bc` (written by
  `Creature_DistributeRepairPoints`) and distributes `+0xd4` stat deltas over each
  missile's part list, then `Creature::CalculateStats(...,1)` → `Escadra_ApplyRefillBudget`.
* `0x1400f4c40` — weighted average of missile field `+0x24c` scaled by `+0x478`;
  callers `Squadron_UpdateFuelAndAmmo` / `displayShortage` → `Squadron_ComputeAverageFuelFraction`.
* `0x1400f0fb0` — post-battle missile-stat refresh/filter over `+0x100` (`ReturnToMap`
  family). `0x140054380` — map-object screen-visibility/zoom test (`manipulateMapObjects`).
* `0x140047920` — `Frame_BuildSnapEdgeSegments` (editor snap segments).
  `0x1400625a0` — `Creature_PruneDeadParts`. `0x140062e10` — battle-return part restore
  (`Body_RestoreDestroyedParts`).
* `0x1400eece0` — ship-target acquisition (`Escadra_AcquireShipTarget`).
  `0x1400f75d0` — random-design recall (`Escadra_BeginDesignRecall`).
* `0x1400f2de0` / `0x1400f32c0` — approach-distance siblings, no direct callers; need a
  suffix to name apart. `0x1400fb610` / `0x1400fbc10` — aircraft-group attack-waypoint and
  landing-approach state machines, both called only from `UpdateMapAircraftGroup`.

All 24 rows were appended to `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`; existing
rows untouched.

## Negative results

* Exact-body twins: 0 between the in-scope set and all 5,422 function objects.
* 14 × 52-byte `ShaderData_ResetVTable(); if(flag) free(this)` bodies remain the
  `ConstantBuffer<T>` slot-1 deleting destructor — still not nameable without a suffix.
* Vtable/RTTI again contributed nothing: the sample bodies in this range are not
  constructor/destructor code, and vtable operands are scalars in this listing.
* The `0x140012xxx` `vector<0x38>` emplace overloads and the `std::` string/vector/RbTree
  machinery remain stale; batch 9's CORRECTION rows for them stand.

## Output

* 24 appended rows in `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`.
* Working dumps: `/tmp/opencode/hf_ghidra_sweep/b10a3_live.tsv`, `b10a3_allfunc.tsv`,
  `b10a3_meta.txt`, `b10a3_extra.txt`, `b10a3_names.txt`, `decomp/`.

## Counts

* audited: **342**
* renamed + plated: **10**
* stale label left: **332** (14 re-sharpened in q1)
* unreadable: **0**
* byte-identical named twins: **0**
