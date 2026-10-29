# Ghidra sweep 2026-10-29 — batch 7, agent 8 (real `FUN_*` A)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: `FUN_*` in `0x140070000–0x1401AFFFF` that are **not** in
`funclet-ownership-2026-10-29.tsv`. No `rep_*` and no funclets were touched.

Start: **54 `FUN_*`** in scope (the `unnamed-2026-10-29.tsv` list matches the live
program exactly). End: **41 `FUN_*`**.
**14 renamed + plated**, **0 created** (one creation request posted for four HGE RNG
vtable targets, see the blackboard), **41 skipped**.

Range context: batch 5 agents 6/7/8 had already been through this window; their
skip table is still accurate for most of what is left. What this pass added is the
**repair-queue / gun-light / Joint-length / GUI-input-link** identifications and the
D3DEngine vertex-submit trio.

## Renames

| addr | new name | why it is provable |
|---|---|---|
| 0x140078930 | `Creature_RebuildRepairQueue` | CalculateStats, then rebuilds the `+0x1558` list from parts with repair state `+0x888 != 0`, sorted by `+0x88c` (SortInsertionByInt88C), assigning the running queue index. `+0x1558` is exactly the list the ship panel shows as the property **`listRepairQueue`** (string `0x140355a20`, `showShipData?` 0x140077705 sets property type 0xe with data `&creature+0x1558`); `+0x888` is the repair state — `Body_BuildPartInfoPanel` compares it to 1/2 and formats `GAME_DMG_REPAIR1` (`0x1403543e8`). |
| 0x140079ed0 | `Creature_SetOuterGunLight` | Caches an aim triple at `+0xd18/+0xd1c/+0xd20`, clears `+0x92c` on every part of the `+0x13a8` gun-group-0 list, then writes the light record of the min-x and max-x part (`+0x92c` intensity, `+0x938`/`+0x93c`/`+0x940` offset vector) and rebuilds the `+0xd28` Link pair. `+0x92c..+0x940` is the per-part light block consumed by `handleLightShifts?` 0x1401b2320 into the 30×20 screen light grid `0x143a15b00` (stride 0x2c). |
| 0x140083450 | `D3DEngine_DrawVertices2` | Two 8-byte vertices taken from `arg+0x58` of two objects, size from vtable +0x10/+8, forwarded to the engine submit 0x1400830f0 with count 2. |
| 0x1400834e0 | `D3DEngine_DrawVertices1` | One vertex from `src+0x58`, optional target resize (`target vtable+0x88`), submitted with count 1; called by Gfx_DrawOverlaySprite, Map_RenderSkyLayers, Hud_DrawZoomGrid, Hud_DrawNoiseFrame, DrawBattleShipPanel, Camera_ZoomByXPreset, SomethingVideoTask. |
| 0x1400835a0 | `D3DEngine_DrawVertices1ToTarget` | Same as above but target = `*(this+0x228)`; used by Hud_DrawZoomGrid / Hud_DrawNoiseFrame / SomethingVideoTask. |
| 0x1400a07a0 | `EffectContext_ResetBindings` | Only caller is `Effect_Release` (0x140088340, Effect vtable slot 5); it is called on `param_1[9]` (the effect's device-context wrapper) and clears the five engine bindings through engine vtable +0x88/+0x58/+0x48/+0xd0/+0x50. |
| 0x1400a2fb0 | `DialogState_Reset` | Clears the global dialog object `0x1403bd0b0`: two begin/end pairs (+0x68..+0x80), +0x88, +0xe8 and the prompt string at +0xd8. `Dialog_ExecuteChoiceActions` calls it right after executing a choice; the same global is used by `mainDialogWithChoices`, `SomethingGameTask` and `!ClickFunc`. |
| 0x140110340 | `Location_SeedRandoms` | Stores the seed at Location+0x2a8 and, under a temporarily replaced HGE RNG state, draws `Random_Float(200,800)` -> +0x2ac and `Random_Float(0,1)` -> +0x2b0, then restores the state. Call sites in `handleTutorials?` run right after +0x150/+0x154 position, +0x2e8 and +0x25c city type are written. |
| 0x14011bbc0 | `CRT_LocalStdioScanfOptions` | Returns `&DAT_1403ef5f8`; `sscanf` (0x14011bbd0) dereferences it as the `__stdio_common_vsscanf` options argument and the scanf error path `FUN_14033536c` ORs 2 into it — UCRT `__local_stdio_scanf_options`. |
| 0x14012d1a0 | `GuiElement_BeginInputCapture` | `SetLink(&0x143a13e00, this); return 1`. `0x143a13e00` is the global active keyboard-capture link (`setSavegameName` assigns it, `Settings_ApplyKeyRebind` and `Input_HandleJoystickEvent` clear it, `InitGlobal_KeyRebindLink` constructs it). It is a GUI element vtable slot in two class tables (`0x140362f60`, `0x1403698f0`), between the mouse handler 0x14012d370 and `AlwaysReturn1`/`Gui_IsElementActive`. |
| 0x140185640 | `LinkVector_DestroyRangeF0` | Destroys `[this[0], this[1])` with stride 0xf0 via `Link_Destructor`; only caller is in the global/atexit destructor tail (0x140341717). New function object that appeared since the batch started (was not in `unnamed-2026-10-29.tsv`). |
| 0x140191f40 | `Node_DeleteIfObject` | `if ((tag & 7) == 7) vtable[0](this, 1)` — the scalar deleting destructor, guarded by the engine class tag. Only caller `Gui_DestroyElementAt30` 0x140061e40. |
| 0x140193090 | `Joint_SetLength` | Clamps between Joint+0xe0 (min) and +0xdc (max), stores at +0xd8 and mirrors `length*0.05` into `b2DistanceJoint+0xa4` (type 3) / `b2RopeJoint+0x90` (type 10). Matches `Joint_CreateB2Joint` (0x140193a10) kind 3, which initialises +0xd8/+0xdc from the anchor distance and writes `maxLength*0.05`. |
| 0x1401a8340 | `Gui_ScalarDeletingDtorE78` | Calls `Gui_Destructor` (0x14012b7a0), then `operator delete(this, 0xe78)` when flag bit 0 is set, and returns `this` — MSVC scalar deleting destructor of a 0xe78-byte GUI element class. |

## New structure facts for `docs/structures.md` (agent 10)

* **Body `+0x888` = repair state, `+0x88c` = repair-queue order.** 0 = not queued,
  1/2 = queued / repaired (the panel prints `GAME_DMG_REPAIR1` for 1; the plane
  launch paths skip `+0x888 == 1`). `+0x88c` is written only by
  `Creature_RebuildRepairQueue` (running index) and read only by the two
  `Sort*ByInt88C` helpers. The repair queue itself is the `std::list` at creature
  `+0x1558` (size `+0x1560`), displayed as the property `listRepairQueue`.
* **Body light record `+0x92c..+0x943`** (used by `handleLightShifts?` 0x1401b2320
  and written by `Creature_SetOuterGunLight`, `FireShell`, `FireFlareLauncher`,
  `Engine_ApplyThrustForce`):
  `+0x92c` intensity/radius, `+0x930`/`+0x934` screen-space offsets added to the
  part centre, `+0x938..+0x943` an offset vector rotated by the part quaternion at
  `+0x970`, `+0x940` also stored as the cell z, `+0xa00` the light colour (16 bytes).
  The light grid is `0x143a15b00`, 20 columns × 30 rows, stride 0x2c (cell+0 =
  accumulated intensity, +4 = max intensity seen, +8 = screen pos, +0x10 = pos,
  +0x18 = colour, +0x28 = z).
* **Joint offsets**: `+0xc8` b2Joint*, `+0xd0` kind (0 distance, 1 revolute,
  2 weld, 3 rope), `+0xd8` length, `+0xdc` max length, `+0xe0` min length.
* **HGE RNG**: state `0x1439e8688` (LCG `state*0x343fd + 0x269ec3`), vtable
  `+0x100` seed, `+0x108` int(min,max), `+0x110` float(min,max), `+0x118` get seed.
  The four targets `0x140174350 / 0x140174320 / 0x1401742d0 / 0x140174310` have **no
  function object**; creation requested on the blackboard.
* **GUI active input link** `0x143a13e00` (Link): the element that owns keyboard
  capture (key rebind, savegame name). Cleared by `Settings_ApplyKeyRebind` and on
  joystick capture end.
* `0x143a13950` = HGE instance used by every draw helper; `0x143a139c8` /
  `0x143a139b0` are BSS objects passed as draw targets (`getFloat`/`getLong`
  unreadable — not initialised in the file image).

## Skipped (41 remaining, with reasons)

### Render / D3DEngine.cpp layer (`0x1400837xx–0x140085fcx`)
The CHECK strings in this block literally name
`D:\!ESSENTIALS\PROJECTS\HYBRID FLEET 2013EX\D3DEngine\D3DEngine.cpp`, so the layer is
the game's own D3D11 engine wrapper, not a game subsystem. Left unnamed because the
object model is not provable:

* **0x140083760** — `if (!this+0x1c5) (*(*(this+0x20)+0x1a8))(*(this+0x20), *(arg+8), 1, 1.0, 0)`.
  Called 15× from drawing code (World_Render, DrawBattleShipPanel, …). The
  `+0x1a8` slot and the `+0x20` sub-object are not identified.
* **0x140085e80 / 0x140085eb0** — `+0x1c5`-gated forwards to `*(this+0x28)+0x40` /
  `*(this+0x1a0)+0x58` after `Render_SetBlendState(this, arg)`. Same reason.
* **0x140085f40 / 0x140085f80 / 0x140085fc0** — the three "render a quad with the blend
  value from `arg+0x168` / `+0x110` / `+0x20`" twins; `0x14016cc80` (HGE vtable
  +0x2e0, `Gfx_RenderQuad`) jumps into **0x140085f40**. Naming each after a blend
  field offset would be a guess about which slot is which texture stage.
* **0x1400838e0** — resource-object factory: two device vtable calls (+0x28 with
  `{arg2,arg3,1,1,0x37,1,0,0x40}` and +0x50 with `{3,0,0x37,0}`) then `New(0x40)`
  wrapper. Called from HGE vtable +0x308 (`ADD RCX,8; JMP 0x1400838e0`). Which D3D
  object pair it creates is not proven.
* **0x140083d60** — 5-byte getter `return byte[HGE+0x10]` (`0x143a13950`); the field
  is never written in a readable block, so no name.
* **0x140088950** — 0x28-byte record init (`[0]=arg, [1]=[3]=[4]=0`); only callers are
  a D3D helper and a memset replica, no type.

### GUI element callbacks (`0x14012xxxx`)
`0x14012b4f0` (0x118-byte stack record ctor in `lootBoxCoins`), `0x14012d370`
(mouse handler: `+0x78()` gate then `+0xca2`/`+0x193`/`+0x194` flags, `param_2` 1/2
-> the two mislabelled `rep_*` callees 0x14023d3a0 / 0x14022b420), `0x14012d600`
(`+0x78()` gate, `makeSoundsForMapInstruments`, resets +0x8d8/+0x8dc/+0x8e4/+0x9e1).
Both dispatch into `rep_*` bodies whose labels are wrong, so the handlers' roles
(sound vs action) cannot be told apart.

### Small predicates/accessors with an unknown field
* **0x140073340** — `if (+0x48 != 0 && 40.0 <= +0x15f8) fall through to RET; else XOR AL,AL`.
  On the true path **no instruction sets AL**, so it returns the low byte of `this`
  (the compiler's `&&` without a materialised 1). Callers (Body_Explode,
  BulletImpact, deployFromReserve, SCR_BOMBERS, …) do `TEST AL,AL`. It is "active and
  combat value >= 40" in intent but the return-value bug makes any name a guess about
  which caller-visible property was meant.
* **0x140073530** — kills the child at `+0x48` through its vtable+0x48 and clears the
  field; `+0x48` is a state int on Creature but a child pointer here, so the owning
  class is unknown (callers `!ClickFunc`, `Scene_RebuildFromProfile`).
* **0x1400a6210** — `+0xf8 == 0 && +0xf6 != 0`; one caller (`Dialog_ExecuteChoiceActions`).
* **0x140162fe0** — `+0x88 == 0 || [[+0x88]+0x28] == 7`; used by the map-mode props
  setup to choose between the `hasTWRStat` path and the owner path. "7" is the Node
  class code, but the object at `+0x88` is not identified.
* **0x14016cd10 / 0x14016cd30** — HGE vtable +0x320 / +0x318: adapters that call the
  resource object's vtable +0x10 / +8 and truncate the float to int. The slot order
  follows `Texture_Load` (+0x310) so they are size getters, but which of the two is
  width and which is height is not provable (no callers; only the vtable).
* **0x14016dde0 / 0x14016ddf0** — raw setters of text-grid +0x1a4 / +0x1a0.
* **0x14016cf30** — `(*(*newValidHGE))()`: HGE vtable slot 0, no arguments.
* **0x140170210** — `if (p) return (*(*p+8))(p, this); return 0` (release via slot 1);
  container/element type not proven.
* **0x14018f910** — locale facet decref (vtable+0x10 of the facet found by id); the
  owning facet class is not known.
* **0x1401941f0** — `if (this+0x58) return rep_14025ecf0(this+0x58, this) != 0`.
  Used by `APP:MoveVolume` / `SaveVolume` as a per-element predicate, but the callee
  is one of the mislabelled rep bodies (a ~1.5 KB string builder), so no name.
* **0x1400f51c0** — returns nested `vtable+0x1d0` or 1.0 (a scale/alpha default); the
  nested object (`+0x288/+0x290`) is not identified.
* **0x1401102c0** — `dist*1000/speed < 7200` selects state 5 vs 7 and plays a sound
  first; what the two states mean is still open (batch 4 left it too).

### Thunks / artefacts / trivial
* **0x1400e85a0** — arg-permuting thunk to `_invalid_parameter_noinfo_noreturn`.
* **0x14010f1a0** — global vector trim through a mislabelled CRT target.
* **0x1400f8da0** — tail call `somethingSpawnShips(*(this+0x520))` (12 bytes); the
  owner class is unknown.
* **0x1400bc5c0** — `if (!IsInEditor) return 0; <editor mouse-mode handler>; return 1`;
  the callee is the stale-rep editor handler 0x1400c12a0 (agent 2's range).
* **0x140118699** — INT3 padding decoded as a function, not real code.
* **0x14019ae0f / 0x14019ae66 / 0x14019ae94** — split halves of one
  `CopyEscadraName` 0x20-stride loop plus its empty tail; not independent functions.
* **0x1400bee20** — zeroes `+0x128` on every `+0x8c0` element with byte `+0x71` set.
* **0x1400fdec0** — clears `+0x1d0`, word `+0x1a4`, `+0x1b8`, string `+0x1a8`.
* **0x140092e70** — releases `this[7]` via vtable+0x20 with a "not-self" flag.

### Record constructors / destructors with no owning type (0x1401a8340 renamed)
* **0x1401783c0** (988) — compiler-generated copy of a 0x?? struct (batch 3 agent 4).
* **0x1401a4210** — 0x20-byte record ctor (qword + 7 dwords) inlined in
  `displayCityOnMap`'s draw-list builder (colour in `R8D`).
* **0x1401a47f0** — 0x18-byte record ctor (qword, qword, dword, dword) in a
  mislabelled `memmoveMAIN` body.
* **0x1401a4b40** — destructor freeing `*(this+8)+0x20` then `*(this+8)`.

## Finding: 170 vtable-referenced code addresses in this range have no function object

While checking for missing vtable targets (every qword in `.rdata`
`0x140352000–0x14036A000` that points into `0x140070000–0x1401AFFFF`), **170 targets
have neither `getFunctionAt` nor `getFunctionContaining`** — i.e. real, never-analysed
code that is only reachable through a vtable/function-pointer table. Sample decodes:

| addr | bytes |
|---|---|
| 0x140093080 | `LEA RAX,[RCX+8]; RET` (getter, vtable slot) |
| 0x1400e7d80 | `MOV [RSP+8],RBX; PUSH RDI; SUB RSP,0x20; ... CALL 0x1400e5040; TEST BL,1` (scalar deleting dtor) |
| 0x1401700f0 | `... LEA RAX,[0x140366650]; MOV [RCX],RAX; ...` (vtable-install dtor) |
| 0x14012ca20 | `... LEA RAX,[0x140361238]; MOV [RCX],RAX; ... CALL 0x14012b7a0; TEST BL,1` (dtor) |

They are concentrated in the D3D11/shader layer (`0x14008xxxx–0x14009xxxx`),
`0x1400e7xxx`, the GUI element tables (`0x14012cxxx–0x14012exxx`), the HGE media
layer (`0x14016cxxx–0x14017exxx` — including the four RNG functions above and
`0x14016cba0/bb0/bc0/bd0/be0`, the resource factories already documented in
`structures.md`) and the font/text classes (`0x1401700f0`, `0x1401734f0` …).

Most are 8–40-byte getters/forwarders/scalar-deleting-destructors, so this is a
**mechanical creation pass**, not a discovery pass: each needs a function object at
the vtable target plus either a name from its slot context or a plate. That is a
separate assignment (it is ~170 creates, well beyond this range's 54 `FUN_*`).

Full list (space-separated, 170):

```
140073520 140082bf8 140082ea0 140082f10 140083c40 140083d50 140083e70 140085d90
140086890 140088410 140088440 1400887f0 14008b260 14008c9c0 14008d290 14008d6e0
14008d880 140092580 1400928b0 140092f30 140092f50 140092f70 140092f90 140092fc0
140093080 140093090 1400930a0 1400930b0 1400930c0 1400942b0 140094780 140095810
1400976e0 1400995c0 14009fff0 1400a0000 1400e7d80 1400e7e40 1400e80d0 1400e8210
1400e8250 1400e8290 1400f3a30 1400f3b20 1400f5200 1400f5270 1401049c0 140104a80
14011bd90 14011bda0 14011ca30 14011caa0 14012ca20 14012ca60 14012cf20 14012d210
14012d4e0 14012d660 14012d830 14012d920 14012da20 14012da30 14012db90 14012dd90
14012e1e0 14012e7e0 14012e7f0 14012e8d0 14012ece0 14015de50 14015e930 14015f0d0
14015f8d0 14015f8e0 14015f930 14015f950 14015f990 1401636b0 140165860 140165b80
1401660c0 140167610 1401680f0 140168c00 14016a130 14016bd10 14016bdf0 14016be10
14016bea0 14016bf00 14016c6d0 14016cba0 14016cbb0 14016cbc0 14016cbd0 14016cbe0
14016ccf0 14016cd00 1401700f0 140170b60 140170b80 1401734f0 140173590 1401736a0
140173720 1401737a0 1401737d0 140173830 140173840 140173850 140173870 140173890
1401738a0 1401738b0 1401738c0 1401738d0 1401742d0 140174310 140174320 140174350
140174380 140174b00 140174c20 140178a00 140178d50 140178ed0 140179030 14017c040
14017c110 14017c170 14017c190 14017c1b0 14017c1d0 14017c1f0 14017c2c0 14017c3d0
14017c680 14017c780 14017c790 14017c800 14017cb60 14017d3d0 14017d3e0 14017d460
14017d4b0 14017d4d0 14017d560 14017d5a0 14017dd00 14017dd70 14017dd90 14017eee0
14017eef0 14017ef00 14018fed0 14018ffe0 140190150 140190c10 140190cf0 140190db0
140191130 140191370 140191430 140191ef0 140192e40 1401950f0 1401952a8 1401a83c0
1401a8400 1401a8440
```

(`0x1401952a8` is unaligned, so a few entries are thunk *bodies* rather than
prologues — each needs the 1-minute sanity check before creating.)

## Cross-references for other agents

* `0x1400bc6b0` (= 0x1400c12a0) is the editor mouse-mode handler (agent 2's range);
  that would unblock **0x1400bc5c0**.
* `0x14025ecf0` and `0x14023d3a0` / `0x14022b420` are stale `rep_*` labels that block
  **0x1401941f0**, **0x14012d370** and **0x14012d600** (agent 3's range 0x1402xxxxx is
  agent 9's, but the labels are the blocker, not the addresses).
* `0x14016cd50` is `Texture_Load` (already documented); its two vtable neighbours
  +0x318/+0x320 are the size adapters left unnamed above.
