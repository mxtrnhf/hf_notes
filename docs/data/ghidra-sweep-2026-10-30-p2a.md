# Ghidra sweep, Phase 2 agent A — render/shader families

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`). 1.163
only; the 1.151 program was never opened or written. No `save_program`, no
commit, no README/STATUS edit, no transaction left open.

Scope: the `wrapper_of_ShaderData_ResetVTable` family (14 rows), every other
`verdict=nameable` row with `region=render_shaders` (13 rows), and
`ctor_vtable_scene_hud` (1 row) — 28 rows. Excluded sets (funclet-ownership TSV
addresses, `0x140336730–0x140350510`, `0x14034b6b8/743/75b`,
`0x14017c780/800`, `0x14004c7e0`) were not touched.

**Result: 15 renamed + plated, 13 skipped** (all 13 already carried a name when
the pass applied: 3 were renamed by a concurrent agent during this pass, 10
were already named with matching bodies). Two of those concurrent names land on
the same conclusion as this pass (see §Skipped).

## Method

The 14 `wrapper_of_ShaderData_ResetVTable` bodies are the 52-byte MSVC
scalar-deleting-destructor shape:

```
ShaderData_ResetVTable();          // base teardown
if (flag & 1) free(this);          // operator delete, unsized
return this;
```

The body does not name its own class, so the class was read from the vtable
that references the body: every data xref site `S` was walked back in 8-byte
steps to the slot that holds a `CompleteObjectLocator` pointer at `S-8`; the
COL signature (`1`), `pTypeDescriptor` (32-bit RVA at COL+0xC) and the
`.?AV…@@` name at `TypeDescriptor+0x10` give the class. Script: listing-only,
fixed address list, no unbounded loop (`p2a/mkv.py` → `/run_script_inline`).

All 14 turned out to be **slot 1 of a `ConstantBuffer<…>` vtable**, i.e. the
deleting destructor of the D3D11 constant-buffer wrapper the owning shader
allocates (`ShaderData_Constructor` base, one `ConstantBuffer<UCB…@ShaderX>`
per shader/block). None is a `ShaderData`-derived *shader* destructor, and none
writes the vtable itself. Nine have a single owning instantiation, five are
MSVC ICF folds serving 2–9 instantiations whose `T` destroys trivially; the
folded ones are named `ConstantBuffer_ScalarDeletingDestructor_SharedA–E` and
the plate lists every owning vtable.

## Renamed (15)

| address | old name | new name | class evidence | plate summary |
|---|---|---|---|---|
| `0x140087460` | `rep_140082c10_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `EffectMatrixConstantBuffer_ScalarDeletingDestructor` | vtable `0x140356ad8` slot 1 → COL → `.?AV?$ConstantBuffer@UCBMatrix@Effect@@@@` | 52 B: `ShaderData_ResetVTable` + guarded `free`; names the CB instance behind `EffectMatrixConstantBuffer_Upload`; class from RTTI |
| `0x1400895e0` | `rep_140084d90_…::free` | `ShaderBackgroundConstantBuffer_ScalarDeletingDestructor` | vtable `0x140356c38` slot 1 → `ConstantBuffer<CBConstants<ShaderBackground>>` | same template; plate records vtable/slot and the unsized delete |
| `0x140089e70` | `rep_140085620_…::free` | `ConstantBuffer_ScalarDeletingDestructor_SharedA` | 9 vtables, all slot 1: `0x140356da0` Bloom, `0x140356e88` Blur, `0x140356fc0` Clouds, `0x1403570b0` Color, `0x140357478` DeferringCloseAndPrebloom, `0x140357858` DeferringFarStepness, `0x140357ea8` Glitch, `0x140358a10` RainDrops, `0x140358c18` Shockwave | plate lists all nine owning `ConstantBuffer<…>` instantiations; states the ICF reason (trivial `T`) |
| `0x14008d570` | `rep_140088d20_…::free` | `ConstantBuffer_ScalarDeletingDestructor_SharedB` | 5 vtable slots: `0x1403572f8` DeferringClose, `0x140357ec0` Glitch-CB2, `0x140358328` Outline-CB2, `0x1403586e0` PrebloomAndOutline-CB3, `0x140358838` LOD-CB3 | as above, five owners |
| `0x14008e5c0` | `rep_140089d70_…::free` | `ConstantBuffer_ScalarDeletingDestructor_SharedC` | 8 vtable slots: DeferringCloseAndPrebloom-CBVertex, DeferringSubscreen, Outline, Prebloom, PrebloomAndOutline, LOD, RainDrops-CB2, ShadowMapping | as above, eight owners |
| `0x1400902c0` | `rep_14008ba70_…::free` | `ShaderDeferringFarPrerenderedConstantBuffer_ScalarDeletingDestructor` | vtable `0x140357758` slot 1 → `ConstantBuffer<CBConstants<ShaderDeferringFarPrerendered>>` | single owner; plate records the vtable |
| `0x140090300` | `rep_14008bab0_…::free` | `ShaderDeferringFarPrerenderedVertexConstantBuffer_ScalarDeletingDestructor` | vtable `0x140357740` slot 1 → `ConstantBuffer<CBConstantsVertex<…>>` | vertex-block CB of the same shader |
| `0x140090340` | `rep_14008baf0_…::free` | `ShaderDeferringFarPrerenderedShadingConstantBuffer_ScalarDeletingDestructor` | vtable `0x140357770` slot 1 → `ConstantBuffer<CBShading<…>>` | shading-block CB of the same shader |
| `0x140092ea0` | `rep_14008e650_…::free` | `ConstantBuffer_ScalarDeletingDestructor_SharedD` | 2 slots: `0x140357c98` Dithering, `0x140358238` MapPostProcessing | two owners |
| `0x140093f00` | `rep_14008f6b0_…::free` | `ShaderGlitchConstantBuffer3_ScalarDeletingDestructor` | vtable `0x140357ed8` slot 1 → `ConstantBuffer<CBConstants3<ShaderGlitch>>` | third CB block of ShaderGlitch |
| `0x140094bb0` | `rep_140090360_…::free` | `ShaderLightingConstantBuffer_ScalarDeletingDestructor` | vtable `0x140357fe8` slot 1 → `ConstantBuffer<CBConstants<ShaderLighting>>` | single owner |
| `0x1400956a0` | `rep_140090e50_…::free` | `ShaderLightingMapConstantBuffer_ScalarDeletingDestructor` | vtable `0x140358128` slot 1 → `ConstantBuffer<CBConstants<ShaderLightingMap>>` | single owner |
| `0x140096ed0` | `rep_140092680_…::free` | `ShaderPostConstantBuffer_ScalarDeletingDestructor` | vtable `0x140358410` slot 1 → `ConstantBuffer<CBConstants<ShaderPost>>` | single owner |
| `0x140097c50` | `rep_140093400_…::free` | `ConstantBuffer_ScalarDeletingDestructor_SharedE` | 4 slots: `0x1403586c8` PrebloomAndOutline-CB2, `0x140358820` LOD-CB2, `0x140358928` RadialBlur, `0x140358d00` ShockwaveTemplate | four owners |
| `0x1402ebb20` | `rep_1402c05f0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::sqrtf` | `Ground_SpawnAlongPath` | allocates `0xa0`, stores vtable `0x1403770e8` slot 0 → COL → `.?AVGround@@`, calls slot 7 (`0x140377120`) and appends to global vector `0x148021c70`; called from `generateCityLandscape` | operand name, not a class name: the function's own class is not provable. Plate documents the path walk over `0x148021cb8`/`0x14800f000`, the duplicate test against the Ground list at `0x14801dd30`, and the `Ground` construction; family verdict `ctor_vtable_scene_hud` is explained as the *created* object's vtable |

Notes on the `ConstantBuffer` names: `XConstantBuffer_…` mirrors the existing
sibling `EffectMatrixConstantBuffer_Upload` (slot 0 of the same vtable
`0x140356ad8`); `…CBConstants2/3/Vertex/Shading` follow the RTTI template
argument of the block. Every shared name is deliberately not tied to one owner
because the body is referenced by 2–9 class vtables.

## Skipped (13)

All 13 already had a name when the rename step ran; none was overwritten.

| address | family | live name at apply time | reason |
|---|---|---|---|
| `0x140082c50` | `wrapper_of_FileOStream_Destructor` | `FileOStream_ScalarDeletingDestructor` | renamed by the concurrent agent between the name check and the apply; plate present, body matches (this-0xa8 + `FileOStream_Destructor` + guarded `free`, reached from `Ofstream_DeletingDestructorThunk` 0x140082bf8, slot 0 of 0x140356810). Same conclusion as the plate queued here |
| `0x140087a70` | `container_vector_op_stride0x8_candidate` | `Effect_AddTextureVectorParam` | concurrent rename; identical conclusion (ShaderResourceView + `ShaderParamTextureVectorNew_Constructor` into the `+0x68`/`+0x80` vectors), plate present |
| `0x14009b950` | `container_vector_op_stride0x6` | `VectorStride64_InsertStringPair` | concurrent rename; accepts the 0x40-stride two-string emplace reading, plate present (the TSV stride 0x6 is a `>> 6` misread) |
| `0x140083d70` | `alloc_stride0x50` | `List_FindOrAppendNode80` | already named; body is a keyed (memcmp 0x34) 0x50-node list find-or-append, not the TSV's "unordered_map too long" shape |
| `0x14008ddb0` | `alloc_stride0x6` | `VectorStride64_Reallocate` | already named; `>> 6` index math, 0x40 elements, 32-byte aligned over 0x1000 |
| `0x14008df40` | `alloc_stride0x4` | `VectorStride80_Reallocate` | already named; `/ 0x50` index math and `*0x50` allocation |
| `0x14008e110` | `alloc_stride0x4` | `VectorStride16_Reallocate` | already named; `>> 4` index math and `*0x10` allocation |
| `0x14009c270` | `container_rbtree_node_stride0x40` | `RbTreeStride104_EmplaceShader` | already named; allocates the 0x68 (104) node, inserts via `RbTree_Insert`, constructs the `VShader` payload |
| `0x14009c470` | `container_rbtree_node_stride0x68` | `RbTreeStride104_ConstructNode` | already named; `New(0x68)` node + key/value construction |
| `0x1400a15d0` | `container_rbtree_node_stride0x28_candidate` | `RbTreeStride40_ConstructNode` | already named; 0x28 (40) node construction |
| `0x1400b8c90` | `alloc_stride0x18_candidate` | `List_PushBackNode24Qword` | already named; `New(0x18)` list node, head insert, "list too long" guard |
| `0x1400df450` | `alloc_stride0x5` | `VectorStride32_InsertDefault` | already named; 0x20 element insert-default with throw path |
| `0x1400dfa70` | `alloc_stride0x4` | `VectorStride16_InsertValueFlag` | already named; `>> 4` index math (0x10 elements), not stride 4 |

## Caveats

* The `ShaderData_ResetVTable` callee is the base teardown, not a per-class
  destructor: it is why these bodies are byte-identical and ICF-folded. The
  class is proven from the vtable that owns the slot, not from the call.
* `free(this)` is the unsized `operator delete`; there is no allocation size in
  the body to quote. The instance is allocated in the owning shader's `_Init`
  (`ShaderX_Init` calls `ShaderData_Constructor` at 0x14009f930, one call per
  CB block; `EffectMatrixConstantBuffer_Constructor` 0x140086fc0 allocates
  `New(0x68)` for `ConstantBuffer<CBMatrix<Effect>>`), which is also the
  independent proof that these wrappers destroy the CB instance and not the
  shader: the shader classes' own deleting destructor is a different body
  (e.g. `0x1400055c0` in every `Shader*` vtable slot 0).
* `0x1402ebb20` is the only non-destructor row named here, and it is named by
  operation; its `Ground` class evidence is the RTTI of the object it creates,
  explicitly not a claim about the function's owning class.
* A concurrent agent renamed three of the 13 scope rows mid-pass
  (`0x140082c50`, `0x140087a70`, `0x14009b950`); the apply step detected the
  new names and skipped them rather than overwrite the plates.
