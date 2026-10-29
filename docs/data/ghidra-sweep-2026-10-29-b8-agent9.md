# Ghidra sweep 2026-10-29 — batch 8, agent 9 (Body slots + HGE RNG vtable)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the 4 created-but-unnamed Body vtable slots from batch 7 agent 7
(`0x140018fb0`, `0x140053110`, `0x14004c7e0`, `0x14004d8e0`) and the 4 HGE RNG vtable
targets `0x140174350 / 0x140174320 / 0x1401742d0 / 0x140174310`.

Result: **4 created** (HGE RNG, all four also named + plated), **3 renamed + re-plated**
(Body slots), **1 left unnamed** (slot +0x240, plate sharpened), **0 skipped addresses**.

| slot | addr | before | after |
|---|---|---|---|
| Body `+0x108` (33) | `0x140018fb0` | `FUN_140018fb0` (plated) | **`Body_OnClick`** |
| Body `+0x220` (68) | `0x140053110` | `FUN_140053110` (plated) | **`Body_LinkAdjacentParts`** |
| Body `+0x240` (72) | `0x14004c7e0` | `FUN_14004c7e0` (plated) | *unchanged* (plate updated) |
| Body `+0x248` (73) | `0x14004d8e0` | `FUN_14004d8e0` (plated) | **`Body_DrawMeshPolygon`** |
| HGE `+0x100` | `0x140174350` | *no function object* | **`HGE_RandSeed`** |
| HGE `+0x108` | `0x140174320` | *no function object* | **`HGE_RandInt`** |
| HGE `+0x110` | `0x1401742d0` | *no function object* | **`HGE_RandFloat`** |
| HGE `+0x118` | `0x140174310` | *no function object* | **`HGE_RandGetState`** |

Creation followed the protocol: request posted in the batch-8 blackboard
(`## Creation request — agent 9 (batch 8)`, count 4, one cycle before the `create_function`
calls). Addresses are disjoint from every other agent (agent 2's assignment excludes these
four explicitly).

## 1. The Body vtable slot family +0x100 … +0x250 is now a proven map

All 16 Body-derived tables (`0x140352a30` base plus `0x140354c40`, `0x14035e1d0`,
`0x140360670`, `0x140360ed8`, `0x140361238`, `0x1403615c8`, `0x140361990`, `0x140361d08`,
`0x140362098`, `0x140362420`, `0x1403627a0`, `0x140362b00`, `0x140362e60`, `0x1403697f0`,
`0x140369b50`) were dumped at the slots below. The **GUI tables name the slot role**, the
Body tables carry the base implementation:

| slot | Body impl | GUI tables | role |
|---|---|---|---|
| `+0x108` (33) | `0x140018fb0` → **`Body_OnClick`** | `?HandleClick` `0x14012d050` (12 tables), `GuiElement_BeginInputCapture` (2), `Settings_ToggleJoystickType` (1) | **click entry** `(int mouseButton, Node* context)` |
| `+0x110` (34) | `0x140018fa0` (`return false` wrapper) | `AlwaysReturn1` / `FUN_14012cf20` | **begin-input-capture**, false = no capture |
| `+0x218` (67) | `Body_SetLink2A0` | same | assign the `+0x2a0` smart-ref |
| `+0x220` (68) | `0x140053110` → **`Body_LinkAdjacentParts`** | `0x14011cdb0` (broadcast to every child within radii+1.0) | **attach/link the touching free parts of two bodies** |
| `+0x228` (69) | `Body_ScanSectors` | `Creature_BroadcastPartCall228` | sector scan / broadcast |
| `+0x238` (71) | `0x14004bed0` (`handleAmmoInBattle?`) | `Gauge_Draw`, `Slider_Draw`, `Panel_Draw` | **draw** |
| `+0x240` (72) | `0x14004c7e0` (forward to +0x238 with `0.0`) | same forwarder, no override | draw in "default state", argument unproven |
| `+0x248` (73) | `0x14004d8e0` → **`Body_DrawMeshPolygon`** | same | draw the Body's Mesh polygon filled |

The `+0x108`/`+0x110` pair is what makes `Body_OnClick` provable without a `.text` caller:
the two Body slots are exactly the GUI "HandleClick / BeginInputCapture" pair, and the Body
version's own `(this, int mouseButton, Node* context)` signature matches `GUI::_HandleClick`
`(this, int param_2, param_3)` instruction for instruction in its prologue (same `+0x78`
gate style, same `+0x193/+0x194` extended flags family, same `_ClickFunc(param_3, this, mode,
…)` tail). Both are reached only through vtables.

## 2. `Body_OnClick` (0x140018fb0, slot +0x108) — shipworks unmount/detach

`(this, int mouseButton, Node* context) -> bool`; returns 0 only on the global guard
`0x143a11960`. Runs when `+0xb8 == 0` (unowned) **and** `vtable+0x1a8` (`Body_IsStatic`) is
false, or when `IsInEditor`, and only when `+0xa39` is set:

* `+0x9e1` set (this part is the held one) → `rep_14017a2e0_MakeGlobal_(context,1)`, the
  "drop the held part" path (clears the drag link `0x1439e9400`, resets the RbTree,
  `[0x1403c0d40]+0x8d8 = 0x45`).
* else `mouseButton == 1` (left): in the editor, move the part's **fuel** (double `+0x7f8` —
  the field `Creature::add_fuel` fills / `Body_BurnUpdate` drains, capped by `stats+0xc8`)
  into the player creature's **float** counter `PLAYER_ESCADRA[+0x340]+0x274`
  (`ADDSD` then `MOVSS`; `Dialog_ExecuteChoiceActions` credits the same counter), and if
  `checkShipPartFlagActive(this,1)` zero the part's own `+0x7f8`; then `0x140185ff0(context,
  this, false)`.
* else `mouseButton == 2` (right): `0x140185ff0(context, this, true)` — no fuel return, and
  the `true` flag skips the editor child-sprite purge.
* other buttons: no-op, returns 1.

`0x140185ff0` (stale label `rep_14017a420_New`) is the actual **pickup**: `Body_DetachFromOwner
(this)`, frees the subtree's link sprites, plays the `"screwdriver"` radio line + SFX,
rebuilds the editor global link lists, `SetLink(this+0x70, NULL)`, clears the `+0x16` link and
calls `Scene_UpdateHoveredNode`. So the operation is "pick the part up off the ship", not
"delete" and not "sell": the left click additionally returns the fuel the part was holding.

**Corrections to batch-7 agent 7:** the `+0x7f8` value is fuel, not money (confirmed by
`Creature::add_fuel` 0x140060e60 and `Body_BurnUpdate` 0x140054850), and `0x140185ff0` is a
*detach*, not an "insert into the other node" routine.

## 3. `Body_LinkAdjacentParts` (0x140053110, slot +0x220)

`(this, Body* other, bool playSound) -> bool`. Returns 0 if `other` is null or shares
`this+0x78`. For every element of the `+0x350` vector of `this` and of `other` (index
`[6a]`/`[6b]` = `+0x350`/`+0x358`):

* skip nulls, skip `+0x58 != 0` (already mounted), skip `Body_IsMountedOrPaired`
  (`0x1402dd230`);
* require `MOV RAX,[this+0xb8]; TEST [other+0xb8],RAX` — a shared **bit** in `+0xb8`;
* require complementary connector flags `+0x84` / `+0x85` (if `this+0x84` then `other+0x85`,
  and at least one of the pair is set);
* convert both part positions through `vtable+0xe8` (`get_world_pos`) and require
  `distance < 1.0` game unit (`Sqrt_Cache` 0x1403365dc, the same table the snap/repair
  passes use).

On a match `0x1402dca50` (stale label `rep_1402b15a0_MakeGlobal_`) links the two parts:
`SetLink(pair+0x50, other+0x70)` both ways and `[pair+0x80] = (u32)(a+0xb8 & b+0xb8)`.
When `playSound` is set it also runs `0x1400bc740` (5.6 KB editor placement/refresh pass,
stale rep label). Finally `0x14004bbc0` runs on **both** bodies: it deletes every element of
the `+0x8c0` vector whose `+0x13c` is set (`child->vtable[0](child,1)`), nulls the slot and
compacts the vector — i.e. it purges both bodies' cached sprite/child records.

**Correction to batch-7 agent 7:** the tail call is `0x14004bbc0`, not `0x140049800`
(`setCertainBodyFloatVals`, which the decompiler had resolved for both). So the function does
*not* re-initialise either body; the two `+0x8c0` passes are exactly what a re-link needs
(the cached child sprites of the affected pairs are stale).

The root-class override of the same slot (`0x14011cdb0` in table `0x140360670`) loops the
`+0x100` child list and calls `child->slot220(param_2, param_3)` for every child within
`radii + 1.0`, and `Frame_CopyConstructor` calls slot `+0x220` once per child node
(`0x14011bcc3`, `R8D = 0`), so `+0x220` is the recursive "attach these parts to the given
body" entry. That fits the only other `.text` call site family (the vtables) and the name.

## 4. `Body_DrawMeshPolygon` (0x14004d8e0, slot +0x248) — the HGE 3-vertex primitive

`(this, vec2* pos, vec2* rot, float angle, float alpha, uint rgbOverride)`. Bails unless
`this+0x1b8` (the `Mesh`/PhysicsFixture) exists and has ≥ 3 vertices (`mesh+0x50`). Copies
`mesh+0x48` to the scratch buffer `0x1403edfd0`, scales by `angle`, rotates through
`vec_rotate` (0x1402e5130) with `rot`, adds `pos`, builds the triangle fan in `0x1403ed800`
(clamped to 500 vertices) and emits one triangle per ear through **`HGE->vtable+0x2d0`**.
Colour = RGB from `this+0x8f0` (or `rgbOverride`), alpha = `(rgb>>0x18)/255 * alphaArg`
clamped to 0..1.

`HGE+0x2d0` is now identified: **`0x14016cd00` → `0x140085f80`**, the 3-vertex primitive
submit through device `+0x48` with the blend index at descriptor `+0x110`. Its siblings are
`+0x2d8` = `0x14016ccf0` → `0x140085fc0` (device `+0x50`, blend at `+0x20`) and `+0x2e0` =
`Gfx_RenderQuad` `0x14016cc80` → `0x140085f40` (device `+0x40`, blend at `+0x168`). The
descriptor is 0xb8 bytes with three vertices at `+0x00 / +0x58 / +0xb0`, which is why the
guard reads the count from the Mesh and the quad/draw-stats code reads `+0xb0/+0xb4`.

Only `.text` caller: the Body draw `+0x238` (`0x14004bed0`) at `0x14004c484`, with
`pos = &Body+0x95c`, `rot = &Body+0x970`, `angle = ZOOM_LEVEL` (1.0 when `+0x91d` is clear),
`alpha = Body+0x98c`, `rgb = 0`, gated on `Body+0x8ec`. `VideoTask_RenderMapScene` and
`VideoTask_RenderMenuScene` hit the same slot on their own body.

## 5. Left unnamed: `FUN_14004c7e0` (slot +0x240)

`JMP [[this]+0x238](this, 0.0f)` — two instructions, identical in all 16 tables, nothing
overrides it. `Gui_BootTitlePass` calls it with no explicit argument (`0x1402a3177`,
`0x1402a3394`) right after writing `Body+0xa8c` (the title-screen ship colour) and before its
`+0x2c8` / `+0x98c` passes. The `+0x238` target declares **no** float parameter and never
reads XMM1, so the fixed `0.0` (alpha / animation time / a base-signature placeholder) is not
verifiable. A name would only restate "call Draw with 0", so it stays unnamed; the plate now
carries the slot map and this reasoning.

## 6. HGE RNG — four created, named, plated

All four had no function object (`getFunctionAt` and `getFunctionContaining` both null) and
were only reachable through the HGE vtable `0x1403672f0` (COL `0x14037f068`, slot 0 = `Release`).
`create_function` sizes: 0x24, 0x30, 0x35, 0x7. Decompiled bodies (as created):

```
void  HGE_RandSeed(HGE, int seed)
    if (seed == 0) DAT_1439e8688 = timeGetTime();       // decompiler resolved the IAT call
    else           DAT_1439e8688 = seed;

int   HGE_RandInt(HGE, int min, int max)
    DAT_1439e8688 = DAT_1439e8688 * 0x343fd + 0x269ec3;
    return min + (DAT_1439e8688 >> 0xf ^ DAT_1439e8688) % ((max - min) + 1U);

float HGE_RandFloat(HGE, float min, float max)
    DAT_1439e8688 = DAT_1439e8688 * 0x343fd + 0x269ec3;
    return (float)(DAT_1439e8688 >> 0x10) * 1.5259022e-05 * (max - min) + min;

uint  HGE_RandGetState(void)  { return DAT_1439e8688; }
```

Names follow the family already used by `engine-hge.md` (`Sound_Load`, `Texture_Load`,
`Input_GetEvent`) and stay distinct so the collision rule never sees a token subset
(`HGE_RandSeed` ⊄ `HGE_RandGetState` because of `Seed`).

`Location_SeedRandoms` (`0x140110340`) is the caller that proves the pairing: it reads a
value with `+0x108` `Random_Int(0,999)`, seeds with `+0x100`, draws twice with `+0x110`
`Random_Float(200,800)` / `(0,1)` and restores with `+0x100`. The `+0x118` getter returns the
**state**, not the original seed (it is advanced by every draw), hence `GetState`.

Naming-convention warnings at creation were stylistic only (`RandInt` 7 chars, "not a
recognised verb"); the names were accepted and no rename was needed.

## 7. Structure facts for `docs/structures.md` (agent 10)

* **HGE vtable `+0x2d0` = 3-vertex primitive submit** (`0x14016cd00` → `0x140085f80`,
  device `+0x48`, blend at descriptor `+0x110`); `+0x2d8` = `0x14016ccf0` → `0x140085fc0`
  (device `+0x50`, blend `+0x20`); `+0x2e0` = `Gfx_RenderQuad` (device `+0x40`, blend
  `+0x168`). The 0xb8-byte descriptor holds 3 vertices at `+0x00/+0x58/+0xb0`.
* **HGE RNG `+0x108` range is inclusive**: `min + (mix % (max-min+1))` — the existing
  structures.md line says `[min, max)`, which is wrong for the int variant.
* **Body draw family**: `+0x238` = draw (GUI tables put `Gauge_Draw`/`Slider_Draw`/
  `Panel_Draw` there), `+0x240` = draw with a fixed `0.0` arg, `+0x248` = filled mesh-polygon
  draw. Per-frame draw inputs: `+0x95c` screen position, `+0x970` rotation, `+0x98c` alpha,
  `+0x8ec` "draw polygon" gate, `+0x8f0` packed colour (ARGB).
* **`Body+0x1b8` = `Mesh`** (created by `setCertainBodyFloatVals` via `Mesh(New(0x58))`):
  `Mesh+0x48` = vertex array, `Mesh+0x50` = vertex count.
* **`Body+0x350`/`+0x358`** = child/part vector (begin/end), walked in slot +0x220.
* **`Body+0x8c0`/`+0x8c8`/`+0x8d0`** = cached child sprite vector; `0x14004bbc0` kills every
  element with `+0x13c != 0` through `vtable[0](1)` then compacts. `+0x13c` = stale flag.
* **`Body+0x84` / `+0x85`** = connector flags used when linking two parts (complementary
  pairs), and `+0x80` receives `(u32)(a+0xb8 & b+0xb8)` after a successful link.
* **`Body+0xb8` is ANDed, not compared**: `MOV RAX,[a+0xb8]; TEST [b+0xb8],RAX` and the
  `u32` AND stored at `+0x80`. `0xb8 == 0` means "unowned" in `Body_OnClick`. structures.md
  calls `+0xb8` the owner pointer; in the part code it behaves as a bit-set, so the pointer
  reading is at least incomplete — worth a targeted check.
* **`Body+0x7f8` = fuel** (double), confirms batch 7 agent 8's fuel note; `+0x274` on the
  player creature (`PLAYER_ESCADRA+0x340`) is a **float** counter credited by both
  `Body_OnClick` and `Dialog_ExecuteChoiceActions`.

## 8. Tool / bookkeeping notes

* No `save_program`, no tags, no README/STATUS edits, no commit.
* `get_function_callers` returns `null` for functions with no `.text` callers (message
  "No callers found for function: null"); `get_xrefs_to` is the working xref source.
* `search_instructions` with `operand_pattern: "0x248"` was the fastest way to enumerate
  indirect slot call sites; it found `0x14004c484` (the draw → polygon call) and the two
  `VideoTask_*` callers.
