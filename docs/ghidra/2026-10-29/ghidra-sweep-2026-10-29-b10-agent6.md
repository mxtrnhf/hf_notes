# Ghidra sweep 2026-10-29 — batch 10, agent 6 (Q4 leftovers + vtable slots)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: the remaining `rep_*` in `0x140300000–0x140350510` outside the funclet
set, the three withheld names, and the six `Landpart`/`Cloud`/`Ground` vtable
slots that had executable code but no function object.

**Result: 0 `rep_*` left open (0 renamed by me, 3 closed by their owner agents),
0 withheld names proven (all three re-checked and recorded, 2 plates sharpened),
6 function objects created + named + plated.** No `save_program`, tags,
README/STATUS edit or commit. No leaked transaction (all writes went through the
documented helpers; `analysis_status` still reports `analyzing:false`).

## 1. `rep_*` leftovers in `0x140300000–0x140350510` — 0 open

Live check at 16:02: 75 `rep_*` function objects exist in the range and **all 75
are rows of `funclet-ownership-2026-10-29.tsv`** (EH funclets / `rep_wrap_0_*`
thunks), i.e. none is an independent body. The three that batch 9 had listed as
"outside the TSV" were renamed by their owner agents while this pass was running:

| addr | old label | current name |
|---|---|---|
| 0x1403182a0 | `rep_1402ed2b0_..._Xtime_get_ticks` | `TimerToken_Update` |
| 0x140336ea0 | `rep_14030bf70_..._CxxThrowException` | `Vector4_InsertRange_EhCleanup_0x98` |
| 0x140336f00 | `rep_14030bfd0_..._CxxThrowException` | `Vector4_InsertRange_EhCleanup_0x98_2` |

Three closure rows were appended to `rep-audit-2026-10-29-q4.tsv` (verdict
`renamed (b10, not by agent6)`) so the audit rebuild picks up the new names
instead of the stale-label verdicts. The only `FUN_*` still in the range are
agents 7/8's (padding, `__scrt_*`, the open funclets) — out of scope.

## 2. The three withheld names — still not provable, evidence sharpened

No name was claimed: none of the three has a caller, string, or table slot that
identifies the interface method. Two plates were rewritten with the decisive
negative evidence found this pass.

### `0x14017c780` — HGE_Impl +0x268, `FUN_14017c780`
* Body: `MOV ECX,arg2; MOV RDX,arg3; JMP [0x1439e89b0]`.
* **New and decisive:** the slot is *never initialised*. The BASS loader at
  `0x14017d1eb–0x14017d235` resolves three names in a row and stores them:
  `0x140367210 "BASS_ChannelSetFX" → 0x1439e8998`,
  `0x140367228 "BASS_ChannelRemoveFX" → 0x1439e89a0`,
  `0x140367240 "BASS_FXSetParameters" → 0x1439e89a8`, and then goes straight to
  `0x140367258 "BASS_GetDeviceInfo" → 0x1439e86c8`. Nothing in the image writes
  `0x1439e89b0`; it is the only anonymous slot in that hand-built pointer table
  and stays null at run time.
* Consequence: the virtual is dead. There is **no** `CALL [reg+0x268]` on an
  HGE_Impl object in the whole image (the only `+0x268` indirect call,
  `0x14004c490`, dispatches on a Body). Calling the slot would jump to null.
* Positional inference alone (`BASS_FXSetParameters` then BASS's
  `BASS_FXGetParameters`; `BASS_FXSetPriority` has the same 2-arg shape) is not
  proof. Verdict: unnamed, plate updated.

### `0x14017c800` — HGE_Impl +0x188 / +0x1a8 / +0x1b8, `FUN_14017c800`
* Body: `MOV EAX,0xffffffff; RET`.
* The seven-slot gap between `Music_GetAmplify` (+0x180) and `Stream_Load`
  (+0x1c0) is `-1 / empty / false / empty / -1 / empty / -1`
  (`0x14017c800`, `0x140005e70` empty, `0x1400055c0` false, …) — a block of
  unimplemented music virtuals; only the original header could say which
  length / position / volume / play / stop method owns which index.
* **New:** all eight `.text` `CALL [reg+0x188]` sites (`0x1400354d2`,
  `0x140035526`, `0x140035fc9`, `0x140037913`, `0x140037c87`, `0x14024fc93`,
  `0x1402b3b88`, `0x1402b8348`) dispatch on Body/Gui objects, not HGE_Impl, and
  there is **no** `CALL [reg+0x1a8]` or `[reg+0x1b8]` at all. So no caller can
  identify the property being stubbed. Verdict: unnamed, plate updated.

### `0x14004c7e0` — Body vtable `0x140352a30` +0x240, `FUN_14004c7e0`
* Body: `MOV RAX,[RCX]; XORPS XMM1,XMM1; JMP [RAX+0x238]` — i.e.
  `(*this->vtable[+0x238])(this, 0.0f)`.
* Confirmed this pass: the +0x238 target on the Body table (`0x14004bed0`) never
  reads XMM1 and takes no float argument, so the fixed `0.0` is signature noise,
  not a semantic value. Both call sites are in `Gui_BootTitlePass`
  (`0x1402a3177`, `0x1402a3394`), each right after setting the element colour at
  `+0xa8c` and right before the `+0x2c8` / `+0x98c` passes, and neither sets
  XMM1. Name would only restate "call Draw with 0", and the +0x238 slot itself
  still carries the stale `handleAmmoInBattle?` label, so naming +0x240 after it
  would propagate a wrong name. Verdict: unnamed (plate already carried this).

## 3. Six created + named + plated (the slot list)

Tables re-verified from RTTI this pass: `Landpart` vtable `0x140377060`
(COL `0x140381088`), `Cloud` `0x1403770a0` (COL `0x140381100`), `Ground`
`0x1403770e8` (COL `0x140381180`). Slots, in table order:

| addr | name | size | slot | proof |
|---|---|---|---|---|
| 0x140316150 | `Landpart_SetParams` | 70 (0x46) | Landpart/Cloud/Ground +0x08 | writes the shared parameter block +0xc x, +0x10 y, +0x30, +0x34, +0x38, +0x3c, +0x44, +0x48, +0x4c from 9 args — the same fields as `Cloud_SetSpawnParams`/`Ground_SetSpawnParams` but without the fixed 999 timer and without +0x60 |
| 0x1403365ac | `Thunk_PureCall` | 6 | Landpart +0x18 and +0x20 | `JMP [0x1403515f0]` = `PTR__purecall`; the same thunk fills ~30 pure slots across the image |
| 0x1402f4b70 | `Cloud_DrawSprites` | 533 (0x215) | Cloud +0x10 | projects +0xc x/y with +0x38 scale / +0x44 colour key / ZOOM_LEVEL / TARGET_SCREEN / shake, then per child: `+0xd4 = +0x58`, `Hud_MarkerSetColor(child,+0x5c)`, `Hud_DrawSpriteAt(...)` |
| 0x1402f4500 | `Cloud_BuildDrawList` | 731 (0x2db) | Cloud +0x18 | same projection, writes the 16-byte quad to `*param3`, `*param4 = 0`, then appends one 0x28-byte draw record per child (`Array_Push40`) and fills it through 0x1402e0830 |
| 0x1402f4d90 | `Ground_DrawSprites` | 1653 (0x675) | Ground +0x10 | child-sprite pass as Cloud, plus the terrain-mesh pass: N=(+0x70-+0x68)/8 points, allocates 8*N + 4*N, fills an index buffer 0..N-1, `vec_rotate` per point, then emits triangles into the queued sprite record (colour 0xff000000) and `Hud_DrawQueuedSprite` |
| 0x1402f4140 | `Ground_IsInLandpartList` | 8 | Ground +0x30 | `return *(byte*)(this+0x98)`; +0x98 is 0 in all four `Ground` inline ctors and becomes 1 only at 0x1402f18cb, right after the object is appended to the shared list `0x148021c70` and given its index at +0x8 |

Creation protocol: request posted to the blackboard at 15:50, one full cycle
waited (no objection), functions created at ~16:01 through `create_function`
(body sizes confirmed: 70 / 6 / 533 / 731 / 1653 / 8). Names are accepted with
only the usual PascalCase/verb validator warnings that every `Class_VerbObject`
name in this project gets. Plates follow summary / `Algorithm:` / `Parameters:`
/ `Returns:`.

## Still missing function objects (reported, not created — outside the six)

The same three tables contain three more entries with code and no function
object, which batch-9's list did not include. They were **not** created here
because they were not in the posted request:

* **0x140316b30** — Cloud +0x28. Per-frame scroll of the cloud: moves +0xc by
  `+0x60 * (+0x60? scale constant)` and wraps/clamps against
  `0x1403c2b6c * 0.5 * +0x38`; Landpart/Ground use the empty stub instead.
  A `Cloud_Update`-style body. Reproduce after a creation post.
* **0x1402eb540** — Ground deleting destructor (stores `0x1403770e8` into
  `*this` and frees the +0x68 vector through 0x1403340d0). Landpart/Cloud
  destructors have objects, Ground's does not.
* **0x1400055c0** — the shared `XOR AL,AL; RET` virtual used at Landpart +0x30
  and Cloud +0x30 (returns false). It has dozens of other vtable users, so it is
  a generic "always false" stub rather than a Landpart-specific body.

## Cross-references for other agents

* **`0x1402f47e0` is Ground +0x18** (vtable `0x1403770e8`), i.e. the exact
  counterpart of the new `Cloud_BuildDrawList`, but it is named
  **`Hud_TransformMarkerToScreen`**. Its prologue and field use (+0xc, +0x38,
  +0x44, +0x60, +0x18/+0x20 child vector, +0x58/+0x5c) are identical to
  `Ground_DrawSprites`/`Cloud_BuildDrawList`, so the HUD-marker name looks wrong.
  It is a *rename* candidate for whoever owns named functions — not touched here.
* **`0x14004bed0`** (Body +0x238) is still labelled `handleAmmoInBattle?`; it is
  the Body draw pass (both `Gui_BootTitlePass` +0x240 calls land there through
  the new trampoline analysis). Same rename-candidate class.
* **`0x1402f6910`** (Ground +0x20, 483 B) is still `rep_...sinf`; it is a real
  Ground virtual (only Cloud leaves +0x20 as the empty stub), so it deserves a
  `Ground_*` name once its role is read.
* `Landpart`/`Cloud`/`Ground` layouts as in batch 9 agent 9 plus: +0x98 byte on
  Ground = "registered in the 0x148021c70 list"; +0x68/+0x70 = terrain point
  vector; +0x90/+0x94 = child-scale blend inputs; +0x60 = rotation phase
  (Cloud 0, Ground set by `Ground_SetSpawnParams`'s param9).

## Tool notes

* `search_functions` / `search_functions_enhanced` silently return 0 results
  unless `program` is passed explicitly, even after `switch_program`.
* `disassemble_bytes` needs `start_address` (not `address`); `set_plate_comment`
  needs `address` (not `function_address`).
* `batch_decompile` cannot decompile an address without a function object — the
  six slot bodies had to be read from `disassemble_bytes` listings first.
* The `.pdata` block for this binary carries multiple chained `RUNTIME_FUNCTION`
  entries per large function (e.g. 0x1402f4d90 has entries at +0x0, +0x29,
  +0x194, +0x2f7, …), so `end - begin` of one record is not the function size;
  use `RET` + `INT3 INT3` padding instead.
