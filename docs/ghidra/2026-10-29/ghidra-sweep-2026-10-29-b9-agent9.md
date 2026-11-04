# Ghidra sweep 2026-10-29 — batch 9, agent 9 (last unplated `FUN_*`)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `FUN_*` with an empty plate comment, minus the addresses in
`funclet-ownership-2026-10-29.tsv` (agents 1–3) and minus agent 8's 31 `.rdata`
creations + `0x14004c7e0`.

**Start: 110 unplated `FUN_*`; 54 in scope.** The other 56 are 54 TSV owner /
funclet rows plus the 2 reserved by agent 8. **End: 5 renamed + plated, 49
skipped and recorded below.** Nothing was created; no `save_program`, tags,
README/STATUS edit or commit.

## Method: MSVC RTTI → real class names

The decisive new tool for this pass was the RTTI graph. 247 MSVC
`CompleteObjectLocator`s exist; each is reachable as the qword just before its
vtable. Resolving `COL+0xc` → `TypeDescriptor+0x10` gives the mangled class
name, and `COL+0x10` → `ClassHierarchyDescriptor+0xc` → base-class array gives
the bases. This produced the real class names used below and is worth reusing
by later passes; the class of any function that stores a vtable pointer (ctor)
or occupies a vtable slot can be proven this way.

Result relevant to this region:

| class | vtable | bases |
|---|---|---|
| `?AVLandpart@@` | `0x140377060` | — |
| `?AVCloud@@` | `0x1403770a0` | `Landpart` |
| `?AVGround@@` | `0x1403770e8` | `Landpart` |
| `?AVtype_info@@` | `0x140378f08` | — |

`Cloud`/`Ground` are the landscape decoration types built and spawned by
`generateCityLandscape` 0x1402eeb90 and `playCloudByDistance_` 0x1402ee5f0.
`Landpart` has 7 slots (0x0–0x30); both derived tables append their own slots,
so `+0x38` is a `Cloud`/`Ground`-only virtual.

## Renamed and plated (5)

| addr | new name | proof |
|---|---|---|
| 0x1403340d8 | `type_info_ScalarDeletingDestructor` | vtable `?AVtype_info@@` 0x140378f08 slot 0 (COL 0x140381718). Body stores that vtable into `*this`, then `if (dl & 1) operator delete(this, 0x18)`; 0x18 is `sizeof(type_info)`. Same naming convention as `std_exception_ScalarDeletingDestructor` etc. |
| 0x1403160a0 | `Cloud_SetSpawnParams` | `?AVCloud@@` vtable 0x1403770a0 slot `+0x38`. Stores the spawn block: +0xc = x, +0x10 = y, +0x30 = param4, +0x34 = param5 (the 15/30/60 s cloud lifetime chosen by `playCloudByDistance_`), +0x38 = param6, +0x3c = (int)param7, +0x44 = param8, +0x48 = 999, +0x60 = param9. Sole call site 0x1402ee5f0 right after the inline 0x68-byte ctor. |
| 0x1403160f0 | `Ground_SetSpawnParams` | `?AVGround@@` vtable 0x1403770e8 slot `+0x38`. Same block, but +0x48 = (int)param10 and +0x4c = param11 instead of 999. Called from `generateCityLandscape` 0x1402eeb90 for the 0xa0-byte `Ground` decorations. |
| 0x1400e85a0 | `Vector18_DestroyRangeThunk` | arg-permuting thunk `(RCX,RDX,R8) -> (RDX,R8,RCX)` + `JMP 0x1400df3c0`. That target loops `param_1 += 3` qwords (0x18 stride), frees `*elem` and zeroes the three pointer fields — a 0x18-byte element range destructor. Callers are compiler cleanups only (0x14033cec0, 0x14033cf0a). |
| 0x14028b340 | `Vector64_DestroyRangeThunk` | same permutation + `JMP VectorStride64_DestroyRange` 0x140287730 (plated: destroys 0x40-byte elements). Sole caller is a cleanup at 0x140346c8d. |

## Skipped and recorded (49)

### Compiler artefacts / not independent functions (5)
* **0x140118699** (7) — seven `INT3` bytes decoded as a function; padding.
* **0x14019ae0f / 0x14019ae66 / 0x14019ae94** (50/46/16) — split halves of the
  `CopyEscadraName` 0x20-stride loop and its empty tail; not independent bodies.
* **0x1403368e0, 0x140336c40, 0x140336d90, 0x140336dc0, 0x140336e30, 0x140336e70,
  0x140336f50** (39–58) — the 13 `/EH` funclets agent 8 handed to agent 1.
  They are absent from `funclet-ownership-2026-10-29.tsv`, but they sit in
  agent 1's `0x140336730–0x14033FFFF` range, so they are **reported, not
  renamed here**. (Note: agent 8's hand-off lists 7 addresses but says "13
  funclets" and shows a 7-address list — the TSV still has none of them.)

### `__scrt_*` / CRT outline stubs (7) — no MSVC symbol provable
Same conclusion as batches 5–8; renaming them "ReturnOne"/"Zero…" would be
behavioural noise, and the token set would collide with the existing
`AlwaysReturn1` 0x1400055d0. Bytes re-read this pass:
* **0x14033503c** (6) — `MOV EAX,1; RET`.
* **0x140335050** (8) — `AND dword [0x1480771ec],0; RET`.
* **0x140335354** (6) — `MOV EAX,0x4000; RET` (`_O_TEXT`).
* **0x14033536c** (27) — ORs `0x24` into `[0x140011000()]` and `0x2` into
  `[0x14011bbc0()]` (stdio `_flag` outlines).
* **0x140335388** (12) — `return *(int*)0x1403c2e68 == 0`.
* **0x140335394** (8) / **0x14033539c** (8) — `LEA RAX,[0x148077208]` /
  `[0x148077200]; RET`.
No `.pdata`-only or xref-free evidence ties them to a named CRT function.

### Small predicates / accessors whose fields stay unidentified (12)
* **0x140073340** (26) — `if (+0x48 != 0 && 40.0 <= +0x15f8) RET; else XOR AL,AL`.
  The "true" path never sets AL, so the return value is the low byte of `this`.
  Called from Body_Explode, BulletImpact?, World_ThermalPass, FX_SpawnCloudPuff
  and five more. Behaviour is proven, intent is not; naming it after the
  predicate would misdescribe the result. (Re-confirms batch 8.)
* **0x140073530** (38) — `if (p=this+0x48) { (*(*p+0x48))(p); this+0x48=0; }`.
  `+0x48` is a state int on Body but a child pointer here; class unknown.
* **0x140083d60** (5) — `return *(byte*)(this+0x10)`. Sole caller
  `handleAmmoInBattle?` passes the media-array global `ArrayLoadedByMedia_res`;
  the flag's writer is unknown.
* **0x1400a6210** (24) — `+0xf8 == 0 && +0xf6 != 0`; caller
  `Dialog_ExecuteChoiceActions` guards the "ANYTIME" branch with it. The
  object comes from a string-parsing helper (0x1400a39e0), not from a proven
  `Profile`/`Creature` class, and neither byte is documented.
* **0x140049cd0** (35) — `if (int(+0x2e8) < arg) return 0; return float(+0x248) != 0`.
  Callers pass arg 2 from `creatureLogic`, `mainDialogWithChoices`, `!ClickFunc`;
  neither field is identified. Class not proven.
* **0x140092e70** (44) — releases `this[7]` through vtable `+0x20` with the
  not-self flag, then clears it. Container element type unknown.
* **0x1400fdec0** (61) — clears +0x1d0, word +0x1a4, +0x1b8 and the std::string
  at +0x1a8/+0x1c0/+0x1c8. Caller is the radio/tutorial trigger evaluator
  0x140238460 (stale `sqrtf` label); the record type is not proven.
* **0x1400f51c0** (52) — `vtable+0x1d0` of `[[[this+0x288]+0x10]+0x50]`, or 1.0;
  used as a screen-offset scale by `VideoTask_RenderMapScene` and
  `FUN_14015f0d0`. Nested object unidentified.
* **0x1400bee20** (58) — zeroes +0x128 on every element of the `+0x8c0` vector
  whose byte +0x71 is set; only caller `rep_14017a420_New` 0x140185ff0.
* **0x1400f8da0** (12) — `JMP somethingSpawnShips(*(this+0x520))`; owner class
  unknown.
* **0x14018f910** (36) — locale-facet decref through vtable `+0x10` of a facet
  found by id; owning facet class unknown, `.pdata` only.
* **0x1401941f0** (40) — `if (this+0x58) return 0x140280fa0(this+0x58, this) != 0`;
  the callee is still a stale `rep_*` body.

### Setters / record initialisers with no proven owner type (8)
* **0x14016dde0 / 0x14016ddf0** (9/7) — one-store setters
  (`MOVSS [RCX+0x1a4],XMM1`; `MOV [RCX+0x1a0],EDX`). Callers are
  `TextGrid_LayoutProjected` / `TextGrid_LayoutLocal` / `TextGrid_CreateObject`,
  but the written object is the **loop element**, not the TextGrid, so the
  element type is unknown.
* **0x140088950** (21) — 0x28-byte record init `[0]=arg; [1]=[3]=[4]=0`; used
  inline in `CSGlitch_Constructor` and
  `ShaderDeferringCloseAndPrebloom_Constructor`; record type unproven.
* **0x1401a4210** (60) — 0x20-byte record ctor (qword + 7 dwords) inlined in
  `displayCityOnMap` and a CRT twin; type unknown.
* **0x1401a47f0** (22) — 0x18-byte record ctor inside `memmoveMAIN`; type unknown.
* **0x1401a4b40** (57) — frees `*(this+8)+0x20` via 0x1401a5090 then
  `operator delete(*(this+8), 0xa0)`; no caller, no owner type.
* **0x14012b4f0** (220) — ctor of a 0x118-byte stack record in `lootBoxCoins`
  (draw-list/coin record); owning type not proven.
* **0x1401783c0** (988) — compiler-generated struct copy in the HGE media
  layer; type unknown (batch-3 verdict re-confirmed).
* **0x140092e70** listed above.

### Dispatch / wrappers (6)
* **0x140017d10** (36) — virtual dispatch through a doubly-indirect table; no
  code xref (`.pdata` only).
* **0x140027f90** (120) — walks a Body slot vector (`+0x350/+0x358`) and calls a
  stale `rep_..._MakeGlobal?` on `element+0x58`; callee unproven.
* **0x14016cf30** (22) — calls slot 0 of the `newValidHGE` singleton; the slot's
  meaning (HGE slot 0 is not Release in `HGEVFTABLE`) is unproven.
* **0x140170210** (24) — `if (p) return (*(*p+8))(p, this)`; only callers are in
  `rep_..._WriteToClientLog`. Object and slot semantics unproven.
* **0x14010f1a0** (69) — trims the `0x1403ef580` global vector through
  0x1400d9a10 (stale label) and copies `DAT_1403ef578` -> `DAT_1403ef57c`.
* **0x1401102c0** (117) — picks state 5 vs 7 from
  `dist*1000/+0x494 < 7200` and calls a stale `rep_14010b1e0_MakeGlobal_`;
  the 5/7 meaning is still unresolved (batch 4/6/7/8 all left it).

### Rendering / HUD helpers with unproven object identity (4)
* **0x1403161a0** (132) — writes `_DAT_148075d50/_d54 = (param1, param2)`, indexes
  the vector-of-vectors `0x14801dd00` (0x18 stride) and, if the record is
  non-empty, calls `FUN_140316a50(rec+0x38, rec+0x44)`. Sole real caller is
  `Gui_FlushDrawList` (with (0x3b, 0)); the record type is unproven.
* **0x140316a50** (213) — applies `pow(param1, param2)`, feeds the result to
  `compareAndUpdateFloatArray_` on the five media globals at
  `0x143a13968/958/960/978/970` (+0x128/+0x130/+0x1b0) and sets
  `Property_SetFloat(*(0x143a13970+0x138), 1.0 or 0.0)` from
  `ZOOM_LEVEL*0.142857 > 0.4`. Callers: `Hud_MarkerRenderLayer*`,
  `Sprite_GetMinDimension`, every `VideoTask_Render*Scene`.
* **0x140316d00** (274) — per-frame update of a list owned by the media global
  `0x143a13950` (assigned in `Init_HGE` from `ArrayLoadedByMedia_res`): advances
  each 0x38-byte element's +0x2c by `*list * time_related_global_` and frees
  expired/flagged elements via `ReassignLinkNode`/`freeLinkMemory_`. Called by
  all four `VideoTask_Render*Scene`.
* **0x1400bc5c0** (32) — `if (!IsInEditor) return 0; <call 0x1400c12a0>; return 1`.
  Only caller `Input_HandleMouseMove` (return value ignored). 0x1400c12a0 is a
  3236-byte editor pass (collects all bodies, dedups by +0xb8, undo stack,
  `Body_IsMountedOrPaired`), so the wrapper's exact responsibility is not proven.

### Large editor body (1)
* **0x1400458c0** (3342) — editor "collect and lay out the selected ship's
  mounted parts" pass; body > 0x2000 and references the `?AVLink@@` vtable
  0x140352310; product list still not pinned (batch 8 verdict kept).

## Out-of-scope wrong names found (report, do not rename)

`rep_*` owners should look at these; they were renamed by label propagation in
earlier batch-1 passes and the bodies disprove them:

* **0x1400c12a0** — labelled
  `rep_1400bc6b0_..._invalid_parameter_noinfo_noreturn` but is a real 3236-byte
  editor routine (body collection, undo stack, mounting checks). Same for the
  2076-byte `rep_14017a420_New` 0x140185ff0 and the 2567-byte radio-trigger
  evaluator 0x140238460 labelled `...sqrtf`.
* **0x1400df3c0** — labelled
  `rep_1400d9d70_..._invalid_parameter_noinfo_noreturn`; body is a 0x18-byte
  element range destructor (free + zero three fields).
* Missing function objects at `0x1402f4b70`, `0x1402f4500`, `0x1402f4140`,
  `0x1402f4d90`, `0x140316150`, `0x1403365ac` — all are `Cloud`/`Ground`/
  `Landpart` vtable slots with executable code but no function object. Not in
  this scope (not `FUN_*`); whoever creates `.text` functions should handle them.

## New structure facts for agent 10

* `Landpart` (base of `Cloud`/`Ground`) vtable 0x140377060: slot 0 dtor,
  +0x8, +0x10, +0x18/+0x20 (two copies of the same body 0x1403365ac),
  +0x28 guard, +0x30.
* `Cloud` 0x1403770a0 adds +0x10, +0x18, +0x28, +0x30 and **+0x38 new virtual
  = `Cloud_SetSpawnParams`**.
* `Ground` 0x1403770e8 adds the same slots; **+0x38 = `Ground_SetSpawnParams`**.
* Cloud/Ground spawn object layout used by `playCloudByDistance_` /
  `generateCityLandscape`: Cloud 0x68 / Ground 0xa0; +0x0 vtable,
  +0x8 index, +0xc x, +0x10 y, +0x18/+0x20/+0x28 child sprite vector,
  +0x30..+0x3c spawn params, +0x44 scale, +0x48 timer (999 default int64),
  +0x50 -1.0, +0x54 word flags, +0x58 = 2, +0x5c = 0.5, +0x60 param.
* `type_info` vtable 0x140378f08, COL 0x140381718.
