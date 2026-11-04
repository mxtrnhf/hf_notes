# Ghidra sweep 2026-10-29 — batch 6, agent 5 (`rep_*` re-match, 0x140300000–0x140336FFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` function with entry in **0x140300000–0x140336FFF**
(the 0x140337000–0x140350510 funclet tail belongs to agent 1).

* `rep_*` in scope at start: **50**
* left at end: **22**
* **28 renamed and plated**, **22 stale-label (recorded, not renamed)**, **0 unreadable**
* no `save_program`, no tags, no README/STATUS edits, no commits, no `create_function`.

Audit table: `rep-audit-2026-10-29-q4.tsv` (50 rows).

## Confirmation of the batch-5 finding

Batch-5 agent 5's conclusion holds for this range too, and is if anything
cleaner:

1. **No byte-identical twin.** SHA-1 over every function body in the program
   (`rep_*` vs all 5 155 functions) gives **0 twins for all 50** in-range
   `rep_*`. Nothing here is ICF-folded.
2. **The embedded target is a stale address, not a replica.** Of the 42 names
   that parse as `rep_<hex>_<name>`, all 42 embed an address in
   0x1402d5xxx–0x14030xxxx. **40 of the 42 land inside an unrelated function**
   (usually mid-instruction): e.g. `rep_1402d5ce0_...pow` at 0x140300db0 →
   0x1402d5ce0 lies inside `PlayRadioSounds?` 0x1402d5910;
   `rep_1402f8ac0_FastFail?` at 0x140323ab0 → 0x1402f8ac0 lies inside
   `displayShortage` 0x1402f84d0; all five `_CxxThrowException` reps point into
   the 16 304-byte 0x14030a6b0; the three CRT-tail reps point into
   `World_Render` / 0x1403050a0. The other **2 are not function entries at all**
   (0x1402f0140, 0x1402f4c40). **None** of the embedded targets is a copy of
   the body.
3. **Sizes are absurd for the claimed imports**: “pow” = 17 122 / 17 814 bytes,
   “memmove” = 711 bytes (it is the 0xc-stride recursive pair sort),
   “memset” = 194 bytes (it is `b2DynamicTree_Constructor`),
   “free” = 1 068 bytes (it is `Hud_DrawDamageMarkers`).

Practical rule used here: parse the embedded address only to record it; never
as evidence. Every rename below comes from the body, its callees/strings and
(when available) the vtable slot.

## The range is not a duplicate section — it is the real Box2D / HUD code

This is worth stating because the `rep_*` prefix misleads: 0x14031xxxx–0x14032xxxx
is the **live Box2D implementation** that the already-named `b2*` functions in
0x1402fxxxx and 0x140330xxx call into, and 0x14030xxxx–0x14031xxxx is the live
HUD/video-task code called by `SomethingVideoTask` (0x140316e20) and the
`World_Render` loop.

### Box2D allocator / tree / contact cluster (14)

Stock Box2D 2.3.1 layout, matched field by field:

| addr | new name | key evidence |
|---|---|---|
| 0x140320720 | `b2BlockAllocator_Constructor` | builds the 641-entry size-class table (`0x280` = `b2_maxBlockSize`), 0x4000 chunk; caller `SuperBigConstructor` |
| 0x140320890 | `b2BlockAllocator_Clear` | frees every block of every chunk then the chunk array; caller `SuperBigDeconstructor` |
| 0x1403208e0 | `b2BlockAllocator_Alloc` | free list at `this+0x10`, grows chunk array by 0x80; callers `b2Joint_Create`, `b2Body_CreateFixture`, `b2World_CreateBody`, `b2Fixture_Create` |
| 0x140320a40 | `b2BlockAllocator_Free` | >0x280 → `free`, else push on size-class list; callers `b2Fixture_Destroy`, `b2Joint_Destroy`, `b2World_DestroyBody`, `b2Contact_DestroyAllocated200` |
| 0x140320a80 | `b2Alloc` | `MOVSXD RCX,ECX; JMP [0x1403516e8]` (malloc IAT) — int32-size allocator used by every b2 tree/broadphase call |
| 0x140320aa0 | `b2Log` | `__acrt_iob_func(1)` + `__stdio_common_vfprintf`; hammered by `b2RevoluteJoint_Dump` |
| 0x140321d50 | `b2ContactManager_Construct` | `b2BroadPhase_Construct` then list/count at +0x58/+0x60, default filter/listener at +0x68/+0x70, allocator +0x78 — exactly `b2ContactManager` |
| 0x1403227f0 | `b2DynamicTree_Constructor` | 0x10 nodes × 0x28 B at `this+8`, free-list threading, −1 terminators; caller `b2BroadPhase_Construct` |
| 0x1403228c0 | `b2DynamicTree_Destructor` | `MOV RCX,[RCX+8]; JMP free`; caller `b2BroadPhase_Destructor` |
| 0x1403237a0 | `b2BroadPhase_Destructor` | frees move buffer +0x30, pair buffer +0x40, then the tree |
| 0x1403238f0 | `b2BroadPhase_AddPair` | 12-byte pair insertion with `b2Min/b2Max`, skips `m_queryProxyId` (+0x50); this is the `UpdatePairs` callback body — the 12-byte `b2Pair` note from agent 10 is confirmed |
| 0x140323ab0 | `b2Island_Report` | per-contact impulse records → listener vtable **+0x20 = PostSolve**; callers `b2Island_Solve`, `b2Island_SolveTOI` |
| 0x140325d00 | `b2Contact_Update` | manifold refresh, TOI flag from bullet bits, TOUCHING/ENABLED transitions, `Begin/End/PreSolve`; caller `b2ContactManager_Collide` |
| 0x14031b130 | `b2World_SolveTOI` | `b2Island_Construct` → `b2TimeOfImpact` → `b2Island_SolveTOI` → `b2Body_SynchronizeFixtures` → `b2ContactManager_FindNewContacts` → `b2Island_Destruct`; sole caller `b2World_Step` |

Also `b2Distance` **0x14031fc30** (2 795 B): `b2Simplex_ReadCache` +
`b2Simplex_Solve` witness-point loop, called twice from `b2TimeOfImpact` and
from the distance helper 0x140318920 — the real `b2Distance`, previously
`rep_1402f4c40_FastFail?`.

### Box2D sort helpers (2)

| addr | new name | evidence |
|---|---|---|
| 0x140321a80 | `b2SortPairsRecursive` | recursive introsort over 0xc-byte pairs; callers `b2BroadPhase_UpdatePairs` + itself; uses `b2SortPairs` and `b2SortPairs_AdjustHeap` |
| 0x140321390 | `b2SortPairs_AdjustHeap` | hole-based `_Adjust_heap` on 0xc-byte elements with caller predicate |

These are two *distinct* instantiations from `b2SortPairs` (0x140321620) and
`b2SortHeapAdjustPairs` (0x140321930); do not collapse them.

### Shape / joint constructors (3)

| addr | new name | evidence |
|---|---|---|
| 0x140318a00 | `b2PolygonShape_Clone` | vtable 0x1403529d8 **slot 1 = Clone**; allocates 0xa0 via the block allocator and copies type/radius/16 vertices |
| 0x14032f440 | `b2FrictionJoint_Constructor` | `b2Joint_Ctor` + vtable **0x140378d18** (slot 4 = `b2FrictionJoint_Dump`) + localAnchorA/B, maxForce, maxTorque |
| 0x14032fdf0 | `b2RopeJoint_Constructor` | `b2Joint_Ctor` + vtable **0x140378dc0** (slot 6 = `b2RopeJoint_InitVelocityConstraints`, slot 4 = 0x14032fe50) + localAnchorA/B, maxLength |

The joint vtable layout is the 9-slot one agent 9 mapped
(`[0]GetAnchorA [1]GetAnchorB [2]GetReactionForce [3]GetReactionTorque [4]Dump
[5]scalar-deleting-dtor [6]InitVelocity [7]SolveVelocity [8]SolvePosition`);
the `Dump` slot (4) plus the named `InitVelocityConstraints` at slot 6 is what
identified the two classes. Agent 10's “six slots” was only the prefix that is
populated per class.

### Profiling timer trio (3)

`PerfTimer_InitAndRead` 0x140327810 (caches `1000/freq` in `DAT_148076bb8`),
`PerfTimer_ElapsedMs` 0x140327890, `PerfTimer_ReadTicks` 0x1403278d0 — all
called from `b2World_Step` / `b2Island_Solve`, all around `QueryPerformanceCounter`.
These are the `b2Timer`-style helpers; the `b2Timer_*` names were avoided
because 0x140327810 also does the one-time frequency init.

### HUD / video-task (4)

| addr | new name | evidence |
|---|---|---|
| 0x1403007f0 | `Hud_DrawDamageMarkers` | body gates on `Body_IsBadlyDamaged` + `Hud_MarkerCheckChildFlag`, builds a four-band colour ramp from `calcDMGPercentage`, draws with `Hud_DrawChildMarker`/`Hud_DrawQueuedSprite` |
| 0x140300c20 | `VideoTask_Dispatch` | resets HGE state, sets shader flags 130/131/132, logs a `VideoTask.cpp` CHECK ERROR, dispatches to one of five scene routines on the task index; two calls from `SomethingVideoTask` |
| 0x1403137f0 | `Hud_DrawZoomGrid` | draws the zoom graticule through HGE vtable +0x2c8 at 10/100/1000-px cells divided by `ZOOM_LEVEL`, gated by zoom < 3 / < 4 |
| 0x140313f40 | `Hud_DrawNoiseFrame` | `loadMediaByName_("noise_01")` then four copies at (w/2 ± 350, h/2 ± 315) with HGE-time flips |

### CRT entry point (1)

`mainCRTStartup` 0x140334c54 is the **PE entry-point target**: `__scrt_initialize_crt`,
startup lock, `_initterm_e`/`_initterm`, thread-local atexit registration,
`Main()`, `__scrt_uninitialize_crt`/`exit`. The adjacent 0x140334b70 is the
earlier `_set_app_type`/`_configure_narrow_argv` stage; it is **left stale**
because the exact `__scrt_*` split is not provable from the body alone.

## Stale labels left (22)

Recorded in the TSV with a partial identity; none is renamed. Summary:

* **VideoTask scene routines (5)**: 0x140300db0 (17 122 B, TV screen / “ MIN” /
  `tv_screen_02`, uses the fullscreen quad), 0x1403050a0 (19 645 B, calls
  `FrameLimiter_Update`/`World_Render`), 0x14030a6b0 (16 304 B, `MAP_SKY`,
  `MAPMARK_*`, `MAPMODE_FLEET`), 0x14030e670 (3 034 B, fullscreen colour fade),
  0x14030f250 (17 814 B, `tv_screen_02` + `heathaze.png`). These are the five
  targets of `VideoTask_Dispatch`; which `VideoTask-N` string each maps to is
  not established, so they stay stale with the partial identity in the TSV.
* **Map-mode HUD (2)**: 0x140314290 (radar/`button_red`/`FindGuiElement`),
  0x140315580 (campaign panel matrix setup).
* **Animation/data helpers (3)**: 0x140315b40 (500-float array ramp),
  0x140316230 (0x28-stride ship-card transform vector), 0x1403182a0
  (`_Xtime_get_ticks` delta clamp, caller `BattleSpawner_SpawnShips`).
* **Box2D helper without stock name (1)**: 0x140318920 — fills two
  `b2DistanceProxy`, builds a `b2DistanceInput` and calls `b2Distance`; called
  from `b2Contact_Update` and 0x140047ef0. A wrapper, no canonical name.
* **CRT startup / thunks (6)**: 0x140334b70, 0x140334c28, 0x140334de0,
  0x140334e43, 0x14033535c, 0x1403353a4 (incl. the SSE2-sinf4 stubs at
  0x140334de0/0x140334e43 and the `_guard_dispatch_icall` thunk).
* **EH cleanup funclets (5)**: 0x140336c80, 0x140336d20, 0x140336df0,
  0x140336ea0, 0x140336f00 — each does `DeleteArray*`/memmove cleanup then
  `_CxxThrowException`. Owner resolution belongs to agent 1's `.pdata` pass;
  named here only as `EH cleanup funclet`.

## Not touched

* `0x140324330` is already `b2Island_SolveTOI` (parent fix) — outside this
  range anyway.
* `0x140320a90` (`free`, 7-byte `JMP [0x1403516d0]`) is not a `rep_*` and was
  left as is; it is the `b2Free` analogue of `b2Alloc`. Flagging it for a future
  pass rather than renaming outside the `rep_*` rule.
* `0x14032fe50` (rope `Dump`, vtable slot 4 of 0x140378dc0) and
  0x14031c160/0x14031c1b0/0x14031c220/0x14031c240 (shared joint slot-0/1/2/3
  bodies) are `FUN_*`/`LAB_` and not in this agent's `rep_*` brief.

## Counts

* `rep_*` in scope: **50**
* renamed + plated: **28** (14 allocator/tree/contact, 3 “distance/sort”, 3 shape/joint,
  3 timer, 4 HUD/video, 1 CRT entry — see TSV for the exact split)
* stale label: **22**
* unreadable: **0**
* `rep_*` left in scope: **22**; `FUN_*` in scope unchanged (27, other agents' brief)
