# Ghidra changes, 2026-10-30 (post-sweep: classification, funclets, family naming)

Program: `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`),
image base `0x140000000`. Follows the ten-wave sweep in
[ghidra-changes-2026-10-29.md](ghidra-changes-2026-10-29.md) and implements
[../plans/2026-10-29-post-sweep-plan.md](../plans/2026-10-29-post-sweep-plan.md)
phases 0–2.

## Result

| metric | before (batch 10) | after |
|---|---:|---:|
| function objects | 5,430 | **5,432** |
| named | 4,502 (82.91%) | **4,639 (85.40%)** |
| unnamed | 928 | **793** |
| — `FUN_*` | 80 | **59** |
| — `rep_*` | 848 | **734** |

+137 named (135 renames + 2 created functions). Every rename carries a
doc-style plate (summary / `Algorithm:` / `Parameters:` / `Returns:`); an
independent plate audit of all 493 names quoted in the agent notes found 30
unplated, of which 17 were P2e's renames — those were plated in a follow-up
and re-verified 17/17. The other 13 are pre-existing functions (link helpers,
CRT imports) that never had plates.

## Phase 0 — classification (1 agent)

All 928 unnamed functions fingerprinted from listing/callee/string/`.rdata`
metadata (no decompilation of the set) into
[unnamed-classification-2026-10-30.tsv](unnamed-classification-2026-10-30.tsv):

| verdict | count |
|---|---:|
| `needs structures` | 457 |
| `CRT noise` | 347 |
| `nameable` | 94 |
| `ambiguous` | 30 |

Report: [../findings/unnamed-classification-2026-10-30.md](../findings/unnamed-classification-2026-10-30.md).
The 94 nameable rows were split into families and handed to Phase 2; the 457
`needs structures` rows became the P2e field-map backlog.

**Known limit:** the classifier's `stride` column was wrong for most container
rows (real sizes 0x10/0x18/0x20/0x30/0x40/0x50/0x70/0x100, not 0x3–0x8). Every
Phase-2 rename re-proved the stride from the allocation immediate and index
scale; the column should be treated as a hint only.

## Phase 1a — funclet owner walk (1 agent)

Method: the binary uses **`__CxxFrameHandler4`**; there is no `0x19930520`
magic anywhere. The walk is
`.pdata → UNWIND_INFO(EHANDLER) → handler-data FuncInfo4 → header → compressed
UnwindMap / TryBlockMap`, with type-3 unwind actions and handler
`dispOfHandler`/continuations as the funclet set. All four handler RVAs
(`0x334494`, `0x334510`, `0x336594`, `0x3365ca`) share the FH4 encoding.

| result | count |
|---|---:|
| funclets closed | **20** (18 renamed, 2 created) |
| owners renamed | **17** |
| still open | **17** |

`0x140342380` was the hard case: the recorded owner `0x1403423c0` is a catch
funclet; the chain `0x140342380 ← 0x1403423c0 ← 0x14019abe0` resolves the root
to `VectorString32_InsertRange`, so the funclet is
`VectorString32_InsertRange_EhCleanup_0xa0_2`.

The 17 open have recorded reasons: 7 shared ICF catch funclets referenced by
2–3 parents (naming after one would be wrong), `0x1403377e0` (Body vtable slot
81, slot order does not prove a name), 2 editor/map tick steps, 3 tutorial
cascade steps, 1 refuel-partner eval, 1 location-map draw step, 2 FX spawners
whose effect is a runtime parameter.

`funclet-ownership-2026-10-29.tsv` gained a trailing `status` column
(20 `closed`, 3 `closed_p1b`, 17 `open`, 894 blank) and 8 missing rows.

## Phase 1b — CRT EH glue / `__scrt_*` (1 agent)

| address | name | proof |
|---|---|---|
| `0x14034b6b8` | `` `eh_vector_destructor_iterator'_EhCleanup_0x60 `` | `.pdata` handler of the C-scope inside `eh_vector_destructor_iterator`; guarded `__ArrayUnwind` over that function's argument homes |
| `0x14034b743` | `CRT_AccessViolationFilter` | AV filter of `__scrt_is_nonwritable_in_current_image`; `return ExceptionCode == 0xC0000005` |
| `0x14034b75b` | `CRT_SehFilterExeThunk` | filter of `mainCRTStartup`'s `__try/__except`; forwards `(code, ep)` to `_seh_filter_exe`; no twin (pattern occurs once) |

The seven `__scrt_*` outlines (`0x14033503c/050/354/36c/388/394/39c`) were
classified as compiler outlines with their callers recorded, not renamed.
New semantics facts: `0x148077208` is the `__dyn_tls_init` callback slot and
`0x148077200` the thread-local atexit callback slot.

## Phase 2 — family naming (5 agents)

| agent | family | renamed | skipped |
|---|---|---:|---:|
| A | shader / HUD destructor wrappers | 15 | 13 |
| B | alloc / stride families | 29 | 2 |
| C | red-black-tree families | 12 | 6 |
| D | vector / constructor / destructor families | 22 | 11 (+7 excluded) |
| E | `needs structures` subsystem bodies | 17 | 302 |

### A — the "ShaderData wrappers" were constant buffers

The 14 `wrapper_of_ShaderData_ResetVTable` rows are **not** shader-class
destructors: each is slot 1 of a `ConstantBuffer<…>` vtable, resolved through
xref → COL → `pTypeDescriptor` (`.?AV?$ConstantBuffer@…@@@@`). Nine are
single-owner (`EffectMatrixConstantBuffer_…`,
`ShaderBackgroundConstantBuffer_…`,
`ShaderDeferringFarPrerendered{,Vertex,Shading}ConstantBuffer_…`,
`ShaderGlitchConstantBuffer3_…`, `ShaderLighting{,Map}ConstantBuffer_…`,
`ShaderPostConstantBuffer_…`); five are MSVC ICF folds serving 2–9
instantiations and are named `ConstantBuffer_ScalarDeletingDestructor_SharedA–E`
with every owning vtable listed in the plate. `ShaderData_ResetVTable` is only
the base teardown; instances come from `ShaderX_Init` via
`ShaderData_Constructor`. Also `0x1402ebb20` → `Ground_SpawnAlongPath`.

### B — vectors, lists and hash maps

`VectorStride16_InsertValue{,_2,_3,_4}`, `VectorStride16_Reallocate`,
`VectorStride32_InsertValue/_InsertDefault`, `VectorStride64_Reallocate`,
`VectorStride80_Reallocate`, `VectorStride24_FillCopy`,
`VectorStride48_InsertCopy/_InsertMove`, `AllocArrayStride16{,_2}/32/80`,
`Array_AllocAligned`. The `alloc_stride0x18_candidate` family is not vectors:
8 rows are `std::list` 0x18-node inserts (`List_PushBackNode24*`), plus
`HashMap_InsertU64Key`, `HashMap_InsertStringPairKey`,
`HashMap_InsertStringKeyAlt`, `List_AppendObject240`,
`List_FindOrAppendNode80`.

### C — red-black trees

Node layout proved from the stores (`+0` left, `+8` right, `+0x10` parent,
`+0x18` colour, `+0x19` isnil): `RbTreeStride64_ConstructNode` +
`_ConstructNodeAlt` + `_ConstructNodeEscadraKey{Alt}`,
`RbTreeStride40_ConstructNode/_ReassignKey/_ReassignKeyGuarded`,
`RbTreeStride48_ConstructNode`, `RbTreeStride72_ConstructNode/_InsertRange`,
`RbTreeStride104_ConstructNode/_EmplaceShader`.

Correction: `0x14009c270`'s `New(0x40)` is the `VShader` value object; the tree
node is `New(0x68)`, so it belongs to the stride-104 family. The two
`container_sort_helper_stride0x18` rows are `std::list` node merge-sort drivers
with the comparator inlined — there is no callable sort helper to name.

Naming convention: the number is the **decimal byte size** of the element or
node (`RbTreeStride64` = 0x40, `VectorStride48` = 0x30).

### D — vectors, pairs, destructors

`String_AssignCopy`, `LinkedList_DestroyFreeHeader`, `LinkedList_ClearFreeChain`,
`RbTree_ClearFreeResetHeader`, `ListStride24_PushBack`,
`VectorStride64_InsertStringPair`, `VectorStride3_AppendRotatedTriples`,
`Stride72_CopyConstructor`, `IntStringPair_CopyConstructor`,
`PointerStringPair_CopyConstructor`, `StringIntPair_CopyConstructor`,
`PlaneLoadout_NamedEntry_Destructor`, `FileOStream_ScalarDeletingDestructor`,
`HGE_ScalarDeletingDestructor`, `VideoTask_ScalarDeletingDestructor`,
`Profiler_ScalarDeletingDestructor`, `Profiler_Singleton_ScalarDeletingDestructor`,
`Effect_AddTextureVectorParam`, `Escadra_GetOrCreateIntelEntry`
(supersedes the Phase-0 `IntelObject_Constructor` proposal — `Intel_Constructor`
already exists at `0x1400e3e30`), `Proximity_CollectLinksByRange2200/1200`,
`LinkVector_RetainLinksReferencing`.

### E — subsystem bodies unlocked by the field maps

17 of 323 `subsystem_*` rows became nameable:
`Creature_EnablePartsWithPower/_WithSensors/_WithWeapons`,
`Creature_SetPartsOwnerRef`, `Body_AccumulateOidCount`,
`Body_AssignAmmoSlotByCaliber`, `Body_RepairHealthStep`,
`Escadra_PredictPosition`, `Missile_PredictPosition`, `ComputeInterceptTime`,
`Profile_CreateTutorialTrigger`, `Gui_CreateStdChild`,
`RadioBeacon_ConstructorDefault`, `Sprite_CopyConstructor`,
`GameEnd_RegisterFreeItem`, `Math_AngleBetween2D`, `Gfx_DrawArcQuads`.

The remaining 302 are blocked on **structure maps**, not on code reading. The
consolidated blocker list (with offsets) is in
[ghidra-sweep-2026-10-30-p2e.md](ghidra-sweep-2026-10-30-p2e.md) §3 and is
summarised in [../structures.md](../structures.md) "Post-sweep additions".

## Incident — runaway EH walk (16:25–17:47)

Phase 1a's `EhWalk.java` hung the Ghidra AWT script thread for ~80 minutes: the
handler-map loop used an unbounded count read from a corrupt/aliased FuncInfo4
record. `jstack` showed `walkFuncInfo(EhWalk.java:74)` RUNNABLE with three MCP
workers queued behind it. Ghidra was restarted and the program reopened
unchanged; the script was hardened (pointers restricted to the image, every EH
count clamped to 1..64). Details:
[ghidra-sweep-2026-10-30-parent.md](ghidra-sweep-2026-10-30-parent.md).
Rule: a Ghidra script runs on the AWT event thread and cannot be cancelled from
outside the JVM — never loop on an image-derived count without a bound.

## What remains

| bucket | count | next step |
|---|---:|---|
| open funclets | 17 | shared ICF catches are unnameable; the rest need a caller-side identity |
| stale `rep_*` | 734 | ~347 CRT noise (classify, do not name); ~370 blocked on structure maps |
| `FUN_*` | 59 | 17 open funclets + 42 padding/`__scrt_*`/split fragments/unproven predicates |

Phase 3 (last predicates/fragments) and Phase 4 (docs close-out) of the plan
remain; the highest-yield next step is extending `structures.md` with the P2e
blocker list, which unlocks ~40 Gui bodies, 7 Sprite bodies and 15 property
records.
