# Unnamed-function sweep — batch 7 agent 9 (real `FUN_*` set B)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: real `FUN_*` only (no `rep_*`, no `/EH` funclets) in

1. `0x140200000–0x140336FFF`, minus everything in
   `funclet-ownership-2026-10-29.tsv`;
2. `0x140000000–0x14006FFFF` (CRT helpers left over from batch 6);
3. `0x140350000–0x140350510`, minus the funclet map.

Counts: **8 renamed + plated, 0 created, 19 skipped/recorded** (32 addresses
including the 13 funclets that are outside my role).
Start census (script `FUN_*` with function objects): 10 in range 1, 5 in
range 2, 5 in range 3 (20 real ones), plus 13 `/EH` funclets
`0x140336730–0x140336f50` that fall below `0x140337000` but belong to
agent 1's funclet role, plus 7 `__scrt_*` stubs. After the pass range 3 has
**0** `FUN_*`; ranges 1 and 2 keep the addresses listed under "Skipped".

## Renamed (8)

| addr | old | new | evidence |
|---|---|---|---|
| 0x14000ad80 | `FUN_14000ad80` | `Body_HasOid` | `CMP dword [RCX+0x190],0; SETNZ AL; RET`. `+0x190` is the first field of Body `m_oid` (MSVC `std::string`, data-or-SSO buffer; `+0x1a0` length, `+0x1a8` capacity — `docs/structures.md`). SSO → first four characters; heap string → data pointer (always true). Only caller `Projectile_DetonateOnImpulse` 0x14001d2e1, on the Body at `projectile+0xa20`, skipping the detonation branch on true. |
| 0x140268a30 | `FUN_140268a30` | `String_ReplaceAll` | Replace-all loop: `pos = 0x1401a1b30(dest, dest.len, searchFrom, needle, needle.len)` (memchr+memcmp substring find, returns `-1` on miss), then `0x14024bd90(dest, pos, needle.len, repl, repl.len)` = MSVC `std::string::replace` (verified: it is the `_Replace`/`replace` body that throws on `pos > size`), then `searchFrom += repl.len`. All three args are `std::string` (data/len/cap at +0/+8/+0x10, SSO when cap < 0x10). Callers `mainDialogWithChoices` 0x1400afc04 and 0x1400afc3f, each on a temp built by `copyIntoEscadraName?` 0x140015390 from literals 0x14035a4e8 / 0x14035a4f4 / 0x14035a4f8, result then passed to `String_Tidy`. |
| 0x14021fdb0 | `FUN_14021fdb0` | `Body_SubtreeEqualsControlledNode` | Gates on `DAT_143a13a78` (global controlled node) and its arg, derives a Body from `node->[0x100]->[0]->[0x10]+0xb8`, then returns `0x14021fe10(body, arg)`. That callee rebuilds both subtree link lists (`Body_RebuildSubtreeList`), drops `0x38e`-tagged entries, compares counts and finally `__RTDynamicCast`, returning 1 only when the two lists match. Sole caller `!ClickFunc` 0x14013a845: `Profile_GetFirstPlayerCreature(Get_Profile())` → this → if true `Shipworks_CommitDesignAsControlledShip(R12, 0)`. |
| 0x140350030 | `FUN_140350030` | `DtorGlobal_Container_148021c88` | `atexit`-registered (thunk 0x140004960 → `JMP 0x14033447c` = `atexit`) teardown of the global vector at `0x148021c88`: byteLen `(cap-ptr) & ~3`, sized-delete header check, `operator delete` 0x1403340d0, zero ptr/size/cap. Read by `generateCityLandscape` 0x1402f196d/0x1402f1997/0x1402f1f58 and `LoadParticle?` 0x1401b9f07. |
| 0x140350260 | `FUN_140350260` | `DtorGlobal_Container_148075cb0` | Same shape, `& ~0xf` → element size 16, global `0x148075cb0`; registered by thunk 0x1400049b0. No other reader of the global. |
| 0x140350480 | `FUN_140350480` | `DtorGlobal_Container_14801dcd0` | Same shape, `& ~7` → element size 8, global `0x14801dcd0`; registered by thunk 0x140004a30. No other reader of the global. |
| 0x1403504f0 | `FUN_1403504f0` | `CInit_b2ContactFilter` | `DAT_1403c2e10 = 0x140369200` (vtable whose slot 0 is `b2ContactFilter_DeletingDtor` 0x1401a8480). `b2ContactManager_Construct` 0x140321d60 stores `&DAT_1403c2e10` into `m_contactFilter` (+0x68) of every contact manager. Called from the C-init slot 0x140004a40. |
| 0x140350500 | `FUN_140350500` | `CInit_b2ContactListener` | `DAT_1403c2e18 = 0x140369218` (`b2ContactListener_DeletingDtor` 0x1401a84b0); stored into `m_contactListener` (+0x70) by the same constructor. Called from C-init slot 0x140004a50. |

Naming conventions kept: `DtorGlobal_Container_<addr>` for anonymous vector
globals, matching agent 5's batch-7 tail convention (agent 5 renamed 75
`rep_*` twins in 0x14034ba30–0x140350410 and named 40 anonymous vectors
`DtorGlobal_Container_<addr>`; my three are the `FUN_*` members of that same
family inside `0x140350000–0x140350510`). Agent 6's `CInit_Atexit_<Tag>` map
then strips `DtorGlobal_` to a clean tag. `CInit_<Global>` for the two
vtable-installation initialisers.

## Correction for agent 6's C-init map

`/tmp/opencode/hf_ghidra_sweep/cinit_names.tsv` classifies **0x140004a40 and
0x140004a50 as `CInit_Atexit_*`**. They are not atexit calls: both thunks are

```
LEA RAX,[0x140369200] / MOV [0x1403c2e10],RAX / RET   (0x140004a40)
LEA RAX,[0x140369218] / MOV [0x1403c2e18],RAX / RET   (0x140004a50)
```

i.e. plain vtable installers (their targets now carry `CInit_b2ContactFilter`
and `CInit_b2ContactListener`). Same for `0x140004960/0x1400049b0/0x140004a30`
(they *are* `LEA RCX,[dtor]; JMP atexit`, targets renamed here). Agent 6 may
want to reclassify those two rows.

## Skipped and recorded

| addr | size | why |
|---|---|---|
| 0x140017d10 | 36 | Virtual dispatch through a doubly-indirect table, **no code xref** (only `.pdata` 0x14807905c). Batch-6 verdict re-confirmed. |
| 0x140027f90 | 120 | Iterates the `+0x350/+0x358` pointer vector and calls `rep_1402b1a80_MakeGlobal?` on `element+0x58`; element class and "MakeGlobal" meaning unproven (label untrusted). |
| 0x1400458c0 | 3342 | Editor "collect and lay out selected ship's mounted parts" pass (`Editor_RebuildGlobalLinkLists` 0x14018c474, `sqrtf`, RbTree inserts, `Link_ConstructFromBody`, `Frame_ClassifyPartMix`). Product (repair list vs layout list) still not pinned down. |
| 0x140049cd0 | 35 | `int(this+0x2e8) < arg → 0; else float(this+0x248) != 0`. Neither field identified (Body +0x2e8 has no entry in `structures.md`; +0x248 is `count` only for Missile). |
| 0x14028b340 | 20 | Tail-call adapter: `(rcx,rdx,r8) → (rcx=rdx, rdx=r8, r8=rcx)` then `JMP 0x140287730`, which is a per-element `pointer+size+cap` free loop over a 0x20-stride array (vector-of-strings teardown). Called from the /EH region at 0x140346c8d with `[obj+0x88],[obj+0x20],[obj+0x70]`. Compiler-generated member-array destructor; no symbol is provable. |
| 0x1403160a0, 0x1403160f0 | 75 / 81 | City/cloud descriptor field setters (store 9 resp. 11 scalars at +0xc/+0x10/+0x30..+0x60, `+0x48 = 999` default). Callers `playCloudByDistance?` and `generateCityLandscape`; owning record type still unidentified (record tables 0x1403770d8 / 0x140377120). |
| 0x1403161a0 | 132 | `Gui_FlushDrawList` call: stamps `DAT_148075d50/d54` with the (index) pair, bounds-checks `DAT_14801dd00` (0x18-stride vector array) and the 100-column dword grid `DAT_14800f210`, then forwards `record[+0x38]/[+0x44]` to 0x140316a50. Deferred draw-list command; the visual effect is not provable. |
| 0x140316a50 | 213 | **New detail**: builds a 4-float lighting colour via 0x1402f3fd0 (`x/20`, clamp, `powf(t/12-1,2)`, `pow(1-x,12)` → `{t, brightness, darkness, 1.0}`), pushes it with `compareAndUpdateFloatArray_` 0x1400a04e0 into five environment objects (`0x143a13968+0x128`, `0x143a13958+0x130`, `0x143a13960+0x1b0`, `0x143a13978+0x130`, `0x143a13970+0x130`) and sets a `ZOOM_LEVEL`-dependent property (`0x143a13970+0x138`). Looks like a time-of-day/sky ramp, but the five objects are still unidentified, so no name. |
| 0x140316d00 | 274 | Ages 0x38-stride entries by `time_related_global_ * dt`, drops entries whose end time passed / `-1.0` sentinel / dead with null link, compacting the vector. Reached from `World_Render` and several render functions; the entry type is unidentified. |
| 0x140319da0 | 3 | Shared empty destructor / `_guard_check_icall` body; called by `SuperBigDeconstructor` and `b2World_DestroyBody`. Leave. |
| 0x1403340d8 | 43 | Scalar deleting destructor; `0x140378f08` is a name→pointer record table, not a vtable. Class not provable. |
| 0x14033503c, 0x140335050, 0x140335354, 0x14033536c, 0x140335388, 0x140335394, 0x14033539c | 6–27 | `__scrt_*` outline stubs used only by the `_set_app_type` worker 0x140334b70 (`mov eax,1; ret`; zero `DAT_1480771ec`; `_O_TEXT` 0x4000; scrt flag stores; `DAT_1403c2e68==0`; `&DAT_148077208`; `&DAT_148077200`). No MSVC symbol provable (batches 5 and 6 reached the same conclusion). |
| 0x140336730 … 0x140336f50 (13) | 29–65 | `/EH` cleanup funclets. They sit just below 0x140337000 and are absent from the ownership TSV (which starts at 0x1403372d0), but they are funclets ⇒ agent 1's role, not touched. **Hand-off: agent 1 should add these 13 to the funclet map** (they are the tail of the same `/EH` block; batch-6 agent 9 already flagged them). |

## End-of-pass census

* `0x140200000–0x140336FFF`: 28 `FUN_*` left — 5 render helpers
  (0x1403160a0/0f0/1a0/a50/d00), 0x140319da0, 0x1403340d8, the 7 `__scrt_*`
  stubs, the 13 `/EH` funclets, and 0x14028b340.
* `0x140000000–0x14006FFFF`: 4 left — 0x140017d10, 0x140027f90, 0x1400458c0,
  0x140049cd0 (all pre-existing skips; the CRT C-init table is agent 6's).
* `0x140350000–0x140350510`: **0** left (`0x140350030/260/480/4f0/500` all
  named here; the 68 `FUN_*` in agent 5's 0x14034b850–0x140350410 tail list
  that lie below 0x140350000 stay for agent 8).

## Open items handed to the parent

1. The 13 `/EH` funclets at 0x140336730–0x140336f50 are outside the ownership
   TSV; they need owner mapping (agent 1).
2. `0x1402f3fd0` (currently mislabelled `rep_..._pow`, real callee of
   0x140316a50) is a lighting/colour ramp `(out[4], dayFrac0..1, hours0..12)`
   and is the key to naming the five environment objects behind
   `0x143a13958…0x143a13978`.
3. `0x14021fe10` (mislabelled `rep_..._free`) is the subtree-list equality
   routine behind `Body_SubtreeEqualsControlledNode`; it deserves its own
   `rep_` re-match (agent 4, range 0x140200000–0x140336FFF).
