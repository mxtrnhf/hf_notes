# Ghidra sweep 2026-10-30 — Phase 2 agent D (vector / constructor / destructor families)

Program: `Highfleet.exe.unpacked.exe` v1.163 only (project `HighfleetServer`,
image base `0x140000000`, `D:/Games/Highfleet/Highfleet v1.163/`). 1.151 was never
opened. No `save_program`, no commit, no `create_function`, no transaction
(the rename/plate MCP endpoints were used, so no `startTransaction` was needed).

Scope: the 21 families assigned to Phase 2 D in
[data/unnamed-classification-2026-10-30.tsv](unnamed-classification-2026-10-30.tsv)
→ **33 rows** (37 TSV rows, of which 4 are the open funclets `0x14033c700`,
`0x14033c730`, `0x14033dab0`, `0x14033dd30`; 3 more of that family were listed
in Phase 0 under a different capitalisation and were added by hand:
`wrapper_of_setupHGEFunctionPointers` = `0x1402eb620`).

Result: **22 renamed + plated, 11 recorded and skipped, 7 excluded by ownership**.

## Method

Each of the 33 bodies was decompiled (`/decompile_function`), read against its
callers (`/get_function_xrefs`) and, for constructors/destructors, against the
vtable it installs (`/read_memory` of the `.rdata` slot + xrefs to the slot).

* **Vector helpers** — element size taken from the allocation immediate *and*
  the index scale (`sar`/`and` mask or the post-increment constant), not from
  the classifier stride. Three classifier strides were wrong (see "Disproved").
* **Constructors** — the vtable written by the body identifies the class.
* **Wrappers** — renamed only where the body adds a step beyond a tail call:
  the deleting destructors (vtable re-install + singleton reset + conditional
  `free`) and the container teardown/copy bodies. `wrapper_of_CopyString`
  bodies are real copy constructors (they copy fields *and* the string), so they
  were named as constructors instead of wrappers.
* Plate comments follow the standing template (summary, `Algorithm:`,
  `Parameters:`, `Returns:`) and were set with `/set_plate_comment`.

All 22 renames were re-read back with `/get_function_by_address` and
`/get_plate_comment` afterwards: **22/22 match, 22/22 carry a plate**.

## Renamed (22)

| address | new name | family | proof |
|---|---|---|---|
| `0x140017e20` | `String_AssignCopy` | `wrapper_of_CopyString` | self-assign check, picks heap vs inline source by capacity (`+0x18 > 0xf`), `CopyString(dst, src, len@+0x10)`; 40+ callers are ordinary string assignments |
| `0x14005e4f0` | `LinkedList_DestroyFreeHeader` | `wrapper_of_freeLinkMemory` | walks the chain, `freeLinkMemory_(node+0x10)`, `free(node)`, then `free(header)`; called from `Escadra_Destructor` / `Creature_Destructor` |
| `0x140060960` | `ListStride24_PushBack` | `container_vector_emplace_stride0x28` | `New(0x28)` = 2 link pointers + 0x18 `Link`, inserts before sentinel `+0x1558`, count `+0x1560`, limit `0x666666666666666` → `_Xlength_error("list too long")`. Not a vector emplace: the classifier family is wrong, the body is `std::list::push_back` for an 0x18-byte element |
| `0x140082c50` | `FileOStream_ScalarDeletingDestructor` | `wrapper_of_FileOStream_Destructor` | `this-0xa8` (vtable at `+0xa8`), `FileOStream_Destructor`, `free` on flag bit 0 |
| `0x140087a70` | `Effect_AddTextureVectorParam` | `container_vector_op_stride0x8_candidate` | `New(0x38)` `ShaderResourceView` + `New(0x38)` `ShaderParamTextureVectorNew`, two stride-8 `vec_realloc_insert` appends at `+0x68`/`+0x80`; sibling of `Effect_AddTextureParam` / `Effect_AddTextureArrayParam` |
| `0x14009b950` | `VectorStride64_InsertStringPair` | `container_vector_op_stride0x6` | index scale `>>6` / mask `0x3f`, max_size `0x3ffffffffffffff`, grow `*0x40`, `StringPairVector_MoveRange`; element = two SSO strings. Classifier stride `0x6` is bogus |
| `0x1400e4a50` | `LinkedList_ClearFreeChain` | `wrapper_of_freeLinkMemory` | frees the node chain from the tail at `+0x18` (`freeLinkMemory_(node+0x10)` then `free`) but keeps the header; no callers (vtable-only) |
| `0x1400e9640` | `Proximity_CollectLinksByRange2200` | `container_vector_emplace_stride0x18_candidate` | three `compareAbsoluteDifferenceThreshold(pos@+0x150, node[1].m_code, r, r²)` tests with r = 2200 / 733.33 / 183.33, each appending an 0x18 `Link` to `+0x5b0` / `+0x598` / `+0x580` via `LinkVec_EmplaceReallocate` |
| `0x1400e9810` | `Proximity_CollectLinksByRange1200` | `container_vector_emplace_stride0x18_candidate` | same shape, r = 1200 / 466.67 / 191.67, vectors `+0x5f8` / `+0x5e0` / `+0x5c8`; called from `rescueMinigame?` |
| `0x1400eab10` | `Escadra_GetOrCreateIntelEntry` | `ctor_vtable_strategic_map` | find-or-create on the list at `+0x1f8`, `New(0x1b8)`, `ISerializable::ISerializable` then `IntelVFTABLE` (`0x14035dff8`, the vtable also written by the *existing* `Intel_Constructor` at `0x1400e3e30`), `SetLink`, `IntelPolygonList_AppendCopy`, `Intel_RecomputeCentroid`, `"…Escadra.cpp"` CHECK lines. Classifier said "constructor"; the body is a cache/merge entry point, not the ctor |
| `0x140110b70` | `LinkVector_RetainLinksReferencing` | `container_vector_emplace_stride0x18_candidate` | copies the 0x18-stride elements of `+0x308` whose sub-entry string pointer equals `param_1` into a local vector, frees every element of the target vector, then copy-appends the kept ones |
| `0x140128c20` | `IntStringPair_CopyConstructor` | `wrapper_of_CopyString` | dword id at 0, embedded `std::string` at `+8` (len `+0x18`, cap `+0x20`), `strlen` + `CopyString` |
| `0x14015ccb0` | `RbTree_ClearFreeResetHeader` | `wrapper_of_TreeNode_DestroyRecursive` | `TreeNode_DestroyRecursive` per node + `free`, then the sentinel is pointed at itself and the count cleared; the header is *not* freed (contrast `RbTree_ClearFreeHeader` at `0x140017180`) |
| `0x140196070` | `PointerStringPair_CopyConstructor` | `wrapper_of_CopyString` | qword at 0, `std::string` at `+8`; called from `TarkhanGUIDispatchOperator` |
| `0x1401960c0` | `StringIntPair_CopyConstructor` | `wrapper_of_CopyString` | `std::string` at 0, dword at `+0x20`; called from `LoadPlaneLoadouts` / `addSalvageToPlayerInv` |
| `0x1401a4420` | `Stride72_CopyConstructor` | `container_vector_op_stride0x3` | copy-ctor of the 0x48-byte element used by `VectorStride72_InsertCopy`: header qwords, `AllocArrayStride40` + `Array_CopyConstruct40Vector` at `+0x18`, `AllocateArrayOf8Byte` + `memmove` at `+0x30`. Classifier stride `0x3` is bogus |
| `0x1401a65e0` | `VectorStride3_AppendRotatedTriples` | `container_vector_op_stride0x2` | appends 3-byte rotated triples (digit buffer `"0123456789"`, `VectorStride3_Insert` on growth). Classifier stride `0x2` is bogus, real stride 3 |
| `0x1401a5090` | `PlaneLoadout_NamedEntry_Destructor` | `wrapper_of_PlaneLoadout_EntryDestructor` | `PlaneLoadout_EntryDestructor(this+0x20)`, then frees the `std::string` at 0 (oversized-block check) and resets it to inline |
| `0x1402ab6a0` | `Profiler_Singleton_ScalarDeletingDestructor` | `wrapper_of_ISerializable_Destructor` | installs vtable `0x140374ae0` (the "PROFILER" stage vtable written by `Profiler_CreateMainLoopNode`), clears `DAT_143a1c448`, `ISerializable_Destructor`, conditional `free` |
| `0x1402ab6f0` | `Profiler_ScalarDeletingDestructor` | `wrapper_of_ISerializable_Destructor` | installs vtable `0x140374b28` (profiler object *with* main-loop node), releases `DAT_147fc6a88` through its virtual slot, falls back to the `0x140374ae0` stage, then the same base teardown |
| `0x1402eb4b0` | `VideoTask_ScalarDeletingDestructor` | `wrapper_of_ISerializable_Destructor` | installs vtable `0x140377130` (same slot installed by `setupVideoTask?`), clears `DAT_143a1c400`, `ISerializable_Destructor`, conditional `free` |
| `0x1402eb620` | `HGE_ScalarDeletingDestructor` | `wrapper_of_setupHGEFunctionPointers` | calls `setupHGEFunctionPointers` (which re-installs vtable `0x140377178` and releases ~30 cached HGE objects), then conditional `free` |

## Disproved and skipped (11)

| address | classifier claim | what the body actually is | why left unnamed |
|---|---|---|---|
| `0x140047fc0` | `wrapper_of_GetStats` | `(b-a)/((b/(GetStats(+0x188)->+0x94 * 60)) * param)` on floats `+0x2c8`/`+0x2cc` | not a wrapper; a derived-stat ratio on an unproven owner class (`needs structures` in Phase 0) |
| `0x140048bf0` | `wrapper_of_GetStats` | `b/(stats->+0x94*60)` | same |
| `0x140048c70` | `wrapper_of_GetStats` | returns the 0x40-stride name string of the stats row selected by `**(int**)(stats+0x98)` | same; the stats table (`someStatsOffset…`) is still unnamed so the returned type is not provable |
| `0x140049da0` | `wrapper_of_GetStats` | boolean test over stats flags `+0xb0` and `owner+0x3c4 ∈ {500, 3}` | same |
| `0x1400490d0` | `container_vector_op_stride0x8_candidate` | orientation update (`normalizeVectors`, `atan2f`, `cosf`, `sinf`), then virtual `+0xe8` sampling over a list, two stride-8 appends to an output vector | a domain routine (`Part`/creature aiming), not a container helper; owner unproven |
| `0x1400fe400` | `ctor_vtable_strategic_map` | spawns `MapShipBody` (`New(0xa60)`, `Body_Constructor` + `MapShipBody` vtable) and `MapShip` (`New(0xa0)`) from `Property` objects, `SetBackground_(…,"sign_map_frigat",…)` | a factory; it writes no vtable onto its own `param_1`, so it is not a constructor |
| `0x14015c650` | `container_vector_emplace_stride0xf` | appends `Text_RightPadInteger` output to the stride-0x20 string vector `+0xe70`, a `Link` to `+0xe88`, and writes a line counter on `+0xed8` | GUI log-line append called from `setupPropsSecondaryMapModes`; stride `0xf` is bogus and the owner widget is unnamed |
| `0x1401bf270` | `ctor_vtable_strategic_map` | builds `dir+name`, `FindFirstFileA`/`FindNextFileA`, `File_OpenIfstream`/`File_OpenOfstream`, copies file text through `operator<<`, `FindClose` | a directory-copy utility; the "vtable" refs were streambuf/ostream vtables, no object is constructed |
| `0x140288840` | `container_vector_op_stride0x20` | zeroes the object, `New(0x38)` circular sentinel, `Vector_Resize8(+0x18, 0x10, sentinel)`, sets `1.0f` | sub-object constructor inside `Profile::Profile` (3 call sites); no vtable and no class evidence → `needs structures` |
| `0x1402c88e0` | `wrapper_of_CopyString` | constructor of `{int; std::string at +8; int +0x28; int +0x2c}` from by-value args | anonymous 0x30-byte struct, only caller is inlined in an unnamed scene function |
| `0x1402ebb20` | `ctor_vtable_scene_hud` | spawns an `0xa0` ground/crowd object (vtable `0x1403770e8`, `Ground_SetSpawnParams`, `"crowd_man"`, `"_salute1"`, `PlayRadioSound?`) plus a `New(0x1a8)` sprite | a spawner, not a constructor of its own argument |

## Excluded (7) — funclet ownership / open-funclet range

`0x140339a20`, `0x14033c700`, `0x14033c730`, `0x14033dab0`, `0x14033dd30`,
`0x14033e600`, `0x140341fe0`. All are `funclet_addr` rows of
[data/funclet-ownership-2026-10-29.tsv](funclet-ownership-2026-10-29.tsv) and sit
inside `0x140336730–0x140350510`. The four `freeLinkMemory?` ones are the open
funclets called out on the blackboard. Note `0x140339a20` is recorded there as
the rethrow funclet of `0x14009b950` (renamed above); `0x14033e600` and
`0x140341fe0` belong to `0x140128dc0` / `0x140199120`, not to any Phase 2 D body.

Also honoured: no address from the withheld trio (`0x14017c780`, `0x14017c800`,
`0x14004c7e0`) and none of `0x14034b6b8/743/75b` was touched.

## Counts

Live program at the end of the run (read-only script, `/run_script_inline`):
**5,432 function objects, 4,622 named (85.09%), 59 `FUN_*`, 751 `rep_*`**.
The baseline on the blackboard was 5,430 / 4,504 / 78 / 848, so other Phase 2
agents were renaming concurrently; **this agent's own delta is 22 `rep_*` →
named** (net 22 fewer `rep_*`, no address created or deleted).

## Caveats

* `Escadra_GetOrCreateIntelEntry` replaces Phase 0's `IntelObject_Constructor`
  proposal: a real `Intel_Constructor` already exists at `0x1400e3e30`.
* The two `Proximity_CollectLinksByRange*` bodies share the 3-band shape but not
  the radii, and the caller (`Fleet_CreateEscadraFromShips`) passes the grid
  owner and the escadra in an order the decompiler could not settle; the class
  prefix was therefore left neutral instead of `Escadra_`.
* `Profiler_Singleton_…` vs `Profiler_…` differ only in the installed vtable
  stage (`0x140374ae0` before the main-loop node is attached vs `0x140374b28`
  after); both act on the `DAT_143a1c448` singleton.
* `VectorStride64_InsertStringPair` uses the existing `VectorStride*` naming so
  it sorts with the other 48 stride helpers; its element is a pair of SSO
  strings, which is what `StringPairVector_MoveRange` already establishes.
