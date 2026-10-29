# Ghidra sweep 2026-10-30 — Phase 2 agent B (alloc / array-op families)

Program: `Highfleet.exe.unpacked.exe v1.163` (project `HighfleetServer`).
**1.163 only.** 29 functions renamed, 29 plate comments set, 2 rows skipped.
No `save_program`, no commit. Program not saved.

Scope: the `alloc_*` and `container_array_op_*` families of
[unnamed-classification-2026-10-30.tsv](unnamed-classification-2026-10-30.tsv):

| family | rows | renamed | skipped |
|---|---:|---:|---:|
| `alloc_stride0x4` | 9 | 9 | 0 |
| `alloc_stride0x18_candidate` | 8 | 8 | 0 |
| `alloc_stride0x5` | 3 | 3 | 0 |
| `alloc_stride0x50` | 3 | 3 | 0 |
| `alloc_stride0x28` | 1 | 1 | 0 |
| `alloc_stride0x38` | 1 | 0 | 1 |
| `alloc_stride0x6` | 1 | 1 | 0 |
| `alloc_stride0xf0` | 1 | 1 | 0 |
| `alloc_stride0x3` | 1 | 1 | 0 |
| `container_array_op_stride0x4` | 3 | 2 | 1 |
| **total** | **31** | **29** | **2** |

## Method

Every body was decompiled (listing + decompiler, one address at a time) and
the element size was proved from the allocation and the index scaling, not
from the classifier's `stride` column. For vector routines the proof is the
`New(n * S)` immediate together with the matching `>> log2(S)`, `/ S` or
`* S` on begin/end/capacity. For list routines the proof is `New(node_size)`
plus the payload offset written inside the node.

**The classifier's `stride` column is wrong for most of this scope.** The raw
pass recorded the most frequent `IMUL`/`lea` scale, which for these bodies is
the scale of an unrelated field access (4 for a dword payload, 5/6 for
`lea`-formed offsets). The real element sizes are 0x10, 0x18, 0x20, 0x30,
0x40, 0x50 and 0xf0. The Phase 0 proposal `VectorUInt32_Grow` /
`VectorStride24_Grow` for these rows is therefore not used.

The other Phase 0 proposal, `VectorStride24_Grow` for `alloc_stride0x18_candidate`,
is also wrong: those eight bodies are **`std::list<T>` node inserts** — they
allocate one `New(0x18)` node, write the value at node+0x10, bump a node count
and splice the node before the sentinel. They are not vector growth. They are
named with the program's existing `List_*` convention (`List_PushBackPointer`,
`List_PushBackPayload24`, `List_InitCircular40`, `List_FreeAllNodes28`), with
the node size in the name.

Naming follows the existing program families exactly:

* vector ops — `VectorStride16_InsertValue`, `VectorStride24_Reallocate`,
  `VectorStride16_Resize`, `VectorStride48_PushBack`, `VectorStride80_Assign`
  (decimal stride, same as `VectorStride40_InsertMove`);
* raw allocate-n helpers — `AllocArrayStride8/24/40/48` → new
  `AllocArrayStride16/32/80`;
* hash maps — `HashMap_InsertStringKey`, `HashMap_FindU64Key`;
* lists — `List_PushBack*`, `List_FindValueByKey`, `List_InitCircular40`.

## Renames

`old` is the live name before this pass. `proof` states the allocation
immediate and the scaling that fixes the element size.

### `alloc_stride0x4` — actually stride 0x10 (insert/reallocate) and 0x80/0x40/0x10 allocators

| address | old | new | proof |
|---|---|---|---|
| `0x140006670` | `rep_140006070_API-..._invalid_parameter_noinfo_noreturn` | `VectorStride16_InsertValue_2` | insert-one; `size=(end-begin)>>4`, `New(cap*0x10)`, slot writes 2 qwords, commit `begin+uVar1*2` qwords |
| `0x140012a30` | `rep_140012bb0_New` | `VectorStride16_InsertValue_3` | same template: `>>4`, `*0x10`, `puVar12+uVar1*2` |
| `0x1400dfa70` | `rep_1400da420_API-..._invalid_parameter_noinfo_noreturn` | `VectorStride16_InsertValueFlag` | `>>4`, `New(uVar14*0x10)`; writes qword+dword at +0/+8 and clears the flag byte at +0xc |
| `0x140198ac0` | `rep_14018aae0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `VectorStride16_InsertValue_4` | `>>4`, `*0x10`, `puVar12+uVar1*2` |
| `0x14008e110` | `rep_1400898c0_New` | `VectorStride16_Reallocate` | grow-to-capacity: `>>4`, `New(uVar6*0x10)`, `end=param_2*0x10+p`, `cap=uVar6+p` |
| `0x14008df40` | `rep_1400896f0_New` | `VectorStride80_Reallocate` | `(end-begin)/0x50`, `New(uVar6*0x50)`, memset/memmove, `end=param_2*0x50+p` |
| `0x140121410` | `rep_14011b340_New` | `AllocArrayStride16` | allocate-n: `param_2*0x10`, `cap=block+param_2*0x10` (the 0x10 shift is explicit) |
| `0x1401b46e0` | `rep_1401a4770_New` | `AllocArrayStride16_2` | allocate-n: `param_2*0x10`, returns block |
| `0x1401b4750` | `rep_140269510_New` | `AllocArrayStride80` | allocate-n: `param_2*0x50` |

### `alloc_stride0x5` — actually stride 0x20 (and a 0x20 allocator)

| address | old | new | proof |
|---|---|---|---|
| `0x14011df60` | `rep_140118090_New` | `VectorStride32_InsertValue` | insert-one: `>>5`, `New(uVar19*0x20)`, element fills 0x20 (`+0x1c` last field), `begin+uVar1*4` qwords |
| `0x1400df450` | `rep_1400d9e00_API-..._invalid_parameter_noinfo_noreturn` | `VectorStride32_InsertDefault` | insert-one: `>>5`, `*0x20`, first qword from param_3, three qwords zeroed |
| `0x140007d70` | `rep_140007840_API-..._invalid_parameter_noinfo_noreturn` | `AllocArrayStride32` | allocate-n: `param_2*0x20` |

### `alloc_stride0x18_candidate` — `std::list` 0x18-byte node inserts

| address | old | new | proof |
|---|---|---|---|
| `0x14004adc0` | `rep_1400489c0_New` | `List_PushBackNode24UInt` | `New(0x18)`; dword payload at node+0x10; count bump + sentinel splice; limit `0xaaa…a` |
| `0x14004b7e0` | `rep_140049420_New` | `List_PushBackNode24Unique` | `New(0x18)`; qword payload at +0x10; linear search skips duplicates; count at +0x238 |
| `0x1400b8c90` | `rep_1400b4d50_MSVCP140.DLL::std::_Xlength_error` | `List_PushBackNode24Qword` | `New(0x18)`; qword payload at +0x10; sentinel splice |
| `0x1400e3090` | `rep_1400dda40_MSVCP140.DLL::std::_Xlength_error` | `HashMap_InsertU64Key` | unordered_map: `New(0x18)` node, 8-byte key at +0x10, 0x10-byte buckets, FNV-1a, "unordered_map/set too long" |
| `0x140123770` | `rep_14011d110_New` | `List_PushBackNode24MatchingField130` | `New(0x18)`; payload pointer at +0x10; matches `*(int*)(obj+0x130)==param_2` |
| `0x140124c00` | `rep_14011e2c0_New` | `List_PushBackNode24ObjectPtr` | `New(0x18)`; object pointer at +0x10; splices into `DAT_1439e5fd8` |
| `0x140124c80` | `rep_14011e340_New` | `List_GridCellPushBackNode24` | `New(0x18)`; row vector `/0x18`, cell vector `>>4`; payload at +0x10 |
| `0x1401a6540` | `rep_140197b80_MSVCP140.DLL::std::_Xlength_error` | `List_PushBackNode24Notifying` | `New(0x18)`; qword payload at +0x10; then `rep_14009d8e0_tooLongError` |

### `alloc_stride0x50` — 0x50-byte list node / unordered_map nodes

| address | old | new | proof |
|---|---|---|---|
| `0x140083d70` | `rep_14007f520_New` | `List_FindOrAppendNode80` | `New(0x50)`; memcmp of 0x34 key bytes at node+0x10, value at +0x48; sentinel splice |
| `0x14018efa0` | `rep_140181470_New` | `HashMap_InsertStringPairKey` | `New(0x50)`; two 0x20-byte std::strings at +0x10/+0x30; FNV-1a; limit `0x333…3` |
| `0x1401a1e90` | `rep_1401934a0_VCRUNTIME140.DLL::memcmp` | `HashMap_InsertStringKeyAlt` | `New(0x50)`; one 0x20-byte key string at +0x10, empty value string at +0x30 |

### Other alloc families

| address | family | old | new | proof |
|---|---|---|---|---|
| `0x1401a40a0` | `alloc_stride0x3` | `rep_140195830_New` | `VectorStride24_FillCopy` | fill-n: `New(param_2*0x18)`, `cap=block+param_2*3` qwords, per-slot 0x18 element holding an 8-byte inner array |
| `0x14008ddb0` | `alloc_stride0x6` | `rep_140089560_New` | `VectorStride64_Reallocate` | `>>6`, `New(uVar5*0x40)`, memset/memmove, `end=param_2*0x40+p` |
| `0x14001c110` | `alloc_stride0x28` | `rep_14001baa0_API-..._invalid_parameter_noinfo_noreturn` | `Array_AllocAligned` | raw byte allocator: `New(param_2)`, over-aligned `New(param_2+0x27)` with header at -8; **no element stride** |
| `0x14011dc50` | `alloc_stride0xf0` | `rep_140117d80_MSVCP140.DLL::std::_Xlength_error` | `List_AppendObject240` | `New(0xf0)` object (fields clear to +0xd8, `0x3f800000` at +0xc8) plus a 0x18-byte list node |

### `container_array_op_stride0x4` — actually stride 0x30

| address | old | new | proof |
|---|---|---|---|
| `0x140128dc0` | `rep_140120740_New` | `VectorStride48_InsertCopy` | insert-one: `(end-begin)/0x30`, `New(uVar11*0x30)`, `CopyEscadraName` + 2 qwords, `Array_RelocateString48`, `end=uVar1*0x30` |
| `0x140199120` | `rep_14018b140_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `VectorStride48_InsertMove` | insert-one: `/0x30`, `New(uVar11*0x30)`, 11 dwords written, `Array_MoveConstruct48`, `end=uVar1*0xc` dwords |

## Skipped

| address | family | live name | why |
|---|---|---|---|
| `0x140056310` | `alloc_stride0x38` | `rep_140054270_New` | `New(0x38)` is a **record** node, not a vector element: the body computes a rect from `param_2`/`param_3` (four floats at +0x14..+0x24), stores ids at +0x10/+0x28/+0x2c/+0x30, appends the node to a global list `DAT_1403ef0b8` and then probes/inserts into the `newProperty_` rb-tree map. No element stride; owner type not provable. Phase 0's `VectorStride56_Grow` is disproved. |
| `0x140123830` | `container_array_op_stride0x4` | `rep_14011d1d0_New` | grid rebuild, not an array primitive: allocates a temporary 0x10-stride vector of 0x18-byte list headers for `(ScreenHeight-1)/10+1` rows, `Array_Resize24` on `DAT_1439e5ff8` and `DAT_1439e5fb0`, frees the temporary, and finally dispatches the virtual at vtable+0x38. Two different strides (0x10 temp, 0x18 cells); no single provable element type. Phase 0's `Array_ResizeStride4` is disproved. |

## Verification

* All 29 target addresses re-read live: `get_function_by_address` returns the
  new name (29/29).
* All 29 plate comments set through `set_plate_comment` (`status: success`).
* The two skipped addresses still carry their `rep_*` names, untouched.
* No address outside the 31-row scope was modified; no `save_program`.

## Caveats

* The 0x18-node list inserts (seven `List_PushBackNode24*`) are structurally
  identical templates with different payloads/filters. The distinguishing
  suffix is the payload or the filter field, not the container type; if a
  later owner pass identifies the concrete `std::list<T>`, the suffix should be
  refined to the type (the node size 0x18 stays correct).
* `HashMap_InsertStringKeyAlt` (`0x1401a1e90`) is the one-string variant that
  leaves the value string empty. It is close to the already-named
  `HashMap_InsertStringKey` (`0x14018e9c0`, 774 B) but not byte-identical
  (678 B) and lives in a different module.
* `Array_AllocAligned` has no element stride by construction (it takes a byte
  count), so it was named as an allocator rather than with a `Stride` token.
