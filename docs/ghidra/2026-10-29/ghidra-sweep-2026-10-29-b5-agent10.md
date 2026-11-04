# Ghidra sweep 2026-10-29 — batch 5, agent 10 (0x140300000–0x14032FFFF, physics glue / Box2D tail)

Program `Highfleet.exe.unpacked.exe` v1.163 (`HighfleetServer`). Every rename
below was applied to a `FUN_*` in the range with a doc-style plate comment
(summary / Algorithm / Parameters / Returns).

Range census at the end of the pass: **196 function objects**, 151 named,
**6 unnamed `FUN_*`**, **39 `rep_*` left untouched** (§4).

Counts: **13 renamed, 0 created, 6 skipped** — no `create_function` was needed;
every vtable slot in the range that holds real code already had a function
object.

## Renames (13)

| addr | new name | evidence |
|---|---|---|
| 0x140309d70 | `World_Render` | main per-frame world draw. Only real caller is the game loop at 0x1403051b2, bracketed by `Render_SetBlendEnabled(1)` / `(0)`. Accumulates `DAT_148075e40` from `__Xtime_get_ticks`, draws the fullscreen background through the HGE vtable (+0x80), then per layer 0x3c..0x45 runs the HUD marker passes and per layer 0x3b..0xa the body render virtuals. |
| 0x1403169c0 | `GraphicsQuality_ApplyToSettings` | maps the global `graphicsQuality` into the settings struct at 0x14801fd00 (8 bool feature flags + an int budget of 0 / 1000 / 20000). Called from `Gui_HandleSliderChange` (quality slider) and from the graphics-init branch 0x1402acb0c. |
| 0x140316ba0 | `FrameLimiter_Update` | adaptive limiter: scales `Perf_GetFps` by the busy fraction, 150 frames above 75 fps decrement `curFrameLimiter`, 50 frames below 50 fps increment it, logging `"curFrameLimiter = %d"`; sets `ArrayLoadedByMedia_res+0x1c5` to present every Nth frame. Called from the main loop right before `World_Render` (0x14030518d). |
| 0x140318b20 | `b2PolygonShape_ComputeAABB` | transforms the 16-vertex array at shape+0x18 (count +0x98, radius +0xc) and writes min/max + radius. It is the b2PolygonShape vtable entry at 0x140352a00, between `b2PolygonShape_RayCast` 0x1403198d0 and `b2PolygonShape_ComputeMass` 0x140319180. |
| 0x140321930 | `b2SortHeapAdjustPairs` | MSVC `_Adjust_heap` / `_Pop_heap_hole` for 0xc-byte elements. Its only caller is the std::sort instantiation 0x140321a80, which is called by `b2BroadPhase_UpdatePairs` 0x140321240 on the pair buffer at broadphase+0x40 (count +0x4c, **12-byte pairs**). |
| 0x140325a40 | `b2Contact_DeletingDtor` | installs the `b2Contact` vtable 0x140378a80 and frees when `edx&1`; the single ICF-merged destructor for all seven contact vtables (matches batch-4 agent 1's note). |
| 0x140328b60 | `b2ContactSolver_SolveTOIPositionConstraints` | TOI-only position pass: bias `0.75*C + 0.00375` clamped to [-0.2,0], extra mass terms for `toiIndexA/B`, returns `minSeparation >= -0.0075`. Caller `b2Island::SolveTOI` 0x140324330 runs it up to `positionIterations` times. |
| 0x14031d4f0 | `b2DistanceJoint_DeletingDtor` | vtable [5] of 0x140378838. |
| 0x14031e360 | `b2WeldJoint_DeletingDtor` | vtable [5] of 0x1403788f8. |
| 0x14032bb20 | `b2MouseJoint_DeletingDtor` | vtable [5] of 0x140378b30. |
| 0x14032c290 | `b2PrismaticJoint_DeletingDtor` | vtable [5] of 0x140378ba0. |
| 0x14032c2c0 | `b2PrismaticJoint_Dump` | vtable [4] of 0x140378ba0; prints the `b2PrismaticJointDef` reconstruction (`jd.bodyA`, local anchors/axis, limit/motor fields). |
| 0x14032dc80 | `b2GearJoint_DeletingDtor` | vtable [5] of 0x140378c78. |

### Joint / contact vtable layout confirmed here

Each joint vtable in this build is six slots, not the stock order:

```
[0] GetAnchorA   [1] GetAnchorB   [2] GetReactionForce
[3] GetReactionTorque   [4] Dump   [5] scalar deleting destructor
```

so the destructor is slot **[5]**, and `Dump` slot **[4]**. The five joint
destructors above (and `b2Joint_DeletingDtor` 0x14031bf20 /
`...Copy2` 0x14031bf50 / `...Copy3` 0x140324ac0) all contain the *same* 0x2b-byte
body: store the **b2Joint base vtable 0x140378570**, then `free` when bit 0 of
`edx` is set. They do not restore the derived vtable because the derived classes
add no members to destroy; MSVC emitted the base destructor inline in each class
section, so there is one copy per class rather than one ICF-merged body. Do not
"fix" them to a single name — the vtable slots point at distinct copies.

`b2Contact`'s destructor *is* ICF-merged: all seven contact vtables point at
0x140325a40 (base vtable 0x140378a80), which is why it looked like an unnamed
oddity next to `b2Contact_Construct`.

## Answers / corrections for the existing notes

1. **`b2Pair` is 12 bytes in this build** (stock 2.3.1 is 8). The broadphase pair
   buffer at `b2BroadPhase+0x40` is indexed by `index*3*4` and the sort at
   0x140321a80 divides the byte length by 0xc. Use 0xc when walking
   `m_pairBuffer`, and remember element bytes +0/+4 are `proxyIdA/proxyIdB`
   (the third dword is still unidentified). Add this to
   `box2d-function-map.md` next to `b2BroadPhase_UpdatePairs`.
2. **`rep_1402f9340_FastFail?` 0x140324330 is actually `b2Island::SolveTOI`.**
   Its body copies the island's body positions/velocities into a
   `b2ContactSolver`, loops `SolveTOIPositionConstraints` (`positionIterations`
   from `param_2[4]`), then `SolveVelocityConstraints`, clamps velocities
   (`|v|^2 > 4`, `|w| > pi/2`) and writes the results back. The `rep_*` name is
   wrong but was left in place per §4 — flagging it here.
3. **`b2ContactSolver` has a seventh method** that the function map is missing:
   `SolveTOIPositionConstraints` 0x140328b60 (see above). The pair
   `SolvePositionConstraints` 0x140328470 (Baumgarte 0.2, -0.015) /
   `SolveTOIPositionConstraints` (0.75, -0.0075) is the stock 2.3.1
   discrete-vs-TOI split.
4. **`b2Body`'s destructor is an empty 3-byte function** at 0x140319da0, but it
   is *not* nameable as `b2Body_Destructor`: the same `ret` is ICF-merged with
   `_guard_check_icall` 0x140005e70 and is called both on a `b2Body` (end of
   `b2World_DestroyBody` 0x14031abce, immediately before `Free(body, 0xb8)`)
   and on `world+0x80` (end of `SuperBigDeconstructor` 0x14031a741). It is the
   compiler's shared empty destructor, so it was left `FUN_`.
5. `b2Body` empty dtor aside, there is no other missing Box2D vtable target in
   this range: every slot of the distance / weld / mouse / prismatic / gear /
   pulley / wheel / friction / rope / revolute / contact tables resolves to a
   function object (named or a `rep_`).

## Skipped (recorded, not renamed)

| addr | size | why |
|---|---|---|
| 0x1403160a0 | 0x4b | 9-argument descriptor initialiser: writes +0xc, +0x10, +0x30, +0x34, +0x38, +0x3c, +0x44, +0x48 (=999 sentinel) and +0x60. Stored as a function pointer in the 0x28-byte record table at 0x1403770d8 and called via computed call from `playCloudByDistance?` 0x1402ee5f0. The owning struct (a city/cloud element descriptor) is not identified, so a name would be a guess. |
| 0x1403160f0 | 0x51 | 11-argument sibling of the above (adds +0x4c, takes +0x48 from the caller); pointer at 0x140377120, called 4x from `generateCityLandscape` 0x1402eeb90. Same reason. |
| 0x1403161a0 | 0x84 | `(layer, index)` → sets `_DAT_148075d50/_d54`, validates the index in the layer vector at `DAT_14801dd00`, then calls 0x140316a50 with body fields +0x38/+0x44. Called from `Gui_FlushDrawList` 0x1402fa10b. It is the "refresh one body's zoom scale" wrapper; the body fields fed to the pow helper are not identified. |
| 0x140316a50 | 0xd5 | calls the 0x140300db0 helper (misnamed `rep_..._pow`) with two floats, pushes the 24-byte result into five render objects via `compareAndUpdateFloatArray_` (+0x128 / +0x130 / +0x1b0), then `Property_SetFloat(obj+0x138, 0/1)` from `ZOOM_LEVEL * 0.142857 <= 0.4`. Almost certainly the zoom-LOD/property updater, but the callee and the five objects are unidentified — skipped rather than guessed. |
| 0x140316d00 | 0x112 | advances a 0x38-stride list by `dt*scale` (+0x2c), expires entries (timer == -1, timer >= limit +0x28, or flag +0 set with a null Link +0x18), compacts and `freeLinkMemory_`s them. Callers are the two large frame functions; the element class (some linked sprite/animation) is not provable. |
| 0x140319da0 | 0x3 | 3-byte `ret`, ICF-merged empty destructor (see answer 4). Not attributable to one class. |

## `rep_*` in the range (left per §4)

39 `rep_*` remain, and the embedded names are unreliable: e.g.
`rep_1402da020_...pow` 0x1403050a0 is a 0x4cbd-byte frame/render function and
`rep_1402f6a90_VCRUNTIME140...memmove` 0x140321a80 is the 0xc-stride
std::sort. One is provably wrong in a way that matters (0x140324330 =
`b2Island::SolveTOI`, answer 2); the rest are duplicated CRT/game bodies whose
real names would need a byte-level match against 0x1402dxxxx/0x1402fxxxx.
Renaming them was out of scope for this task; recommend a dedicated pass that
matches each `rep_` body to its original by hash instead of trusting the
embedded name.

## Remaining work in the range

6 `FUN_*` (the five non-Box2D render/descriptor helpers above plus the shared
empty destructor) and 39 `rep_*`. **No unnamed Box2D helper remains in
0x140300000–0x14032FFFF.**
