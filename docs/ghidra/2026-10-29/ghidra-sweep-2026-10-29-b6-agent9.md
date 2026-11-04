# Unnamed-function sweep — batch 6 agent 9 (CRT/Box2D remainder)

Ranges: `0x140000000–0x14006FFFF` and `0x140300000–0x140336FFF` on
`Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`). Role: `FUN_*`
only (no `rep_*`, no funclets — those belong to agents 1–5).

Counts: **4 renamed + plated, 36 created + named + plated, 33 skipped/recorded.**
Unnamed `FUN_*` at the start of the pass: 8 in range 1 and 28 in range 2
(36 total, matching the batch-5 tail). After the pass: **5 `FUN_*` left in range 1
and 27 in range 2**, and every Box2D joint/shape vtable slot now has a function
object. Two further gaps are handed off, not touched: the 150-entry CRT
C-initialiser table and 19 Body/Node base-class slots (both below).

## Start census (script, `FUN_*` with function objects)

Range 1: `14000ad80`, `140017d10`, `140019310`, `140019380`, `1400211a0`,
`140027f90`, `1400458c0`, `140049cd0`.
Range 2: `1403160a0`, `1403160f0`, `1403161a0`, `140316a50`, `140316d00`,
`140319da0`, `1403340d8`, `140334e00`, `14033503c`, `140335050`, `140335354`,
`14033536c`, `140335388`, `140335394`, `14033539c`, and the 13 `/EH` cleanup
objects `140336730–140336f50`.

## New structural finding: the Body/Creature vtable block

`0x140352a30` = `BodyVFTABLE`, `0x140354c40` = `CreatureVFTABLE` (RTTI locator at
`-8`), plus two more unnamed 0x100-aligned copies at `0x14035e1d0` and
`0x140360670`. They are **not** separate classes with separate code: all four share
the same slot table from `+0x100` upward (only the class-specific slots differ, e.g.
`Creature_EnableBody`/`Creature_DisableBody` in the creature table). Confirmed slot
map, `+0x100 …`:

| slot | offset | function |
|---|---|---|
| 32 | +0x100 | `0x1400055c0` (`xor al,al; ret`, shared "return false" stub) |
| 33 | +0x108 | `0x140018fb0` (unnamed atexit-style thunk) |
| 34 | +0x110 | `0x140018fa0` (`Frame_ResetCounter(); return 0`) |
| 35 | +0x118 | `0x1400055c0` again |
| 36 | +0x120 | **`Body_OnHoverEnter`** (was `FUN_140019310`) |
| 37 | +0x128 | **`Body_OnHoverLeave`** (was `FUN_140019380`) |
| 38 | +0x130 | `Creature_EnableBody` |
| 39 | +0x138 | `rep_1400191c0_MakeGlobal?` |
| 40 | +0x140 | `Creature_DisableBody` |
| 41 | +0x148 | `AlwaysReturn1` |
| 42 | +0x150 | `Body_CollectSelfLinkIfDropped` |
| 44 | +0x160 | `Body_SyncFromB2` |
| 45 | +0x168 | `Body_PreStepUpdate` |
| 46 | +0x170 | `Body_AddForceAtPoint` |
| 47 | +0x178 | `Body_AddForceAtCenter` |
| 80 | +0x280 | **`Body_BuildPartStatsText`** (was `FUN_1400211a0`) |
| 82 | +0x290 | `Body_BuildPartInfoPanel` |
| 83 | +0x298 | `0x14004bba0` (panel teardown called from `Body_OnHoverLeave`) |

## Renamed (4)

| addr | old | new | evidence |
|---|---|---|---|
| 0x140019310 | `FUN_140019310` | `Body_OnHoverEnter` | virtual slot [36] of BodyVFTABLE/CreatureVFTABLE (+0x120). Body: gate `DAT_143a11962`, class-id check `byte(this+0x28)&0x1f != 0x1f` on this and on `DAT_1403c0d88`, calls `vtable+0x290` (`Body_BuildPartInfoPanel(this,0)`), then `vtable+0x280` (`Body_BuildPartStatsText(this,0,0)`) when `+0x7c8 != 0`, sets byte `+0x9e0 = 1`, stamps the frame time, returns 1. **Only caller is `Scene_UpdateHoveredNode` 0x14018da06**, which invokes it on the newly picked node immediately after running slot [37] on the previously hovered node. |
| 0x140019380 | `FUN_140019380` | `Body_OnHoverLeave` | virtual slot [37] (+0x128). Calls `vtable+0x298` (`0x14004bba0(this)`) when `+0x9d0 != 0`, clears `+0x9e0`, calls `Frame_ResetCounter()`. Caller `Scene_UpdateHoveredNode` 0x14018d9ee, on the node being left. Flag `+0x9e0` is read only in `Creature_DebugDrawDetails` 0x14004d4a5 and the loot-box code, consistent with a "hovered/selected for panel" flag; `+0x9e1` (0x9e0+1) is the separate pause flag of `Creature_EnableBody`/`DisableBody`. |
| 0x1400211a0 | `FUN_1400211a0` | `Body_BuildPartStatsText` | virtual slot [80] (+0x280) of the same tables, called from `Body_OnHoverEnter`. 9 142-byte body that emits HGE rich-text markup (`{font=dinpro_20_black}{align=2}{color=…}`, `{font=flash_large}`) around `DAMAGE_STAT`, `PRICE_STAT`, `FIREPOWER_STAT`, `FIRE_RATE_STAT`, `CLIP_AMOUNT_STAT`, `THRUST_STAT`, `POWER_STAT`, `POWER_NEED_STAT`, `FUEL_STAT`, `FUEL_NEED_STAT`, `AMMO_NEED_STAT`, `GAME_DMG_RAD`, `sign_contamination_big`, `gui_mil`; pulls the numbers from `GetStats` 0x14002de30, `displayDescriptionOfPart?`, `tutorialForPartName`. |
| 0x140334e00 | `FUN_140334e00` | `__sincosf` | scalar AMD-libm sincos: `|x| < 2^-13` → packed `{x, 1-x²/2}`, otherwise packed `{x, |x|+π/2}` and tail-jump into `__sse2_sinf4` 0x140335420, so lane0 = `sinf(x)`, lane1 = `cosf(x)`. Called twice by `b2RopeJoint_SolvePositionConstraints` 0x140330460. Batch-5's proposed name; no symbol string survives, this is the descriptive family name next to `__sse41_sinf4`. |

## Created (36) — Box2D vtable slots with no function object

Posted to the blackboard as `@agent9 -> creation` at 12:36 MSK (with the full slot
evidence) and created after the cycle with no objection. Every address was checked
first: no containing function, valid instruction at the address, and a qword slot of
a confirmed joint/shape vtable.

This build's joint vtable layout (9 slots, confirmed against the already-named
neighbours on all 10 joint tables):

```
[0] GetAnchorA   [1] GetAnchorB   [2] GetReactionForce   [3] GetReactionTorque
[4] Dump   [5] scalar deleting destructor
[6] InitVelocityConstraints   [7] SolveVelocityConstraints   [8] SolvePositionConstraints
```

(NB batch-5 agent 10 described six slots; the tables actually reach `[8]`, and the
`Init`/`Solve` slots are what made `b2WheelJoint`/`b2PulleyJoint`/`b2MouseJoint`/
`b2FrictionJoint` look incomplete.)

| addr | name | vtable · slot | body proof |
|---|---|---|---|
| 0x14031bf80 | `b2Joint_DumpNotSupported` | b2Joint 0x140378570 · [4] | `LEA RCX,[s_//_Dump_is_not_supported_for_this_type]; JMP printf` |
| 0x14031c160 | `b2Joint_GetAnchorA` | shared [0] of revolute 0x1403785e8, prismatic 0x140378ba0, friction 0x140378d18, rope 0x140378dc0 | `mov rax,[rcx+0x60]` (m_bodyA) + localAnchorA `+0x80/+0x84` rotated by bodyA angle |
| 0x14031c1b0 | `b2Joint_GetAnchorB` | shared [1] of the same four | `mov rax,[rcx+0x68]` (m_bodyB) + `+0x88/+0x8c` |
| 0x14031c220 | `b2Joint_GetReactionForce` | shared [2] of revolute + friction | `impulse(+0x90) * inv_dt` |
| 0x14031c240 | `b2Joint_GetReactionTorque` | shared [3] of revolute + friction | `m_impulse.z(+0x98) * inv_dt` |
| 0x14031d720 | `b2Joint_GetReactionTorqueZero` | shared [3] of distance 0x140378838, pulley 0x140378960, mouse 0x140378b30, rope | `xorps xmm0,xmm0; ret` |
| 0x14031d650 | `b2DistanceJoint_GetAnchorA` | distance · [0] | `[rcx+0x60]` + `+0x8c/+0x90` |
| 0x14031d6a0 | `b2DistanceJoint_GetAnchorB` | distance · [1] | `[rcx+0x68]` + `+0x94/+0x98` |
| 0x14031d6f0 | `b2DistanceJoint_GetReactionForce` | distance · [2] | `impulse(+0xa0) * inv_dt` |
| 0x14031e4c0 | `b2WeldJoint_GetAnchorA` | weld 0x1403788f8 · [0] | `[rcx+0x60]` + `+0x90/+0x94` |
| 0x14031e510 | `b2WeldJoint_GetAnchorB` | weld · [1] | `[rcx+0x68]` + `+0x98/+0x9c` |
| 0x14031e560 | `b2WeldJoint_GetReactionForce` | weld · [2] | `impulse(+0xa8) * inv_dt` |
| 0x14031e580 | `b2WeldJoint_GetReactionTorque` | weld · [3] | `impulse.z(+0xb0) * inv_dt` |
| 0x140324c70 | `b2PulleyJoint_GetAnchorA` | pulley 0x140378960 · [0] | `[rcx+0x60]` + `+0x98/+0x9c` |
| 0x140324cc0 | `b2PulleyJoint_GetAnchorB` | pulley · [1] | `[rcx+0x68]` + `+0xa0/+0xa4` |
| 0x140324d10 | `b2PulleyJoint_GetReactionForce` | pulley · [2] | `+0xb0 * inv_dt` |
| 0x140324d40 | `b2PulleyJoint_InitVelocityConstraints` | pulley · [6] | prologue between dtor [5] and named `SolveVelocityConstraints` [7] |
| 0x14032ab50 | `b2WheelJoint_GetAnchorA` | wheel 0x140378aa8 · [0] | `[rcx+0x60]` + `+0x88/+0x8c` |
| 0x14032aba0 | `b2WheelJoint_GetAnchorB` | wheel · [1] | `[rcx+0x68]` + `+0x90/+0x94` |
| 0x14032abf0 | `b2WheelJoint_GetReactionForce` | wheel · [2] | spring/impulse mix `+0xa8/+0xb0` |
| 0x14032ac50 | `b2WheelJoint_GetReactionTorque` | wheel · [3] | `impulse.z(+0xac) * inv_dt` |
| 0x14032b6c0 | `b2WheelJoint_SolveVelocityConstraints` | wheel · [7] | between named Init [6] and SolvePosition [8] |
| 0x14032bb50 | `b2MouseJoint_Dump` | mouse 0x140378b30 · [4] | `LEA RCX,[s_Mouse_joint_dumping_is_not_supported]; JMP printf` |
| 0x14032bb60 | `b2MouseJoint_GetAnchorA` | mouse · [0] | `movsd xmm0,[rcx+0x88]` (target as a b2Vec2-in-three-doubles) |
| 0x14032bb70 | `b2MouseJoint_GetAnchorB` | mouse · [1] | `[rcx+0x68]` + `+0x80/+0x84` |
| 0x14032bbc0 | `b2MouseJoint_GetReactionForce` | mouse · [2] | `impulse(+0x9c) * inv_dt` |
| 0x14032bf50 | `b2Joint_SolvePositionConstraintsTrue` | shared [8] of mouse + friction 0x140378d18 | `mov al,1; ret` (neither joint has position constraints) |
| 0x14032c470 | `b2PrismaticJoint_GetReactionForce` | prismatic 0x140378ba0 · [2] | `(impulse.x(+0xac) + springImpulse(+0xb0)) * inv_dt` |
| 0x14032c4d0 | `b2PrismaticJoint_GetReactionTorque` | prismatic · [3] | `impulse.z(+0xa8) * inv_dt` |
| 0x14032dd90 | `b2GearJoint_GetAnchorA` | gear 0x140378c78 · [0] | `[rcx+0x60]` + `+0xa8/+0xac` |
| 0x14032dde0 | `b2GearJoint_GetAnchorB` | gear · [1] | `[rcx+0x68]` + `+0xb0/+0xb4` |
| 0x14032de30 | `b2GearJoint_GetReactionForce` | gear · [2] | `impulse(+0xe8) * inv_dt` |
| 0x14032de60 | `b2GearJoint_GetReactionTorque` | gear · [3] | `+0x14c * impulse(+0xe8) * inv_dt` |
| 0x14032ff40 | `b2RopeJoint_GetReactionForce` | rope 0x140378dc0 · [2] | `impulse(+0x98) * inv_dt` |
| 0x14032fe50 | `b2RopeJoint_Dump` | rope · [4] | prints `b2RopeJointDef jd;` + `jd.bodyA/bodyB/localAnchorA/localAnchorB/maxLength` + `joints[%d] = m_world->CreateJoint(&jd);` |
| 0x140319bc0 | `b2PolygonShape_TestPoint` | b2PolygonShape 0x1403529d8 · [3] | point vs the `m_count` edges of the `+0x18` vertex array, non-strict half-plane test |

Verified after creation: each body is contiguous, starts at the vtable target and
does not overlap the next function object. The four shared bodies
(`b2Joint_GetAnchorA/B`, `b2Joint_GetReactionForce/Torque`, the zero-torque stub and
the `return true` stub) are ICF-merged and appear in several tables on purpose —
**do not "fix" them into per-class copies.**

### Post-pass body verification (all 36)

| addr | end | next object | size |
|---|---|---|---|
| 0x14031bf80 | 0x14031bf8b | 0x14031bf90 b2RevoluteJoint_Dump | 12 |
| 0x14031c160 | 0x14031c1af | 0x14031c1b0 (created) | 80 |
| 0x14031c1b0 | 0x14031c1ff | 0x14031c200 b2RevoluteJoint_GetJointAngle | 80 |
| 0x14031c220 | 0x14031c23f | 0x14031c240 (created) | 32 |
| 0x14031c240 | 0x14031c24b | 0x14031c250 b2RevoluteJoint_InitVelocityConstraints | 12 |
| 0x14031d720 | 0x14031d723 | 0x14031d730 b2DistanceJoint_InitVelocityConstraints | 4 |
| 0x14031d650 | 0x14031d69f | 0x14031d6a0 (created) | 80 |
| 0x14031d6a0 | 0x14031d6ef | 0x14031d6f0 (created) | 80 |
| 0x14031d6f0 | 0x14031d717 | 0x14031d720 (created) | 40 |
| 0x14031e4c0 | 0x14031e50f | 0x14031e510 (created) | 80 |
| 0x14031e510 | 0x14031e55f | 0x14031e560 (created) | 80 |
| 0x14031e560 | 0x14031e57f | 0x14031e580 (created) | 32 |
| 0x14031e580 | 0x14031e58b | 0x14031e590 b2WeldJoint_InitVelocityConstraints | 12 |
| 0x140324c70 | 0x140324cbf | 0x140324cc0 (created) | 80 |
| 0x140324cc0 | 0x140324d0f | 0x140324d10 (created) | 80 |
| 0x140324d10 | 0x140324d3f | 0x140324d40 (created) | 48 |
| 0x140324d40 | 0x1403252c8 | 0x1403252d0 b2PulleyJoint_SolvePositionConstraints | 1417 |
| 0x14032ab50 | 0x14032ab9f | 0x14032aba0 (created) | 80 |
| 0x14032aba0 | 0x14032abef | 0x14032abf0 (created) | 80 |
| 0x14032abf0 | 0x14032ac42 | 0x14032ac50 (created) | 83 |
| 0x14032ac50 | 0x14032ac5b | 0x14032ac60 b2WheelJoint_InitVelocityConstraints | 12 |
| 0x14032b6c0 | 0x14032ba56 | 0x14032ba60 b2MouseJoint_Ctor | 919 |
| 0x14032bb50 | 0x14032bb5b | 0x14032bb60 (created) | 12 |
| 0x14032bb60 | 0x14032bb6f | 0x14032bb70 (created) | 16 |
| 0x14032bb70 | 0x14032bbbf | 0x14032bbc0 (created) | 80 |
| 0x14032bbc0 | 0x14032bbdf | 0x14032bf50 (created) | 32 |
| 0x14032bf50 | 0x14032bf52 | 0x14032bf60 b2MouseJoint_SolveVelocityConstraints | 3 |
| 0x14032c470 | 0x14032c4ca | 0x14032c4d0 (created) | 91 |
| 0x14032c4d0 | 0x14032c4db | 0x14032c4e0 b2PrismaticJoint_InitVelocityConstraints | 12 |
| 0x14032dd90 | 0x14032dddf | 0x14032dde0 (created) | 80 |
| 0x14032dde0 | 0x14032de2f | 0x14032de30 (created) | 80 |
| 0x14032de30 | 0x14032de5f | 0x14032de60 (created) | 48 |
| 0x14032de60 | 0x14032de74 | 0x14032de80 b2GearJoint_InitVelocityConstraints | 21 |
| 0x14032fe50 | 0x14032ff39 | 0x14032ff40 (created) | 234 |
| 0x14032ff40 | 0x14032ff67 | 0x14032ff70 b2RopeJoint_InitVelocityConstraints | 40 |
| 0x140319bc0 | 0x140319c43 | 0x140319c50 b2Body_Ctor | 132 |

No neighbour was truncated: each created body ends exactly before the next function
entry, and every "next" object listed above was already there before the pass.

## End-of-pass census (script)

Range 1, 5 `FUN_*` left: `14000ad80` (11), `140017d10` (36), `140027f90` (120),
`1400458c0` (3342), `140049cd0` (35).
Range 2, 27 `FUN_*` left: the 5 render helpers + `140319da0` + `1403340d8` + the 7
`__scrt_*` stubs + the 13 `/EH` funclets `140336730–140336f50`; plus 22 `rep_*`
(agent 5's scope). `140334e00` is now `__sincosf` and `1403198c0` is now
`b2EdgeShape_GetChildCount`.

## b2PolygonShape vtable 0x1403529d8 (completed)

```
[0] 0x140018ba0 b2Shape_ScalarDeletingDestructorA
[1] 0x140318a00 Clone
[2] 0x1403198c0 b2EdgeShape_GetChildCount  <- created by another agent this batch
[3] 0x140319bc0 b2PolygonShape_TestPoint    <- created here
[4] 0x1403198d0 b2PolygonShape_RayCast
[5] 0x140318b20 b2PolygonShape_ComputeAABB
[6] 0x140319180 b2PolygonShape_ComputeMass
```

**Hand-off closed:** batch 4/5's open item `0x1403198c0`
(`b2Shape_GetChildCountOne`) now carries a function object named
`b2EdgeShape_GetChildCount`. The "shared `return 1`" caveat still holds — the same
body is used by every one-child shape — but the address is no longer a gap.

## Vtable-pointer scan of both ranges (data side)

Every 8-aligned qword in `0x140350000–0x1403C6000` pointing into either range was
resolved. Apart from the 36 created above, the remaining pointers to **code**
without a function object are all of one kind:

### 1. The CRT C-initialiser table — 150 targets, NOT created (recorded)

`0x1403519e8–0x1403521a8` is the MSVC `__xc_a`/`__xc_z` table: **249 entries, 150
unique targets in `0x140001000–0x140004a60`, none of which has a function object.**
They are genuine static-initialiser thunks, every one of the shape

```
LEA RCX,[<global>] ; JMP <vector-constructor-iterator / ctor>
```

(or `LEA RCX,[<global>]; LEA RAX,[<global+8>]; JMP …` for arrays), i.e. the
`_initterm` payload for one global each. This is a 150-function gap that would need
one `create_function` and one name per initialised global — a dedicated pass, not a
tail job. Recommended scheme: `CInit_<GlobalName>` derived mechanically from the
`LEA` operand (the name is then provable, not a guess). Not attempted here to avoid
bulk-creating 150 function objects under a time-boxed sweep; flagged for the parent.

### 2. Import thunks / CFG dispatch (not code of this program; never create)

`0x14033404c/52/5e/70/76/7c/82/88/8e` (std::streambuf import thunks),
`0x1403365ac` (`memmove` thunk, appears in ~25 unresolved "vtable-shaped" tables),
`0x14033664e`, `0x140336710` (CFG dispatch stub). Confirms batch 4/5.

### 3. `0x140334c38` — CRT C-initialiser entry (`__scrt_set_unhandled_exception_filter`
+ `_set_new_mode`), documented by batch 5 agent 1, left unnamed.

### 4. Body/Node base-class vtable slots with no function object (19) — recorded, not created

Range 1 also contains a second missing-slot family that no earlier batch reported:
the **shared base-class slots of the Body/Creature/Node tables**, each referenced by
13–25 different vtables in `0x140352xxx–0x140369xxx`:

```
0x140018b60 (BodyVFTABLE [0])      0x140018fb0 (BodyVFTABLE [33])
0x140019300 (thunk add rcx,0x2a0; jmp — shared by ~15 tables)
0x14001b7f0  0x14001bf60  0x14002e290  0x14002e300
0x140048020  0x140049e10  0x14004a560  0x14004a8b0  0x14004a9f0
0x14004bba0 (BodyVFTABLE [82] — the panel teardown called by Body_OnHoverLeave)
0x14004c7e0  0x14004d8e0  0x14004eaa0  0x140051de0  0x140053110  0x140054dd0
```

They are real code (`mov [rsp+8],rbx …` prologues, `movss` getters) and real vtable
slots, but they sit in the **CRT half** of my assignment, not in the Box2D half, and
each is inherited by many classes at once, so a per-class name would be wrong. They
were **not** created in this pass: they need their own blackboard creation request
and a base-class slot map (`Node`/`Body`/`Creature` virtual index → role). The one
exception I would argue for is `0x14004bba0` (slot +0x298), whose role is now proven
by its single caller (`Body_OnHoverLeave`); proposed name `Body_ClosePartInfoPanel`.
Its whole body is `if (this->field_0x9d0) this->field_0x9d0->vtable[9](&this->field_0x9d0, 0); return;` —
i.e. it releases the panel object at `+0x9d0` through that object's virtual at
`+0x48`, matching the "cached panel link" the hover-enter path creates.

## Skipped and recorded (not renamed)

| addr | size | why |
|---|---|---|
| 0x140017d10 | 36 | Virtual dispatch through a doubly-indirect table (`*(int*)(*(longlong*)*this+4)` + 0x48 + this → `call [*p+0x10]`). **No code xref at all**, only a `.pdata`-space data ref at 0x14807905c, so no caller context; cannot prove the owning class or the virtual's role. |
| 0x14000ad80 | 11 | `return *(int*)(this+0x190) != 0;` — 3-instruction field test. Only caller `Projectile_DetonateOnImpulse` 0x14001d2e1; field `+0x190` is not identified anywhere else, so `Projectile_HasX` would be a guess. |
| 0x140027f90 | 120 | Iterates the 8-byte pointer vector at `+0x350..+0x358` and calls `rep_1402b1a80_MakeGlobal?` on `element+0x58` when non-null. Callers: `memcmp_editor`, `?BuyPartShop` (×2), `rep_140116d70_WriteToClientLog`. The element class and the meaning of "MakeGlobal" are not provable (`rep_` label is untrusted), so no name. |
| 0x1400458c0 | 3342 | Called from `Editor_RebuildGlobalLinkLists` 0x14018c474 as `f(Node*, Link*)`. Walks the editor frame's children (`CODE_FRAME` branch) or `node[2]` list, filters bodies with `(flags+0xb8 >> 9|10)&1` and `Body_IsMountedOrPaired()`, builds a pair list of `{body, body+0x48}`, then uses `sqrtf`, `RbTree_Insert`, `RbTree_InsertLinkByFloatPair`, `Link_ConstructFromBody`, `setXposYPos` and `Frame_ClassifyPartMix(DAT_1403c0d88)`. It is clearly an editor "collect and lay out the selected ship's mounted parts" pass, but the exact product (repair list / layout list / node order) is not pinned down. |
| 0x140049cd0 | 35 | `if (int(this+0x2e8) < arg) return 0; return float(this+0x248) != 0;` — index-bounds + non-zero-float getter. Seven call sites (`creatureLogic`, `mainDialogWithChoices` ×2, `ClickFunc` ×2, 0x1402b9526) but the two fields are unidentified. |
| 0x1403160a0, 0x1403160f0, 0x1403161a0, 0x140316a50, 0x140316d00 | 75–274 | Re-confirmed batch-5 agent 10's five render/descriptor helpers (city/cloud descriptor initialisers stored in the 0x1403770d8 record tables, the zoom-LOD/property updater and the 0x38-stride timer list). Owning structs still unidentified; no name added. |
| 0x140319da0 | 3 | shared empty destructor / `_guard_check_icall` body (batch-5 answer 4). Leave. |
| 0x1403340d8 | 43 | scalar deleting destructor, vtable `0x140378f08` is a name→pointer record table, not a real vtable. Class not provable. |
| 0x14033503c, 0x140335050, 0x140335354, 0x14033536c, 0x140335388, 0x140335394, 0x14033539c | 6–27 | `__scrt_*` outline stubs used only by the `_set_app_type` worker (0x140334b70): `mov eax,1; ret`; zero `DAT_1480771ec`; `mov eax,0x4000; ret` (`_O_TEXT`); set two scrt flag globals; `(DAT_1403c2e68==0)`; return `&DAT_148077208`; return `&DAT_148077200`. No MSVC symbol name is provable for any of them (batch 5 reached the same conclusion). |
| 0x140336730 … 0x140336f50 (13 objects) | 29–65 | `/EH` cleanup funclets — agent 1's role. Untouched. |
| 0x14031f4b0 | 60 | **Newly noticed**: a comparator (`movzx eax,word[rdx+0x38]; cmp ax,[r8+0x38]; … setg al`) reached only from the reflection name→function record table at `0x1403691f8–0x140369218` (strings 0x14037f838 / 0x14037f8b0). It orders a struct by 16-bit field `+0x38` then bitmasks at `+0x34/+0x36`; the owning type is not identified. Not created (no call site, no vtable slot). |

## Open hand-offs for the next pass

1. The **150-entry CRT C-initialiser table** (`0x1403519e8–0x1403521a8`) — the single
   largest remaining `FUN_*` gap in `0x140000000–0x14006FFFF`. Naming scheme and
   evidence recipe are in the section above.
2. `0x14031f4b0` comparator — identify the record type (the `+0x34/+0x36/+0x38`
   bitmask/word layout) and name it; it belongs to the same reflection machinery as
   the 0x1403770xx / 0x1403692xx record tables.
3. `0x1400458c0` / `0x140027f90` / `0x140049cd0` / `0x14000ad80` — cheap to finish
   once the Body/Creature field map (`+0x190`, `+0x248`, `+0x2e8`, `+0x350`,
   `+0x7c8`, `+0x9d0`, `+0x9e0`) is written up; they are getters/collectors over
   already-mapped creature state.
4. Body/Creature vtable: slots 33 (`0x140018fb0`), 34 (`0x140018fa0`) and the
   `+0x298` teardown (`0x14004bba0`) are still unnamed but are now *documented by
   caller* — `0x14004bba0` is the "close the part-info panel" call of
   `Body_OnHoverLeave`. The full 19-address base-slot gap is listed in the
   "Body/Node base-class vtable slots" section; it needs a Node/Body slot index map
   plus one creation request for the whole set (`0x14004bba0` →
   `Body_ClosePartInfoPanel` is the one with proved semantics).
5. The 36 joint slots created here make every Box2D joint table fully materialised.
   A follow-up should only *verify* them: the remaining unnamed targets in
   `0x140300000–0x140336FFF` are then the 13 `/EH` funclets (agent 1), the 7
   `__scrt_*` stubs, `0x1403340d8`, `0x140319da0`, the 5 render helpers, `0x14031f4b0`
   and the `rep_*` population (agent 5).
