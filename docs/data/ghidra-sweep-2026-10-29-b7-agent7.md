# Ghidra sweep 2026-10-29 — batch 7, agent 7 (Body/Node base-class vtable slots)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the 19 Body/Node base-slot addresses from the "Left for a later pass"
item 5 of [ghidra-changes-2026-10-29.md](ghidra-changes-2026-10-29.md), all in
`0x140018b60–0x140054dd0`.

Result: **19 created** (all 19 slot addresses now have a function object),
**15 named + plated**, **4 created-but-unnamed (plated, behaviour recorded)**,
**0 renamed** (there was nothing to rename), **0 skipped addresses**.

## 1. The slot map is the Body vtable `0x140352a30`

`0x140352a30` holds **88** qword slots and is followed immediately by string
data (slot 88 = `ESSENTIALS\:DATA\...`), so the table is exactly 0x2c0 bytes.
The qword before slot 0 (`0x140352a28`) is `0x140379a98`, a pointer into
`.rdata`; the RTTI type names are stripped in this build (no `.?AV` string
anywhere in `0x140351000–0x1403bc000`), so class identity comes from the code:
slot 0 calls `Body_Destructor` (`0x1400174d0`) and frees 0xa40 bytes, the Body
instance size. **There is no second Node table to build**: all 19 addresses are
slots of this one table, and the same address sits at the same index in 15
other `.rdata` tables, so every one of them is an inherited base virtual:

```
0x140352a30  (88 slots) - the base Body table
0x140354c40  (88)       - Creature      (slot 21 CreatureUpdate, 75 Creature_DebugDrawOverlay)
0x14035e1d0  (88)       - MapShipBody   (slot 0 named MapShipBody_ScalarDeletingDtor)
0x140360670  (89)       - Node/GUI element (extra slot 88, Node_BroadcastCall2A0 family)
0x140360ed8, 0x140361238, 0x1403615c8, 0x140361990, 0x140361d08, 0x140362098,
0x140362420, 0x1403627a0, 0x140362b00, 0x140362e60, 0x1403697f0, 0x140369b50
```

That resolves the open question left in `structures.md` ("which slot is declared
on Node vs Body"): the whole 88-slot set is one class, `Body`, whose first ~20
methods are the tree/serialisation layer (`Serialize`, `Deserialize`, `Add`,
`remove`, `relink`, `Load`, `Reflect`). Naming below follows that: tree
traversal helpers get `Node_`, physics/render/parts get `Body_`.

### Slot table (all 88 slots, name of the current function object at each)

| slot | target | name (after this pass) |
|---|---|---|
| 0 | 0x140018b60 | **Body_ScalarDeletingDtor** |
| 1 | 0x140280c50 | `LAB_140280c50` |
| 2 | 0x140190820 | `Serialize` |
| 3 | 0x14018fa40 | `Deserialize` |
| 4 | 0x14004f010 | `SerializeHeader` |
| 5 | 0x140025240 | `bodySecondaryInit` |
| 6 | 0x14004a1c0 | `calc_angle_cache` |
| 7 | 0x140005e70 | `_guard_check_icall` |
| 8 | 0x1402805e0 | `KillAndQueueDead` |
| 9 | 0x140049ea0 | `Body_Kill` |
| 10 | 0x140019ab0 | `Add` |
| 11 | 0x14027fb00 | `List_ActivateIndex` |
| 12 | 0x14004ba00 | `remove` |
| 13 | 0x140281080 | `LAB_140281080` |
| 14 | 0x140005e50 | stub |
| 15 | 0x140005e60 | `Node_IsStateActive` |
| 16 | 0x14004b880 | `relink` |
| 17 | 0x14004a040 | `Load` |
| 18 | 0x14004b010 | `Reflect` |
| 19 | 0x140024f70 | `Body_DestroyPhysics` |
| 20 | 0x140054d90 | `BodyNode_ApplyToChildrenIfReady` |
| 21 | 0x140054b20 | `Part_UpdateDispatch` |
| 22 | 0x14002d7b0 | stale `rep_*` |
| 23 | 0x1402802b0 | stale `rep_*` |
| 24 | 0x14002e300 | **Node_FindAllByOid** |
| 25 | 0x14002e290 | **Node_FindByOid** |
| 26 | 0x1402801c0 | stale `rep_*` |
| 27 | 0x14002e1e0 | `CollectObjectsByMask` |
| 28 | 0x140055ab0 | `Body_AddWorldAngle` |
| 29 | 0x140055af0 | `get_world_pos` |
| 30 | 0x14004a0b0 | `Body_LocalAngleToWorld` |
| 31 | 0x14004a100 | `Body_LocalPointToWorld` |
| 32 | 0x1400055c0 | `return false` stub |
| 33 | 0x140018fb0 | **created, unnamed** (slot 33) |
| 34 | 0x140018fa0 | wrapper |
| 35 | 0x1400055c0 | `return false` stub |
| 36 | 0x140019310 | `Body_OnHoverEnter` |
| 37 | 0x140019380 | `Body_OnHoverLeave` |
| 38 | 0x1400192b0 | `Creature_EnableBody` |
| 39 | 0x1400190d0 | stale `rep_*` |
| 40 | 0x140019250 | `Creature_DisableBody` |
| 41 | 0x1400055d0 | `return true` stub |
| 42 | 0x140045660 | `Body_CollectSelfLinkIfDropped` |
| 43 | 0x140005e20 | `Node_CopyEscadraName` |
| 44 | 0x140054bf0 | `Body_SyncFromB2` |
| 45 | 0x14001d440 | `Body_PreStepUpdate` |
| 46 | 0x14001b2c0 | `Body_AddForceAtPoint` |
| 47 | 0x14001b5d0 | `Body_AddForceAtCenter` |
| 48 | 0x14001bf60 | **Body_AddTorqueForce** |
| 49 | 0x14001b7f0 | **Body_AddImpulseAtPoint** |
| 50 | 0x14001baf0 | stale `rep_*` |
| 51 | 0x14001c0d0 | `Body_ApplyAcceleration` |
| 52 | 0x140019be0 | `Body_AddTorque` |
| 53 | 0x140049e10 | **Body_IsStatic** |
| 54 | 0x14004a560 | **Body_FindNearestPartInRange** |
| 55 | 0x14004a2f0 | stale `rep_*` |
| 56 | 0x14004a9f0 | **Body_IntersectsRect** |
| 57 | 0x14004a8b0 | **Body_TestPoint** |
| 58 | 0x140048020 | **Body_GetZ** |
| 59 | 0x140049c30 | stale `rep_*` |
| 60 | 0x140054fb0 | `Part_Tick` |
| 61 | 0x140033b90 | `creatureLogic` |
| 62 | 0x140055870 | `Body_ThermalStep` |
| 63 | 0x140054720 | `Body_ComputeMeshBounds` |
| 64 | 0x140023ac0 | `Body_DieExplode` |
| 65 | 0x140051de0 | **Body_StoreHealthClamped** |
| 66 | 0x1400519d0 | `Body_ApplyDamage` |
| 67 | 0x140019300 | **Body_SetLink2A0** |
| 68 | 0x140053110 | **created, unnamed** (slot 68) |
| 69 | 0x140052340 | `Body_ScanSectors` |
| 70 | 0x140027bd0 | stale `rep_*` |
| 71 | 0x14004bed0 | `handleAmmoInBattle?` |
| 72 | 0x14004c7e0 | **created, unnamed** (slot 72) |
| 73 | 0x14004d8e0 | **created, unnamed** (slot 73) |
| 74 | 0x14004e220 | stale `rep_*` |
| 75 | 0x14004c7f0 | `Creature_DebugDrawDetails` |
| 76 | 0x14004e0d0 | `Hud_DrawSlotPinsForChildren` |
| 77 | 0x14004dfa0 | `Creature_DrawLinkSprites` |
| 78 | 0x140054dd0 | **Body_UpdateEffectTimers** |
| 79 | 0x1400465d0 | `Frame_FindSnapCandidates` |
| 80 | 0x1400211a0 | `Body_BuildPartStatsText` |
| 81 | 0x140023580 | stale `rep_*` |
| 82 | 0x14001dd40 | `Body_BuildPartInfoPanel` |
| 83 | 0x14004bba0 | **Body_ClosePartInfoPanel** |
| 84 | 0x14002de30 | stale `rep_*` |
| 85 | 0x140054380 | stale `rep_*` |
| 86 | 0x140018fa0 | wrapper |
| 87 | 0x14004eaa0 | **Body_RestoreStage** |

## 2. Evidence per created slot

All 19 are `__thiscall`, `RCX` = Body (0xa40 bytes). Sizes below are the gap to
the next existing function entry; each body ends in `RET`/`INT3` inside it.

### 0x140018b60 — `Body_ScalarDeletingDtor` (slot 0, 0x40 bytes)
`MOV RDI,RCX; CALL 0x1400174d0 (Body_Destructor); TEST BL,1; if set: free(this,
0xa40); return this`. The canonical MSVC scalar deleting destructor; the size
0xa40 is the Body instance size (matches the `New(0xa40)` sites). Confirmed by
the same convention already in the DB: `MapShipBody_ScalarDeletingDtor`
(0x1400e8140) at slot 0 of 0x14035e1d0.

### 0x14002e290 — `Node_FindByOid` (slot 25, 0x110 bytes)
`strlen(RDX)`; compare against the `std::string` at `this+0x190` (m_oid: SSO
capacity test `[this+0x1a8] >= 0x10`, size `[this+0x1a0]`, `memcmp`); on a match
return `this`, else tail-jump to `0x140280370` with `(this, name)` =
recursive descent. Returns the first matching node.

### 0x14002e300 — `Node_FindAllByOid` (slot 24, 0xa0 bytes)
Same prefix as slot 25, but on a match it pushes `this` into the vector `R8`
(then `rep_140005e10` = `memmove` for the regrow) and always ends in
`Node_ChildCallC0` (slot +0xc0, i.e. this same virtual on every child) — i.e. it
collects every node in the subtree whose `m_oid` equals the argument.

### 0x14001bf60 — `Body_AddTorqueForce` (slot 48, 0x170 bytes)
Single float argument in XMM1. Adds it to the game-side accumulator `this+0x164`
and adds `arg * 0.05^5` to the Box2D torque accumulator `b2Body+0x54`
(`0x1403c0e10` = 0.05 multiplied five times, the same scale as
`Body_AddForceAtPoint` uses for force/`0.05^4`). It does **not** touch angular
velocity — contrast `Body_AddTorque` (slot 52), which adds
`torque*0.05^5*invI` straight to `b2Body+0x48`. So it is the force/accumulator
variant of torque, not the impulse `Body_AddTorque`.

### 0x14001b7f0 — `Body_AddImpulseAtPoint` (slot 49, 0x300 bytes)
Args: `RDX` = force vec2, `R8` = body-local point vec2. Bails when
`vtable+0x1a8` (`Body_IsStatic`, slot 53) is set; resolves the b2Body (`+0x178`, else
`+0x88+0x178`); converts the local point through `vtable+0xe8`
(`get_world_pos`); then adds to `b2Body+0x40/+0x44` (**linear velocity**,
`m_linearVelocity`) and `+0x48` (**angular velocity**) — the impulse form.
`Body_AddForceAtPoint` (slot 46) is the mirror image: it writes the same
geometry into `b2Body+0x4c/+0x50` (m_force) and `+0x54` (m_torque) plus the
game accumulators `+0x15c/+0x160`. Same 0.05^4 scale, velocity vs accumulator.

### 0x140049e10 — `Body_IsStatic` (slot 53, 0x20 bytes)
`return this+0x1d0 (m_density) == 0.0f` (NaN returns false). `Body_CreateB2Body`
makes the b2 body type 2 (dynamic) iff `+0x1d0 > 0`, else static — so this is
exactly the "is this body static" predicate. It is the `vtable+0x1a8` guard
every physics entry uses (`Body_AddForceAtPoint` / `AtCenter` / `AddTorque` /
`AddImpulseAtPoint`, `Projectile_DetonateOnImpulse`,
`Physics_ProcessContactRecord`, ...): a static part (terrain, `m_density 0`)
skips forces, impulses and contact damage.

### 0x14004a560 — `Body_FindNearestPartInRange` (slot 54, 0x7e0 bytes)
`(this, u8 mask, u8 layerFlag) -> Body*`. Walks the world array
`0x143a33c90`/count `0x143a51150`, skips itself and its master (`+0x88`),
requires `vtable+0x78` true, owner (`+0xb8`) compatibility, then distance <=
`this+0x20c + other+0x20c` (radii), optional `+0x1f0` layer-mask overlap, the
`+0x7b0` flags and finally `this->vtable[+0x1b8](other)` as an accept test.
Returns the first accepted body or 0. Its result is stored in the smart-ref
`this+0x9e8` by `rep_1400191c0` (`CALL [RAX+0x1b0]` then `SetLink`), i.e. it
picks the part to attach to. The GUI-table override at slot 54 is already named
`Creature_FindPartResult1B0`, which matches ("part finder whose result belongs
to slot +0x1b0").

### 0x14004a9f0 — `Body_IntersectsRect` (slot 56, 0x350 bytes)
`(this, vec2* a, vec2* b) -> bool`. Converts every vertex of the body's polygon
(`[b2body+0x48]` array, count `[+0x50]`) through `vtable+0xe8` and tests it
against the axis-aligned box spanned by `a` and `b`; if no vertex is inside, it
tests the four box corners with `b2Shape::TestPoint`. Returns 1 on overlap. The
GUI-table override at slot 56 is `Creature_AnyPartMatches1C0`.

### 0x14004a8b0 — `Body_TestPoint` (slot 57, 0x490 bytes)
`(this, vec2* p) -> bool`: `p * 0.05` (game units -> b2 units) then
`shape->vtable[+0x18](shape, transform, &point)` = `b2Shape::TestPoint`, using
`this+0x168` (b2Fixture, shape at `+0x18`, transform at `+0x10`). Returns
`true` when the point is inside the part. Both arguments are null-checked
before use.

### 0x140048020 — `Body_GetZ` (slot 58, 0x10 bytes)
`return *(float*)(this+0x90c)`. `+0x90c` is documented as `m_z` in
[structures.md](../structures.md) and is used as the z/height everywhere
(`Creature_WorldToScreen`, `Body_UpdateRenderTransform`, `Trail_*`,
`Map_RenderSkyLayers`, ...). The only table that overrides it is
`0x140360670` (0x1400f5200), which also just reads `+0x90c`.

### 0x140051de0 — `Body_StoreHealthClamped` (slot 65, 0x40 bytes)
The virtual "set health" slot (documented in
[weapons-index.md](../findings/weapons-index.md) and
[combat-hit-hook-sites.md](../findings/combat-hit-hook-sites.md) as
`vtable+0x208`): return if `+0x2d0` (invulnerability) is set; return if the old
`+0x2c8` and the new value are both <= 0; store `min(this+0x2cc, XMM1)` at
`+0x2c8`; when the stored value is 0, tail-jump to `vtable+0x200`
(`Body_DieExplode`). **Name note:** `Body_SetHealth` already exists at
0x140049c10 (a 17-byte helper that stores the same value into `+0x2c8` and
`+0x2cc`); the name-collision rule also rejects `Body_SetHealthClamped`, because
its token set contains `Body_SetHealth`'s. Hence `Body_StoreHealthClamped`.

### 0x140019300 — `Body_SetLink2A0` (slot 67, 0x10 bytes)
`ADD RCX,0x2a0; JMP 0x140194de0` = assign the smart-ref (`Link`) at
`Body+0x2a0`. The field is constructed in `Body_Constructor`/`createNewBody`,
destroyed in `Body_Destructor` and re-armed by `setCertainBodyFloatVals`; the
target class is not identified, so the name is field-based (same convention as
the existing `Node_BroadcastCall2A0` / `Object_GetSubObject2A0`).

### 0x140054dd0 — `Body_UpdateEffectTimers` (slot 78, 0x1e0 bytes)
Called from `Part_Tick` only (0x14005567c). Ages the intrusive list at
`this+0x998` (nodes are 0x18 bytes, float lifetime at `+0x10`, frame time from
`0x1403c1268`), unlinks and frees the nodes whose timer exceeds 2.0 s
(`0x1403527e8`), then decrements the `+0x9ac` timer and re-arms the `+0x9a8`
cooldown from `HGE->vtable[+0x110]` (random 0..1) to 0.15/0.2/0.3 s, and resets
`+0x990` to -1.0. The `+0x998` list is drawn by `Creature_DrawLinkSprites`
(0x14004dfac) and destroyed in `Body_Destructor`; `+0x990`/`+0x9a8`/`+0x9ac`
are the effect/sound-slot bookkeeping set by `0x140048ba0`'s body. Hence
"effect timers", not a game-specific name.

### 0x14004bba0 — `Body_ClosePartInfoPanel` (slot 83, 0x10 bytes)
`if (!this->field_0x9d0) return; [[0x9d0]+0x48](0x9d0, 0)`. `+0x9d0` is the
panel object created/cached by `Body_BuildPartStatsText` (slot 80) — the
hover-enter path (`Body_OnHoverEnter`, slot 36) calls slot 80 and sets `+0x9e0`;
the hover-leave path calls this slot and clears `+0x9e0`; `Body_Kill` (slot 9)
calls it before teardown (`0x140049ec3..0x140049ed3`). The forwarded virtual is
the object's own `+0x48` slot, which for the GUI element class is the
kill/remove entry. **Verified**: the body is a kill-forwarder to the cached
panel, and closing the part-info panel is what both callers do with it. The old
label "projectile cleanup" (+0x298, batch 6) is disproved. Agent10's
structures.md note that the name "is not supported" is too strong - see
`body` above.

### 0x14004eaa0 — `Body_RestoreStage` (slot 87, 0x10 bytes)
`this+0x8d8 (m_stage) = this+0x8dc`. `+0x8dc` is the backup copy of `m_stage`:
`Creature_DisableBody` saves `+0x8d8` into `+0x8dc` then zeroes `+0x8d8`;
`Creature_EnableBody` restores `+0x8d8 = +0x8dc`; `Add`/`remove` adjust the pair
together. Only caller of slot 87 is `memcmp_editor` (0x1400bc092), i.e. the
editor restores the render stage of the node it re-attaches.

## 3. Created but left unnamed (4)

| slot | addr | size | verified behaviour | why no name |
|---|---|---|---|---|
| 33 | 0x140018fb0 | 0x120 | `(this, int mode, Node* other) -> bool`. Bails on global `0x143a11960`; only proceeds when `this+0xb8` (owner) is null and `vtable+0x1a8` (`Body_IsStatic`) is false, or when the editor flag `0x1403ef368` is set; requires `+0xa39`; if `+0x9e1` set calls `0x140185e60(other,1)` (editor: clear the other node's selection/hover, frees its RbTree link nodes and sets `[0x1403c0d40]+0x8d8=0x45`); mode 2 calls `0x140185ff0(other, this, 1)`; mode 1 refunds fuel (`this+0x7f8` double) into `PLAYER_ESCADRA+0x340+0x274` when the editor is open, zeroes the fuel when `checkShipPartFlagActive(this,1)`, then calls `0x140185ff0` (which links `this` into `other`'s structures, `SetLink`s and plays a sound) | the operation is clearly "move this part out of one node and into another", but which of detach/unmount/sell/transfer it is (and what `mode` 1 vs 2 means) is not provable from one body. It has **no direct caller** in .text - only the 16 vtables reach it |
| 68 | 0x140053110 | 0x2e0 | `(this, Body* other, bool playSound) -> bool`. Requires a different `+0x78` id, then for every pair of children of `this` and `other` (both `+0x350` vectors): skips nulls, skips `+0x58 != 0`, skips when `Body_IsMountedOrPaired` (0x1402dd230) is true, requires a common `+0xb8` bit, matches the `+0x84/+0x85` flags, and requires `distance < 0x1403524d8` (the same radius constant the snap/repair passes use); on a hit calls `0x1402dca50` (links `pair+0x50` to the other's `+0x70`, `SetLink`) and, when the flag is set, `0x1400bc740` (the 5 KB editor sound/placement pass); finally runs `0x14004bbc0` on **both** bodies - the routine that deletes every child of `+0x8c0` through its vtable[0] - and returns 1 | "weld/merge two bodies' matching nearby parts, then drop both sprite caches" is the mechanics, but whether the game means repair, weld or dock is not provable. Note the two `+0x8c0` passes destroy sprite objects **of both bodies**, which a "merge" would not normally do - flagging it rather than guessing |
| 72 | 0x14004c7e0 | 0x10 | `JMP [[this]+0x238](this, 0.0f)` - forwards to slot 71 (`handleAmmoInBattle?` 0x14004bed0) with the float argument 0. Same 2 instructions in all 16 tables (nothing overrides it). | the callee's role itself is unresolved (it is one of the stale-named `handleAmmoInBattle?` functions), so a name here would only restate "slot 71 with zero" |
| 73 | 0x14004d8e0 | 0x470 | `(this, vec2* pos, vec2* dir, float angle XMM3, float alpha stack, int flag)`. Bails unless `b2body+0x50 >= 3` (a polygon with at least 3 vertices); builds the projection of the body polygon from `[b2body+0x48]`, rotating each vertex by the angle (`vec_rotate` 0x1402e5130) and adding `pos`; writes a vertex buffer at `0x1403edfd0` and an index fan at `0x1403ed800` (static scratch, also used by `0x1403ed820`'s vertex layout), builds the colour dword from `this+0x8f0` (RGB in the low 24 bits, alpha = the high byte scaled by the `alpha` argument), then calls `HGE->vtable[+0x2d0]` with the vertex list and count for each ear of the fan | it is a coloured convex-polygon draw/upload, but the exact HGE virtual (`+0x2d0`) is not identified as a known draw entry, so "Body_DrawHullPolygon" would be an inference from the call shape rather than a proof |

## 4. What this pass proves beyond the 19 names

* The `Body` vtable is a single 88-slot table; the base class has **no** own
  Node table (answers the open point in `structures.md` §"Body vtable slot map").
* The physical "force" family is slots 46/47/48 (accumulators: `b2Body`
  `+0x4c/+0x50/+0x54`, game `+0x15c/+0x160/+0x164`) and the "impulse" family is
  49/52 (straight into `+0x40/+0x44/+0x48`). This corrects the earlier
  assumption that there was no impulse-at-point entry.
* `+0x8dc` is a *saved* `m_stage` (+0x8d8), maintained by
  `Creature_DisableBody`/`EnableBody`, `Add`/`remove` and the editor.
* `+0x998` is a 0x18-byte-node, 2.0 s effect/link-sprite timer list destroyed in
  `Body_Destructor` and drawn by `Creature_DrawLinkSprites`.
* `+0x9d0` is the cached part-info panel object; `+0x9e8` is the smart-ref that
  receives the "part to attach to" found by slot 54.

## 5. Creation / naming summary

* **created**: 19 `create_function` calls (`SourceType.USER_DEFINED`), exact byte
  ranges; four of them end in a tail `JMP` (`0x14002e300` -> `0x1402803e0`,
  `0x14002e290` -> `0x140280370`, `0x140019300` -> `0x140194de0`,
  `0x14004c7e0` -> `[rax+0x238]`) rather than `RET`, so the range is closed at
  the jump instruction, not at the next function.
* **named + plated**: 15
* **created, left unnamed (plated)**: 4 (`FUN_140018fb0`, `FUN_140053110`,
  `FUN_14004c7e0`, `FUN_14004d8e0`)
* **renamed**: 0 (no address had a wrong name; `0x14004bba0` had no name at all)
* **skipped**: 0

Final function objects (addresses verified after creation, no overlap with the
neighbouring functions):

```
Body_ScalarDeletingDtor        0x140018b60-0x140018b93
Node_FindAllByOid              0x14002e300-0x14002e394
Node_FindByOid                 0x14002e290-0x14002e2fb
Body_AddTorqueForce            0x14001bf60-0x14001c0ca
Body_AddImpulseAtPoint         0x14001b7f0-0x14001baea
Body_IsStatic                  0x140049e10-0x140049e27
Body_FindNearestPartInRange    0x14004a560-0x14004a806
Body_IntersectsRect            0x14004a9f0-0x14004ad30
Body_TestPoint                 0x14004a8b0-0x14004a9ed
Body_GetZ                      0x140048020-0x140048028
Body_StoreHealthClamped        0x140051de0-0x140051e1d
Body_SetLink2A0                0x140019300-0x140019307
Body_UpdateEffectTimers        0x140054dd0-0x140054f94
Body_ClosePartInfoPanel        0x14004bba0-0x14004bbb3
Body_RestoreStage              0x14004eaa0-0x14004eaac
FUN_140018fb0                  0x140018fb0-0x1400190c8   (slot 33, plated)
FUN_140053110                  0x140053110-0x1400533e9   (slot 68, plated)
FUN_14004c7e0                  0x14004c7e0-0x14004c7eb   (slot 72, plated)
FUN_14004d8e0                  0x14004d8e0-0x14004dd4b   (slot 73, plated)
```

Spot checks after creation: the decompiler now produces `Body_AddImpulseAtPoint`
(0.05^4 scaling, writes `b2Body+0x40/+0x44` and `+0x48`), `Body_AddTorqueForce`
(`+0x164` and `b2Body+0x54`), `Node_FindByOid` (`strlen` + `std::string`
compare at `+0x190`, then `Node::RecursiveSearchChildren`), `Body_IsStatic`
(`+0x1d0 == 0`), `Body_StoreHealthClamped` (clamp to `+0x2cc`, `vtable+0x200`
when zero) and `Body_TestPoint` (`b2Shape::TestPoint` with the point scaled by
0.05). No `save_program`, no tags, no README/STATUS edits, no commits.
