# Ghidra sweep 2026-10-29 — batch 10, agent 8 (last `FUN_*` B)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: `FUN_*` in `0x140200000–0x140350510` that are absent from
`funclet-ownership-2026-10-29.tsv` — the `__scrt_*` outlines, padding,
`0x140319da0`, `0x14028b340` (if agent 7 left it) and the open-funclet neighbours
that are not agent 1/2's funclets.

**Result: 1 renamed + plated, 16 skipped and recorded.**
No creations, no tags, no `save_program`, no README/STATUS edit, no commit. No
transaction was started, so nothing can leak.

## Inventory (live, after agent 1 finished)

`FUN_*` objects inside `0x140200000–0x140350510`: **45**. Of those **28 are TSV
rows** (agent 1/2 funclets) and **17 are unclaimed**. The 17:

| addr | size | disposition |
|---|---|---|
| `0x140316d00` | 0x111 | **renamed** `ExplosionDebrisLink_Update` |
| `0x1403161a0` | 0x84 | skipped (lighting wrapper, no owner proof) |
| `0x140316a50` | 0xd5 | skipped (tint push, no property proof) |
| `0x14033503c` | 5 | skipped (`__scrt` outline, `return 1`) |
| `0x140335050` | 7 | skipped (`__scrt_fastfail` outline, zeroes `0x1480771ec`) |
| `0x140335354` | 5 | skipped (`__scrt` outline, `return 0x4000`) |
| `0x14033536c` | 0x1a | skipped (`__scrt` stdio-flag outline) |
| `0x140335388` | 0xb | skipped (`__scrt` outline, `return [0x1403c2e68]==0`) |
| `0x140335394` | 7 | skipped (`__scrt` outline, `LEA RAX,[0x148077208]`) |
| `0x14033539c` | 7 | skipped (`__scrt` outline, `LEA RAX,[0x148077200]`) |
| `0x1403368e0`, `0x140336c40`, `0x140336d90`, `0x140336dc0`, `0x140336e30`, `0x140336e70`, `0x140336f50` | 0x27–0x39 | skipped — agent 1's funclet range |

Already done by earlier passes, verified unchanged: `0x140319da0`
(`NoOpDestructor`, plated) and `0x14028b340` (`Vector64_DestroyRangeThunk`,
batch-9 agent 9). No `FUN_*` padding bytes exist in this range (`0x14034b743`
is a TSV funclet row).

## Renamed and plated (1)

### `0x140316d00` → `ExplosionDebrisLink_Update`

`__fastcall(float* header)` where `header` is the global at **`0x1403c2d88`**:

```
+0x000 float   scale (0.66)
+0x004 float   0.075        \
+0x008 float   0.15          } used by the 4 render tasks as draw parameters
+0x00c float   0.075        /
+0x010 ptr     vector<entry> begin   (== 0x1403c2d98)
+0x018 ptr     vector<entry> end     (== 0x1403c2da0)
+0x020 ptr     vector<entry> cap     (== 0x1403c2da8)
entry: 0x38 bytes, +0x00 active byte, +0x04/+0x08 x/y, +0x10 Link (vtable
0x140352310), +0x18 sprite ptr, +0x20 ?, +0x28 end-time float, +0x2c age float,
+0x30/+0x34 float speeds
```

Algorithm: for each live entry `age += header->scale * time_related_global_`;
retire the entry when `age == -1.0`, when `header->end_time <= age` (excluding the
equal-to-sentinel case), or when `active != 0 && sprite == NULL`. Retiring shifts
the following entries down one 0x38 stride (`ReassignLinkNode` on the Link at
+0x10), calls `freeLinkMemory_` on the last Link, and decrements the end pointer.

Owner proof (not inferred from the body, but from the only other references):

* the **only writer** of the `+0x10` vector (`0x1403c2d98`) is
  `FX_SpawnExplosionDebris` `0x1401c7270`, which appends exactly this 0x38-byte
  entry — `*end = 0`, `+0x4 = x`, `+0x8 = y`, `+0x10 = &LinkVFTABLE`,
  `+0x18 = 0`, `+0x20 = 0`, `+0x28 = size/100`, `+0x2c = 0`, `+0x30`, `+0x34`
  — through `VectorLink56_InsertAt`;
* `DtorGlobal_ExplosionDebrisLink` `0x14034fe40` (atexit, paired with
  `CInit_Atexit_ExplosionDebrisLink` `0x140004900`) frees the same
  `0x1403c2d98`;
* the four call sites are the four scene renderers, after the final
  `D3DEngine_DrawVertices1`/`Gfx_QuadPositionFromExtents` flush:
  `VideoTask_RenderEditorScene` `0x140302b1a`, `VideoTask_RenderBattleScene`
  `0x140307a5e`, `VideoTask_RenderMapScene` `0x14030c72d`,
  `VideoTask_RenderMenuScene` `0x140311f09`, all passing
  `&FLOAT_1403c2d88`.

So this is the per-frame aging/cleanup pass of the explosion-debris list; the
name follows the existing `InitGlobal_/DtorGlobal_ExplosionDebrisLink`
convention. Name-collision check: existing token sets
`{CInit,Atexit,ExplosionDebrisLink}`, `{DtorGlobal,ExplosionDebrisLink}`,
`{FX,Spawn,ExplosionDebris}` are not subsets of `{ExplosionDebrisLink,Update}`.

## Skipped and recorded (16)

### `__scrt_*` / CRT outline stubs (7) — compiler outlines, not semantic functions

Re-read the bytes and the **callers**, which is more than batch 9 had:

* **`0x14033503c`** — `MOV EAX,1; RET`. Sole caller `CRT_InitializeProcess`
  `0x140334bb9`, as `_configure_narrow_argv(FUN_14033503c())`; the returned 1 is
  `_crt_argv_unexpanded_arguments`. It is the outlined constant argument of
  `_configure_narrow_argv`, not an argv API.
* **`0x140335050`** — `AND dword [0x1480771ec],0; RET` (it ignores its argument).
  Both callers are inside `__scrt_fastfail` `0x140335058` (`0x140335086`,
  `0x14033518c`, each `MOV ECX,3`), i.e. an outlined "clear the fastfail state"
  fragment of the fail path.
* **`0x140335354`** — `MOV EAX,0x4000; RET` (`_O_TEXT`). Sole code caller
  `CRT_InitializeProcess` `0x140334b80`, as `_set_fmode(FUN_140335354())`; also
  reachable as a pointer at `.rdata` `0x1480889f0`. It is the outlined default
  `_fmode` constant.
* **`0x14033536c`** — ORs `0x24` into `[0x140397200]` and `0x2` into
  `CRT_LocalStdioScanfOptions`. Sole caller `CRT_InitializeStdioOptions`
  `0x140334c2c` (`__xi_a[2]`); pointer copy at `.rdata` `0x1480889f8`. Outlined
  body of that initializer, so naming it separately would duplicate its caller.
* **`0x140335388`** — `return *(int*)0x1403c2e68 == 0`. Sole caller
  `CRT_InitializeProcess` `0x140334bce`, gating `__setusermatherr(...)`. The
  global's writer is unknown (not reachable from any code reference), so the
  predicate's meaning (a `__scrt` link-config flag) is not provable.
* **`0x140335394` / `0x14033539c`** — `LEA RAX,[0x148077208]` / `[0x148077200]`;
  `RET`. Sole callers `mainCRTStartup` `0x140334ceb` / `0x140334d17`. These are
  the outlined table-address loads for the `_initterm` bracket (the two globals
  are adjacent 8-byte cells), not getters with an identity.

Naming any of these after a guessed MSVC symbol would be a guess, and naming the
behaviour (`ReturnOne`, `GetDefaultFmode`, `GetInitTableStart`) collides with
`AlwaysReturn1` `0x1400055d0` / duplicates the caller's plate. Verdict unchanged
from batches 5–9: **leave unnamed, behaviour now documented by caller**.

### Rendering helpers whose property fields stay unidentified (2)

* **`0x140316a50`** (0xd5) — `__fastcall(float a, float b)`: calls the ramp
  builder `0x1402f3fd0` (currently stale-labelled
  `rep_1402c8b90_..._pow`, see below) to fill a 4-float
  `{x, brightness, darkness, 1.0}` block, then pushes it with
  `compareAndUpdateFloatArray_` `0x1400a04e0` into five render objects
  (`0x143a13968+0x128`, `0x143a13958+0x130`, `0x143a13960+0x1b0`,
  `0x143a13978+0x130`, `0x143a13970+0x130`) and sets
  `Property_SetFloat(*(0x143a13970+0x138), 1.0/0.0)` from
  `ZOOM_LEVEL*0.142857 > 0.4`. The same five objects receive their reflective
  parameters from every `VideoTask_Render*Scene`, so these are per-scene render
  objects — but *which* property `+0x128/+0x130/+0x1b0/+0x138` is has never been
  read, so the operation cannot be named.
* **`0x1403161a0`** (0x84) — `__fastcall(int layer, int index)` (the only call
  site, `Gui_FlushDrawList` `0x1402fa10b`, passes `(0x3b, 0)`; verified in the
  disassembly: `XOR EDX,EDX; LEA ECX,[RDX+0x3b]`). It stamps
  `_DAT_148075d50/_d54 = (layer,index)`, bounds-checks the layer vector
  `DAT_14801dd00[layer]` (0x18-stride vector array, 100 layers — see
  `InitGlobal_ChnVectorPool` `0x1400046e0`), checks the 100-column dword grid
  `DAT_14800f210[layer*100+index]`, then feeds the first element's `+0x38/+0x44`
  to `0x140316a50`. Effectively "select the current draw-list cell and apply its
  first entry's tint", but the tint fields are the same unidentified pair, so the
  name would be a guess.

**Correction for the record (b7 agent 9 / b5 agent 10 answered this as
"time-of-day/sky ramp"):** the ramp builder `0x1402f3fd0` is *not* proven to take
an hour. Its arguments are `(level/20 clamped to 0..1, value in 0..12+ with a
`0.75-(t/12-1)^2` day curve and `0.1` below 3)` mixed with the global
`DAT_143a119a0`, which `CityLandscape_RenderTiles` `0x1402ed4e0` **saves/restores
around its zoom override** and `UpdateZoom` writes. In
`Hud_TransformMarkerToScreen` `0x1402f4947` the second argument is the object's
`+0x38`, the same field used as the projection depth divisor in that very
function, so "depth/zoom ramp" is at least as likely as "hour of day". The
`{x, brightness, darkness, 1.0}` output and its three call sites are proven; the
input semantics are not. `0x1402f3fd0` itself is a `rep_*` outside this agent's
scope (`0x140200000–0x1402FFFFF`) — **for batch-10 agent 5/9: it is the ramp
builder, not `pow`**, and the only `pow` call in it is the two `powf`/`pow`
inside the curve.

### Agent 1's still-open funclets (7) — reported, not touched

`0x1403368e0`, `0x140336c40`, `0x140336d90`, `0x140336dc0`, `0x140336e30`,
`0x140336e70`, `0x140336f50` are absent from the TSV but lie inside agent 1's
`0x140336730–0x140341FFF` range, so they are agent 1's by the ownership rule.
They are still `FUN_*` after agent 1 finished (its note says 36 funclets left
open), so they are simply part of that open set, not strays. Shape confirmed this
pass — all seven are `/EH` funclets:

```
MOV [RSP+0x10],RDX ; PUSH RBP ; SUB RSP,0x20 ; MOV RBP,RDX
<destroy frame member(s)> ; XOR EDX,EDX ; XOR ECX,ECX ; CALL 0x14033658e
```

with the member destroyed read from the frame:

| funclet | frame member(s) | destroyer |
|---|---|---|
| `0x1403368e0` | `+0x70`, `+0x78`, `+0x20` | `0x1400099e0` |
| `0x140336c40` | `+0x60` (virtual `+0x4` dispose, flag 1) | vtbl call `[0x140351360]` |
| `0x140336d90` | `+0x50`, `+0x68`, `+0x58` | `0x140009990` |
| `0x140336dc0` | `+0x60`, `+0x78`, `+0x68` | `0x1400099e0` |
| `0x140336e30` | `+0x80` → `0x1400199d0`, then `+0x38`/`+0x88` | `0x140023990` |
| `0x140336e70` | `+0x88` stored through `+0x98` | (store only) |
| `0x140336f50` | `+0x50` → `0x1400199d0`, then `+0x68`/`+0x58` | `0x140009990` |

Nothing in their bodies ties them to any function in *this* agent's scope (the
two remaining `FUN_*` helpers here have no unwind data), so no rename was
possible even if they had been mine.

## New structure facts for agent 10

* Global `0x1403c2d88` **`ExplosionDebrisLink` header** (0x28 bytes, then
  `0x1403c2db0` is a different global written by `MapMode_DrawRadarSweep`):
  scale +0x0, draw parameters +0x4/+0x8/+0xc = 0.075/0.15/0.075, and a
  `vector<0x38-byte entry>` at +0x10. Entry layout as in the rename section
  (`Link` at +0x10, vtable `0x140352310`); inserted with
  `VectorLink56_InsertAt(0x1403c2d98, end, pos, ???)`; aged by
  `ExplosionDebrisLink_Update`; freed by `DtorGlobal_ExplosionDebrisLink`.
* `DAT_14801dd00` is a **100-layer array of 0x18-byte `vector<vector<T*>>`**
  (`InitGlobal_ChnVectorPool`), indexed `layer*0x18`; `DAT_14800f210` is the
  matching 100×100 dword count grid (`layer*100+index`, memset 28000 B). The
  layer numbers observed: 0xa–0x45 world/marker layers, **0x3b special
  (cleared first, `_d54 = 0`, drawn last)**, 0x3c–0x45 HUD markers.
* `_DAT_148075d50/_d54` = "current layer / current index" stamps written by
  `World_Render`, `VideoTask_RenderBattleScene`, `Sprite_GetMinDimension`,
  `FUN_1403161a0` and `FUN_140316a50`-adjacent code.
* `Hud_TransformMarkerToScreen` caches the ramp output in
  `_DAT_148075d38`(4 floats)/`_DAT_148075d48`(flag) and compares the marker's
  `+0x44` against the float at `0x148015fc8` before recomputing.

## Out-of-scope stale label found (report only)

`0x1402f3fd0` is labelled `rep_1402c8b90_API-MS-WIN-CRT-MATH-L1-1-0.DLL::pow`
but the body is the **4-float brightness/darkness ramp builder** described above
(no `pow` of its own arguments; the two `powf`/`pow` calls are `powf(t/12-1,2)`
and `pow(1-x,12)` inside the curve). Its three callers are `0x140316a50`,
`Hud_TransformMarkerToScreen` `0x1402f4947` and the function-object gap at
`0x1402f463e`. Not renamed here: it is a `rep_*` in agent 5/9's range.
