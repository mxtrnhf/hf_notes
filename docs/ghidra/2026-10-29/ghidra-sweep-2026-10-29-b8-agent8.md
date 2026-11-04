# Ghidra sweep 2026-10-29 — batch 8, agent 8 (last real `FUN_*`)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `FUN_*` that is **not** in `funclet-ownership-2026-10-29.tsv` and is
not a creation target of agents 1/2 (`0x140070000–0x1401AFFFF` `.rdata` targets).
No `rep_*` and no `/EH` funclets were touched.

**Start: 134 in-scope `FUN_*`** — 63 global-destructor tail functions
(`0x14034b850–0x14034fe50`), 54 others across `.text`, 4 Body slots owned by
agent 9, and the 13 `/EH` funclets at `0x1403368e0–0x140336f50` (owner missing
from the TSV). **End: 76 renamed + plated, 0 created.** 55 in-scope `FUN_*`
remain: 41 deliberate skips (below), 13 funclets (agent 1's role), and
`0x14004c7e0` (agent 9's slot at the time of writing; the other three slots were
renamed by agent 9 during this pass). A further 28 `FUN_*` appeared inside
`0x140070000–0x1401AFFFF` while this pass ran — they are the agents 1/2
`create_function` targets from the batch-7 `.rdata` list, not part of this scope.

## A. Global-destructor tail (`0x14034b850–0x14034fe50`) — 63 renamed

These are the `FUN_*` members of the atexit-teardown block that batch-7 agent 5
named for the `rep_*` twins. Each body destroys exactly one global and was
classified from the callee plus the global's layout; the batch-7 naming
convention (`DtorGlobal_*`, `Container_<addr>`) is kept.

| kind (n) | globals | evidence |
|---|---|---|
| `DtorGlobal_Link_<addr>` (17) | `1403bd060`, `1403ef558`, `1403c0d38/0d50/0d68/0d80/0d98/0db0`, `1403c1438/1450`, `1403c2d48/2d60`, `143a2bfa0/2bfc0` | `LEA RCX,[global]; JMP 0x140194d20` = `freeLinkMemory_` |
| `DtorGlobal_LinkPair_<addr>` (2) | `1403bd578/590`, `1403bd5b8/5d0` | two `freeLinkMemory_` calls in one body |
| `DtorGlobal_LinkVector_<addr>` (12) | `1403ef3a0`, `143a13de8`, `143a15820/5868/58b0/58e0/59c0`, `143a13a98`, `143faa5d8`, `147fc7590/73d8/7578` | `JMP 0x1400052b0` = `freeLinkMemory_` per 0x18-byte element, then free buffer |
| `DtorGlobal_String_<addr>` (9) | `1403bd548`, `1403c12a8/13b0/13d0/13f0/1410/1690/16b0`, `1403c2ba0` | `0xf < cap` then free buffer, reset len 0 / cap 0xf / first char 0 (MSVC string at `+0/+0x10/+0x18`) |
| `DtorGlobal_Container_<addr>` (13) | `1403eefe0`, `1403ef000/050/078/0f8/5c8`, `1439e6038`, `143a33c58`, `143faa5f0`, `147fc6880/73c0`, `14801dce8` | sized-delete (`& ~7` or `& ~0xf`) then zero begin/end/cap |
| `DtorGlobal_Vector18_<addr>` (4) | `1403ef580/5a8` (element dtor `0x1400d9d70`), `1439e5fb0/5ff8` (element dtor `0x14011b730`) | tail-call `0x1400e8d20` / `0x14011ef50` |
| `DtorGlobal_Vector32_<addr>` (4) | `143a15990`, `143a1c350`, `143a158c8`, `143a13b30` | per-element string free `0x140011810`, `& ~0x20` buffer free |
| `DtorGlobal_Vector12_<addr>` (2) | `1439e92f8`, `14801dd60` | `(end-begin)/0xc*0xc` buffer free |
| `DtorGlobal_List_<addr>` (4) | `143a2dde0`, `147fc6e70`, `147fc6e88`, `147fc6f68` | sentinel detach, 0x28-byte nodes, `Link` at node+0x10 freed with `freeLinkMemory_`, then sentinel freed |

Every one carries a plate naming the destroyed global and the callee.

## B. D3DEngine / HGE dispatch family — 7 renamed (new proof)

The batch-7 pass left these unnamed because the HGE sub-objects were not
identified. `InitD3DEngine?` 0x140083ed0 resolves them (D3D11CreateDeviceAndSwapChain
call at `0x140084164`, results stored in HGE_Impl):

* **HGE `+0x18` = `ID3D11Device`**, **`+0x20` = `ID3D11DeviceContext`**,
  **`+0x28` = `IDXGISwapChain`**. Device ops used: `+0x28` CreateTexture2D,
  `+0x40`/`+0x48` view creation, `+0x50` CreateDepthStencilView, `+0x80` etc.;
  context ops: `+0x108/+0x120/+0x158/+0x160/+0x168` state/input/RT binds.
* **HGE `+0x1a0` = current `ShaderDefault`/concrete-shader object** (assigned
  from `+0x228` and switched through its slot +0x28). Its slot `+0x40`/`+0x48`
  are concrete-shader `EmitVerticesA/B`; `Render_SetBlendState` calls its
  `+0x70` (blend/state selector).

| addr | new name | proof |
|---|---|---|
| 0x140083760 | `Gfx_ClearDepthBuffer` | `ID3D11DeviceContext::ClearDepthStencilView` = context vtable **+0x1a8**; called with `(*(arg+8), 1, 1.0, 0)` — flags 1 = `D3D11_CLEAR_DEPTH`, depth 1.0, stencil 0 |
| 0x1400838e0 | `Gfx_CreateDepthStencil` | device `+0x28` CreateTexture2D with Format 0x37, BindFlags 0x40 (`D3D11_BIND_DEPTH_STENCIL`), then device `+0x50` CreateDepthStencilView, 0x40-byte wrapper `{texture, view, desc}`; HGE vtable `+0x308` stub `0x14016cba0` |
| 0x140085e80 | `Gfx_Present` | `IDXGISwapChain::Present` = swap-chain vtable **+0x40**, args `(this+0x11 != 0, 0)` = vsync, flags |
| 0x140085eb0 | `Gfx_SubmitColoredRect` | HGE vtable `+0x2c8` stub converts ARGB with `Color_ARGBToFloat4`, calls this with `(x,y,w,h,colour,blend,arg)`; body = `Render_SetBlendState` + shader slot `+0x58` |
| 0x140085f40 | `Gfx_SubmitQuadA` | body behind HGE `+0x2e0` (`Gfx_RenderQuad` 0x14016cc80); blend from quad `+0x168`, shader `+0x40` (EmitVerticesA) |
| 0x140085f80 | `Gfx_SubmitTriangle` | HGE `+0x2d0` (stub 0x14016cd00); blend from descriptor `+0x110`, shader `+0x48` (EmitVerticesB). Sole game caller is `Body_DrawMeshPolygon` 0x14004d8e0, which emits one 3-corner descriptor per mesh-fan triangle (agent 9 independently proved the slot is the 3-vertex primitive) |
| 0x140085fc0 | `Gfx_SubmitQuadC` | HGE `+0x2d8` (stub 0x14016ccf0); blend from quad `+0x20`, shader `+0x50` |

`Gfx_RenderQuad` (0x14016cc80) is the statistics wrapper and the HGE slot;
`Gfx_SubmitQuadA` is the actual draw. The earlier doubt about `Gfx_DrawQuad`
is resolved by the shader-slot identity, not by the blend field alone.

## C. Texture size adapters — 2 renamed (new proof)

`TextureSingle_CreateFromMemory` (0x1400852b0) calls
`ID3D11Texture2D::GetDesc` (`texture vtable +0x50`) into a local desc and then
copies the first 0x2c bytes into the object starting at **`+0x20`**:
`+0x20` = `D3D11_TEXTURE2D_DESC.Width`, `+0x24` = `.Height`.
`TextureSingle_GetField20` (vtable slot 1, offset `+8`) returns `+0x20`;
`TextureSingle_GetField24` (slot 2, offset `+0x10`) returns `+0x24`.

| addr | new name | proof |
|---|---|---|
| 0x14016cd10 | `Gfx_GetTextureHeight` | calls texture `+0x10` = slot 2 = `+0x24` = Height; HGE vtable `+0x320` |
| 0x14016cd30 | `Gfx_GetTextureWidth` | calls texture `+8` = slot 1 = `+0x20` = Width; HGE vtable `+0x318` |

## D. GUI callbacks and predicates — 4 renamed

| addr | new name | proof |
|---|---|---|
| 0x14012d370 | `GuiElement_HandleMouseButton` | element vtable slot `+0x100` in every GUI table (`0x140362f60`, `0x1403698f0`, ...), immediately before `GuiElement_BeginInputCapture`. Gates on IsActive `+0x78` and `+0xca0`; `param_2 == 1` starts a drag (`+0xc98 == 0` -> `0x14023d3a0`), `param_2 == 2` ends it (`-> 0x14022b420`); returns 1/0 |
| 0x14012d600 | `GuiElement_ResetDragPosition` | element vtable slot `+0x140`, after `Gui_HandleCardDrop`; calls `makeSoundsForMapInstruments`, restores `+0x8dc` into `+0x8d8`, clears `+0x8dc/+0x8e4/+0x9e1` — the drag state set by `Gui_HandleCardPickUp` |
| 0x140162fe0 | `Node_IsTopLevel` | true when master `+0x88 == 0` or `master->[0x28] == 7`; class code 7 is Node (Creature 47, Body 15, Frame 31), i.e. not parented under a Body/Frame/Creature |
| 0x140319da0 | `NoOpDestructor` | single `RET 0` body; shared empty destructor/callback target (callers `SuperBigDeconstructor`, `b2World_DestroyBody`) |

## E. Skipped and recorded (41)

### D3D / HGE
* **0x140083d60** (5) — `MOVZX EAX,byte[this+0x10]`; the field has no readable
  writer, class unknown.
* **0x140088950** (21) — 0x28-byte record init (`[0]=arg; [1]=[3]=[4]=0`,
  `[2]` left untouched) inlined at `+0x50` of `CSGlitch_Constructor` and
  `ShaderDeferringCloseAndPrebloom_Constructor`. Shape does not match
  `ShaderData_Constructor` (0x14009f930) and the record's type is not proven.
* **0x14016cf30** (22) — calls slot 0 of the object at `0x1439e8670`; that object
  and the slot's meaning (HGE slot 0 is not Release in `HGEVFTABLE`) are unproven.
* **0x14016dde0 / 0x14016ddf0** (9/7) — bare stores into TextGrid `+0x1a4`
  (float) and `+0x1a0` (dword). Call sites are `TextGrid_LayoutProjected`,
  `TextGrid_LayoutLocal`, `TextGrid_CreateObject`; the decompiler loses the
  argument values and no TextGrid layout exists in `structures.md`.

### GUI / records with no owning type
* **0x14012b4f0** (220) — ctor of a 0x118-byte stack record in `lootBoxCoins`
  (three 0x58 groups, `1.0` at `+0x54/+0xac/+0x104`, tag `+0x108/+0x110`);
  it is a draw-list/coin record, owning type not proven.
* **0x1401a4210** (60) — 0x20-byte record ctor `(qword + 7 dwords)` inlined in
  `displayCityOnMap` and a CRT twin; type unknown.
* **0x1401a47f0** (22) — 0x18-byte record ctor inside `memmoveMAIN`; type unknown.
* **0x1401a4b40** (57) — frees `*(this+8)+0x20` then `*(this+8)`; no caller and
  no owning type.
* **0x1401783c0** (988) — compiler-generated struct copy used by the HGE media
  layer; type unknown (batch-3 verdict re-confirmed).

### Small predicates / accessors with unknown fields
* **0x140073340** (26) — `if (+0x48 != 0 && 40.0 <= +0x15f8) RET; else AL=0`.
  The true path never sets AL, so the caller-visible result is the low byte of
  `this`. Behaviour is proven, intent is not; naming it after the predicate
  would misdescribe the return value.
* **0x140073530** (38) — `if (p=this+0x48) (*(*p+0x48))(p); this+0x48=0`.
  `+0x48` is a state int on Creature but a child pointer here; class unknown.
* **0x1400a6210** (24) — `+0xf8 == 0 && +0xf6 != 0` on the object returned by
  `Profile_GetFirstPlayerCreature` in `Dialog_ExecuteChoiceActions`; neither
  byte is documented.
* **0x1400f51c0** (52) — nested `vtable+0x1d0` of `[[[+0x288]+0x10]+0x50]` or
  1.0; used as a screen-offset scale by `VideoTask_RenderMapScene` /
  `FUN_14015f0d0`, but the nested object is unidentified.
* **0x140092e70** (44) — releases `this[7]` through vtable `+0x20` with the
  not-self flag and clears the field; container element type unknown.
* **0x1400bee20** (58) — zeroes `+0x128` on every element of the `+0x8c0`
  vector whose byte `+0x71` is set; only caller is `rep_14017a420_New`.
* **0x1400fdec0** (61) — clears `+0x1d0`, word `+0x1a4`, `+0x1b8` and the string
  at `+0x1a8/+0x1c8`; class unknown.

### Thunks / artefacts
* **0x1400e85a0** (20) — permutes `(a,b,c)` to `(b,c,a)` and tail-calls the
  0x18-stride element destructor `0x1400d9d70`; element class unknown.
* **0x14010f1a0** (69) — trims the global vector at `0x1403ef580` through
  `0x1400d9a10` (a chunk of `displayinShipworks?`) and copies
  `DAT_1403ef578` -> `DAT_1403ef57c`; helper semantics unproven.
* **0x1400f8da0** (12) — `JMP` into `somethingSpawnShips` at `0x140204600` with
  `*(this+0x520)`; owner class unknown.
* **0x1400bc5c0** (32) — `if (!IsInEditor) return 0; <editor chunk>; return 1`.
  The call target `0x1400c12a0` is a separate editor handler but is still
  unnamed, so the handler's mode is unknown.
* **0x1401102c0** (117) — selects state 5 vs 7 from
  `dist*1000/+0x494 < 7200` and calls an unnamed state setter; the 5/7 meaning
  is unresolved (batch-4/6/7 all left it).
* **0x140170210** (24) — `if (p) return (*(*p+8))(p, this); return 0` on the
  manager `0x143a119e8`; only callers are inside `rep_..._WriteToClientLog`.
  Object and slot semantics unproven.
* **0x14018f910** (36) — locale-facet decref (vtable `+0x10` of a facet found by
  id); owning facet class not known. No callers, `.pdata` only.
* **0x1401941f0** (40) — `if (this+0x58) return 0x14025ecf0(this+0x58, this) != 0`;
  the callee is still a stale `rep_...` body.
* **0x14028b340** (20) — `(a,b,c) -> (b,c,a)` then `JMP 0x140287730`, a
  vector-of-strings teardown; compiler-generated member-array destructor.
* **0x140118699** (7) — `INT3` padding decoded as a function, not code.
* **0x14019ae0f / 0x14019ae66 / 0x14019ae94** (50/46/16) — split halves of the
  `CopyEscadraName` 0x20-stride loop plus its empty tail; not independent
  functions.
* **0x1400458c0** (3342) — editor "collect and lay out the selected ship's
  mounted parts" pass; body > 0x2000, product list still not pinned.
* **0x1403340d8** (43) — scalar deleting destructor; `0x140378f08` is a
  name→pointer record table, not a vtable, so the class is not provable.

### CRT / `__scrt_*`
* **0x140017d10** (36) — virtual dispatch through a doubly-indirect table, no
  code xref (`.pdata` only).
* **0x140027f90** (120) — iterates `+0x350/+0x358` and calls a stale
  `rep_..._MakeGlobal?` on `element+0x58`.
* **0x140049cd0** (35) — `int(+0x2e8) < arg -> 0; else float(+0x248) != 0`;
  neither field identified.
* **0x14033503c / 0x140335050 / 0x140335354 / 0x14033536c / 0x140335388 /
  0x140335394 / 0x14033539c** (6–27) — `_set_app_type` outline stubs
  (`mov eax,1; ret`; zero `0x1480771ec`; `_O_TEXT` 0x4000; scanf-options OR;
  `0x1403c2e68 == 0`; `&0x148077208`; `&0x148077200`). No MSVC symbol provable;
  batches 5–7 reached the same conclusion.

## Hand-offs

1. **13 `/EH` funclets at `0x1403368e0–0x140336f50`** (39–58 bytes) are still
   absent from `funclet-ownership-2026-10-29.tsv`. They are agent 1's role:
   map the owner from `.pdata`/`FuncInfo4`, then name `<Owner>_EhCleanup_*`.
   Addresses: `0x1403368e0, 0x140336c40, 0x140336d90, 0x140336dc0, 0x140336e30,
   0x140336e70, 0x140336f50`.
2. **`0x14004c7e0`** (7 bytes) was still `FUN_*` at the end of this pass. Agent 9
   owns it and renamed the sibling slots `0x140018fb0`, `0x14004d8e0`,
   `0x140053110`.
3. The `DtorGlobal_*` tail names are mechanical; agent 10's `CInit_Atexit_<Tag>`
   map can strip `DtorGlobal_` to `Link_<addr>` / `String_<addr>` /
   `Container_<addr>` / `List_<addr>` / `Vector12/18/32_<addr>`.

## New structure facts for agent 10

* **HGE_Impl fields**: `+0x18` `ID3D11Device`, `+0x20` `ID3D11DeviceContext`,
  `+0x28` `IDXGISwapChain`, `+0x1a0` current shader (`ShaderDefault*`),
  `+0x1c5` render-disabled/dummy byte, `+0x228` default `ShaderDefault`,
  `+0x300/+0x308` resource/depth-view factories, `+0x310` `Texture_Load`,
  `+0x318/+0x320` texture size getters.
* **TextureSingle layout**: `+0x8` vtable, `+0x20` Width, `+0x24` Height
  (from `ID3D11Texture2D::GetDesc`), `+0x28..+0x4c` the remaining desc fields,
  `+0x50` depth-stencil view in the 0x40-byte depth wrapper.
* **HGE vtable `0x1403672f0`**: `+0x2c8` coloured-rect submit, `+0x2d0`
  3-vertex primitive submit (`body_drawMeshPolygon`), `+0x2d8`/`+0x2e0` quad
  submits B/A, `+0x300` `RenderTarget_Create`, `+0x308`
  `Gfx_CreateDepthStencil`.
