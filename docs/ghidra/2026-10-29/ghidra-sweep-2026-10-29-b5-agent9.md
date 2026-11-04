# Ghidra sweep 2026-10-29 — batch 5, agent 9 (0x140200000–0x1402FFFFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range on entry: **31 unnamed `FUN_*`** and **322 `rep_*`**.
Result: **16 renamed** (all with a doc plate: summary / `Algorithm:` /
`Parameters:` / `Returns:`), **15 left unnamed**, **0 created**.
`rep_*` bodies were not touched (§4): they are ICF replicas of named
functions, e.g. `rep_1401f2e60_MSVCP140...` / `rep_1402a9430_...` chunks of
`Player_SendThrustCommands`.

No `create_function` calls, so no blackboard "creation" post was needed; no
vtable/pointer target in the range lacked a function object.

## Renames

### Prologue / endgame event passes (0x140203xxx–0x1402A9xxx)

| addr | new name | description |
|---|---|---|
| 0x1402038e0 | `Prologue_SpawnEventEscadra` | spawns the escadra of one prologue event; looks up creature "UR", forces the count override to 0 when the event point is < 5000 from it, then `somethingSpawnShips` + Escadra ctor |
| 0x1402077c0 | `Endgame_BuildEscadra` | weighted endgame hull catalogue (Borey / Nomad Mk2 / Nomad / Gryphon / Kormoran / Negev, optional Tarantul ARM, Wasp/Longbow, Typhon), picks the first hull at <= half budget then random fills to budget; builds the Escadra |
| 0x140297100 | `Prologue_PlaceCreatureGroups` | clusters profile creatures within 1400 units, sorts the clusters by size and pushes each member 1399 units from its nearest neighbour; copies the leader's scene position to the escadra |
| 0x1402a7f60 | `Prologue_SpawnEventGroups` | draws a random encounter group 2..6 for each creature (no other creature within 2000 may share it), then group 5 sets 5.0, group 2 adds 100 and group 6 spawns up to five NPC records named after the creature |
| 0x1402a8760 | `Prologue_HideUnusedCraft` | clears the mode of unengaged craft groups, checks 0x14028bf80, renames them `HIDDEN`, and rebuilds the profile creature vector |
| 0x1402a9090 | `Aircraft_ComputeGroupAvailability` | min available/count over the PLANE_LOADOUTS entries of each linked craft (+0x7a8, +0x7a4), then the profile loadout count for the lead craft |

### Scene / level (0x140211xxx–0x140294xxx)

| addr | new name | description |
|---|---|---|
| 0x1402114a0 | `Scene_FitLevelBounds` | averages player-fleet positions within 1500, builds a 1500-unit box, clamps it to the level bounds, sets `ZOOM_LEVEL=3`, marks creatures on/off screen at +0x16f and clamps the overflow with `Ship_ClampPartsAndVelocity` |
| 0x140224ec0 | `Scene_LoadMapSeria` | resets the 0x148 scene block, `PM::Load` of the profile path + argument, clamps the localisation tables, then `Map.seria` or `EditorSkirmish.seria` (when `BOOL_147fc6f80`) |
| 0x1402943f0 | `Scene_RebuildFromProfile` | kills and rebuilds every scene object list after a load, recalcs the missile creature stats, assigns fresh random ids, constructs the scene object (`DAT_143a119d0`) and frees stale ship property children |

### Battle / HUD (0x14022Axxx–0x140245xxx)

| addr | new name | description |
|---|---|---|
| 0x14022ad00 | `Creature_SpawnImpactDebris` | ray-cast impact fan, debris_01/debris_03/debris.psi particles and an additional shell body (mass/velocity/fire/spin) at a shell impact |
| 0x140245180 | `Hud_DrawIncomingShellWarnings` | perimeter ray sweep from the most-threatened creature and from the player creature, stores warning points, draws rects and the blinking threat count, lazily loads the `sign_shell_*` / `sign_prize` sprites by ammo caliber (+0x144) |
| 0x140233490 | `Math_ComputeInterceptPoint` | bisection (<= 100 iters) over the target motion segment for a projectile with initial speed / acceleration and boost duration; returns the lead point |
| 0x140256a90 | `Ship_UpdatePartElevation` | recomputes `m_floor` (+0x9b8) per hull part from `m_floor_type` (+0x9b0) AUX/SUP/EXTRA bits, propagating to linked parts until stable |
| 0x140263700 | `SCR_MISSILE_AssignDefender` | picks and links the interceptor; logic id 1 for a `_CONV` attacker, 10 otherwise, sorted by `List_MergeSortByTargetF8` |

### GUI / profile (0x140232xxx, 0x14028Axxx)

| addr | new name | description |
|---|---|---|
| 0x140232830 | `Gui_ComputeCardRowLayout` | fits a row of fleet cards (min 20x20, evac pods fixed) into the window, per-card or uniform scale capped at 0.5; used by the pre-combat and shipworks result layouts |
| 0x14028a980 | `Profile_LoadSavesFromFolder` | builds `<entry>/profile.seria`, matches the `Profile_` prefix and loads each profile with `Profile_LoadSaveFile` |

## Left unnamed (15 `FUN_*`)

| addr | size | reason |
|---|---|---|
| 0x140211e60 | 1404 | 2-D cell-list merge/flood; only caller is an ICF `rep_` chunk (`tooLongError`), role unproven |
| 0x1402130b0 | 105 | get-or-create singleton `DAT_143a13b08` + status at +0x3cc; transitions 1->0. Owning class not proven |
| 0x140213fc0 | 109 | same singleton, transitions 0/1->2, 3->2; class not proven |
| 0x140216f00 | 356 | copies ship +0x15d0 into creature +0xf8 and sorts; +0x15d0 still unknown (same reason as batch 3/4) |
| 0x14021b110 | 117 | vtable +0xb8 name lookup then vector realloc + vtable +0x50 add; owner unproven |
| 0x14021cf40 | 8696 | 70 KB decompiled, only caller `repairSlider?`; contains main.cpp `CHECK ERROR`; not read |
| 0x14021fdb0 | 88 | reads `DAT_143a13a78` as an object at +0x100 and forwards to an ICF `rep_` chunk; real callee not identifiable |
| 0x1402410b0 | 12 | `CopyString(param_1, &DAT_143a13a78)`, but 0x14021fdb0 / 0x140216f00 read that global as an object; type contradiction (batch 3 flag) |
| 0x140247850 | 1843 | rotating ray fan + `Gfx_DrawWorldLine` over body pairs; colour fields (+0x3d0, +0x7b0) not decoded, role (tracers vs links) unproven |
| 0x140268a30 | 162 | string replace loop with a garbled `memcmp` return use (batch 3 flag) |
| 0x140269d00 | 731 | pushes thrust spasm codes 100/0x65/0x66/0x67 at +0x6e; only callers are unnamed ICF chunks |
| 0x14028b340 | 20 | argument-shuffling wrapper around a `rep_` free; no behaviour of its own |
| 0x14028bf80 | 1194 | state consistency test over profile+0x210 / creature +0x2e8 / parts +0x320; the meaning of +0x2e8 is not documented |
| 0x140292820 | 31 | argument-shuffling wrapper around a `rep_` free (batch 3 flag) |
| 0x140296530 | 3023 | draws eight ints in [-2,2] at +0x128..+0x144 with |sum| < 12 and exactly three |v| > 1; consumer of those fields not identified |

## What remains in the range

* the 15 `FUN_*` above;
* 322 `rep_*` ICF replicas, intentionally left (§4).

No other `FUN_*` in 0x140200000–0x1402FFFFF.
