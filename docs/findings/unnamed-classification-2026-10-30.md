# Unnamed-function classification — Highfleet 1.163

Date: 2026-10-30. Phase 0 of the post-sweep plan
([plan](../plans/2026-10-29-post-sweep-plan.md)).
Program: `Highfleet.exe.unpacked.exe v1.163` (project `HighfleetServer`).
Data: [data/unnamed-classification-2026-10-30.tsv](../data/unnamed-classification-2026-10-30.tsv).
No function was renamed, created or saved in this phase.

## Scope and method

All **928** unnamed function objects were enumerated in the live program:
80 `FUN_*` and 848 `rep_*`, of 5,430 total. For each one a single Ghidra
script (`run_script_inline`, listing/asm metadata only) recorded:

* entry address, current name, body size, region;
* caller count (`getCallingFunctions`) and callee count/name set
  (`getCalledFunctions`);
* up to three referenced string literals (rdata, printable, ≥5 chars,
  40-char truncation) and up to three referenced `.rdata` addresses that
  hold a pointer into the image (vtable / class-table evidence);
* element stride when derivable: immediate size passed to `New`, else the
  most frequent `IMUL` immediate, else the most frequent `lea`/memory scale.
  Allocation immediates ≥ 0x1000 are recorded as buffer/object sizes, not
  element strides.

No decompilation was used for the table: the first pass reads only
listing/callee/string metadata, so none of the 928 rows can hang the
decompiler. One spot-check decompile (`0x140005390`) was taken before the
classification run and showed the `rep_` embedded name is unreliable
(that body assigns ammo-slot indices while its name says `GetStats`), so
the family key uses **callee signature + stride + string cluster + region**,
with the `rep_` embedded name used only as a hint.

### The nine regions

| region | address range | dominant named content |
|---|---|---|
| `core_physics` | `0x140001000`–`0x140080000` | Body, Creature, Part, Frame, AircraftLogic |
| `render_shaders` | `0x140080000`–`0x1400e0000` | Effect, Shader*, Render/Gfx, FileBuf |
| `strategic_map` | `0x1400e0000`–`0x140120000` | Escadra, Location, Intel, StrategicFleet |
| `gui_ui` | `0x140120000`–`0x140160000` | Gui, Slider, Trail, ShipStats, TextGrid |
| `engine_res` | `0x140160000`–`0x1401a0000` | Sound/HGE, ResDesc, Input, Media, Zip |
| `seria_level` | `0x1401a0000`–`0x140280000` | seria loaders, screens, Fleet/Ship/Shop/Profile |
| `scene_hud` | `0x140280000`–`0x140310000` | Scene, Sprite, Hud, SCR/Level, VideoTask |
| `box2d` | `0x140310000`–`0x140330000` | b2World/Joint/Body/Contact |
| `crt_eh` | `0x140330000`–`0x140355000` | CRT, EH funclets, `__scrt_*`, global dtors |

## Totals

| verdict | count | share |
|---|---:|---:|
| `nameable` | 94 | 10.1% |
| `needs structures` | 457 | 49.2% |
| `CRT noise` | 347 | 37.4% |
| `ambiguous` | 30 | 3.2% |
| **total** | **928** | 100% |

Per region:

| region | total | nameable | needs structures | CRT noise | ambiguous |
|---|---:|---:|---:|---:|---:|
| core_physics | 190 | 12 | 107 | 66 | 5 |
| render_shaders | 142 | 27 | 57 | 53 | 5 |
| strategic_map | 97 | 10 | 54 | 29 | 4 |
| gui_ui | 37 | 9 | 17 | 10 | 1 |
| engine_res | 132 | 6 | 72 | 41 | 13 |
| seria_level | 143 | 15 | 86 | 40 | 2 |
| scene_hud | 67 | 8 | 42 | 17 | 0 |
| box2d | 2 | 0 | 2 | 0 | 0 |
| crt_eh | 118 | 7 | 20 | 91 | 0 |

Family-group roll-up (320 family labels; groups by prefix):

| group | rows | nameable | needs structures | CRT noise | ambiguous |
|---|---:|---:|---:|---:|---:|
| `subsystem_*` | 323 | 0 | 323 | 0 | 0 |
| `CRT_*` | 254 | 0 | 0 | 254 | 0 |
| `container_*` | 102 | 32 | 70 | 0 | 0 |
| `wrapper_*` | 52 | 30 | 22 | 0 | 0 |
| `scrt_*` | 47 | 0 | 0 | 47 | 0 |
| `EH_*` | 43 | 0 | 0 | 43 | 0 |
| `alloc_stride*` | 37 | 28 | 9 | 0 | 0 |
| `buffer_alloc_*` | 33 | 0 | 33 | 0 | 0 |
| `unattributed_*` | 30 | 0 | 0 | 0 | 30 |
| `ctor_vtable_*` | 4 | 4 | 0 | 0 | 0 |
| `thunk_alias_*` | 3 | 0 | 0 | 3 | 0 |

## Top 10 families by count × nameability

Ranked by the number of `nameable` members (families that are both large and
actionable for Phase 2):

| # | family | n | nameable | evidence |
|---:|---|---:|---:|---|
| 1 | `wrapper_of_ShaderData_ResetVTable` | 14 | 14 | 52 B, calls `ShaderData_ResetVTable` + `free`; one destructor per shader class |
| 2 | `alloc_stride0x4` | 9 | 9 | `New(4)` + `ThrowBadArrayLength` + `vectorTooLong`; `vector<uint32>` growth |
| 3 | `alloc_stride0x18_candidate` | 8 | 8 | `New(0x18)` + `_Xlength_error` + "list too long"; stride-24 vector growth |
| 4 | `wrapper_of_freeLinkMemory` | 6 | 6 | 44–109 B, `freeLinkMemory?` (+`free`); link-list teardown |
| 5 | `container_rbtree_node_stride0x40` | 5 | 5 | `New(0x40)` + `RbTree_Insert` + `tooLongError`; 64-byte map node |
| 6 | `container_rbtree_node_stride0x28_candidate` | 5 | 5 | `New(0x28)` + `RbTree_Insert` + `tooLongError`; 40-byte node |
| 7 | `wrapper_of_ISerializable_Destructor` | 3 | 3 | 73–109 B, `ISerializable_Destructor` + `free` |
| 8 | `container_vector_emplace_stride0x18_candidate` | 3 | 3 | `LinkVec_EmplaceReallocate` + `Link_ConstructFromBody` + `Link_CopyConstructor` |
| 9 | `container_rbtree_node_stride0x30_candidate` | 3 | 3 | `New(0x30)` + `RbTree_Insert` + `tooLongError` |
| 10 | `container_array_op_stride0x4` | 3 | 3 | `Array_Resize/MoveConstruct`, `New(4)`, throw path |

Next tier (2–3 members each): `alloc_stride0x50` (stride-80 unordered_map node,
"unordered_map/set too long"), `alloc_stride0x5`, `container_sort_helper_stride0x18_candidate`,
`container_rbtree_node_stride0x48`, `ctor_vtable_strategic_map`,
`wrapper_of_Array_FreeStride24`, `wrapper_of_Thunk_DestroyStringRange48`,
`container_vector_op_stride0x8_candidate`.

## Phase 2 rename candidates (not applied)

Only families whose member type is fixed by an allocation immediate, a
container callee triple, or a teardown callee are listed. `Alt` suffixes are
used where several addresses are structurally identical; the per-address
name should be refined from the vtable/owner at naming time.

| address(es) | proposed name | family / confidence |
|---|---|---|
| `0x140087460`, `0x1400895e0`, `0x140089e70`, `0x14008d570`, `0x14008e5c0`, `0x1400902c0`, `0x140090300`, `0x140090340`, `0x140092ea0`, `0x140093f00`, `0x140094bb0`, `0x1400956a0`, `0x140096ed0`, `0x140097c50` | `ShaderData_Destructor` (+ `Alt` per class) | destructor wrapper, high |
| `0x140006670`, `0x140012a30`, `0x14008df40`, `0x14008e110`, `0x1400dfa70`, `0x140121410`, `0x140198ac0`, `0x1401b46e0`, `0x1401b4750` | `VectorUInt32_Grow` (+`Alt`) | alloc stride 4 + vector throw triple, high |
| `0x14004adc0`, `0x14004b7e0`, `0x1400b8c90`, `0x1400e3090`, `0x140123770`, `0x140124c00`, `0x140124c80`, `0x1401a6540` | `VectorStride24_Grow` (+`Alt`) | alloc stride 0x18 + "list too long", high |
| `0x140083d70`, `0x14018efa0`, `0x1401a1e90` | `HashMap_Stride80_Grow` (+`Alt`) | alloc stride 0x50 + "unordered_map/set too long", high |
| `0x14005e4f0`, `0x1400e4a50`, `0x14033c700`, `0x14033c730`, `0x14033dab0`, `0x14033dd30` | `LinkMemory_Destructor` (+`Alt`) | calls `freeLinkMemory?`, high for the two 44–47 B bodies |
| `0x1400069a0`, `0x14009c270`, `0x1401a25b0`, `0x1401a2bd0`, `0x1401a2d20` | `RbTree_InsertNodeStride64` (+`Alt`) | `RbTree_Insert` + `New(0x40)`, high |
| `0x1400560c0`, `0x1400a15d0`, `0x140185a20`, `0x1401881a0`, `0x140192050` | `RbTree_InsertNodeStride40` (+`Alt`) | `RbTree_Insert` + `New(0x28)`, high |
| `0x1401a6430`, `0x140288590`, `0x1402c8fd0` | `RbTree_InsertNodeStride48` (+`Alt`) | `RbTree_Insert` + `New(0x30)`, medium |
| `0x1400e9640`, `0x1400e9810`, `0x140110b70` | `VectorLink_EmplaceReallocate` (+`Alt`) | `LinkVec_EmplaceReallocate` triple, high |
| `0x140123830`, `0x140128dc0`, `0x140199120` | `Array_ResizeStride4` (+`Alt`) | `Array_Resize/MoveConstruct` + `New(4)`, medium |
| `0x1402ab6a0`, `0x1402ab6f0`, `0x1402eb4b0` | `ISerializable_DtorWrapper` (+`Alt`) | `ISerializable_Destructor` + `free`, high |
| `0x1400eab10` | `IntelObject_Constructor` | `Intel_InitBaseFields` + `IntelPolygonList_AppendCopy` + vtable store, high |
| `0x1400fe400` | `EscadraMapShip_Constructor` | `EscadraMapShip_InitBaseFields` + `ISerializable` + vtable store, high |
| `0x140221be0`, `0x140224480` | `Sort_Stride24_ByFloat` (+`Alt`) | `Sort_PartitionByFloat` / `Sort_MedianOfNByStats`, medium |
| `0x140056310` | `VectorStride56_Grow` | `New(0x38)` + "list too long", medium |
| `0x14001c110` | `VectorStride40_Grow` | `New(0x28)` + throw path, medium |
| `0x140060960` | `VectorStride40_EmplaceLink` | `Link_ConstructFromBody` + `New(0x28)`, medium |
| `0x14011dc50` | `VectorStride240_Grow` | `New(0xf0)` + "list too long", medium |
| `0x14012c240` | `StringCopy_FreeWrapper` | `stringCopyWithMemoryFree` only, medium |
| `0x14015ccb0` | `TreeNode_DestroyRecursiveAlt` | `TreeNode_DestroyRecursive` + `free`, medium |
| `0x1401a5090` | `PlaneLoadout_EntryDestructorAlt` | existing destructor + `free`, medium |
| `0x1402eb620` | `HGE_Setup_FunctionPointersAlt` | `setupHGEFunctionPointers` + `free`, medium |
| `0x140339a20` | `StringPairVector_DestroyRange_EhWrap` | `StringPairVector_DestroyRange` + EH, medium |
| `0x140082c50` | `FileOStream_DtorWrapper` | `FileOStream_Destructor` + `free`, medium |

These 25 rows account for the 94 `nameable` members; the remaining
`nameable` singletons are in the TSV with their stride and evidence.

## What is left for Phase 2/3

* **`needs structures` (457).** 323 are `subsystem_*` families: real game code
  whose owner class or field map is missing. The largest are
  `subsystem_core_physics_GetStats` (16), `subsystem_engine_res_compareEscadraString`
  (12), `subsystem_strategic_map_Get_Profile` (6),
  `subsystem_render_shaders_CopyEscadraName` (6) and 33 `buffer_alloc_0x1000`
  bodies (4 KB streaming buffers). Extending `structures.md` for Body/Part/
  Profile/Escadra fields unlocks these.
* **`CRT noise` (347).** Compiler output and should stay unnamed:
  string/vector teardown (`CRT_tidy_deallocate` 70), `free`-only teardown
  (45), EH funclets (40), `__scrt_*`/padding stubs (47), float-math wrappers
  (31), mem wrappers (20), allocator wrappers, throw/fail glue, and 3 ICF
  thunk aliases. Naming them would duplicate a target or add clones.
* **`ambiguous` (30).** 27 bodies ≤64 B with no callee, string or rdata
  reference (padding, alignment stubs, `ret`-only fragments), plus 3 bodies
  with only rdata reads and no attributable owner. Record and close.

## Caveats

* The stride column is a heuristic. `stride_src` in the raw pass distinguishes
  `new` (allocation immediate), `imul` and `lea`; large `New` immediates
  (≥ 0x1000, e.g. 0x1000, 0x1090, 0x7e90) are treated as buffer/object sizes
  and excluded from element-stride families.
* `rep_*` embedded names are unreliable: `rep_140005390_GetStats` is an
  ammo-slot assignment loop, not `GetStats`. They were used only as hints.
* During an optional spot-check decompile the Ghidra MCP bridge process
  exited; the program itself was not modified and no transaction was open.
  The classification table was written before that, from listing-only data.
* No `rename`, `create_function`, `save_program` or transaction was issued.
