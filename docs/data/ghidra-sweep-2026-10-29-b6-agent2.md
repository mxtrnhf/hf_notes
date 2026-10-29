# Ghidra sweep batch 6, agent 2 — `rep_*` re-match 0x140000000–0x1400FFFFF

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Scope: every `rep_*` function in `0x140000000–0x1400FFFFF`, excluding
`0x140337000–0x140350510` (agent 1's funclet tail).

**513 `rep_*` functions in scope** (512 real bodies + one 6-byte import thunk at
0x1400e4cc0; 513 rows in the TSV, the 21 renames keep their old label).
**21 renamed, 21 bodies plated. 492 stale labels left; 0 unreadable.**
No `save_program`, no tags, no README/STATUS edits, no commits, no
`create_function`.

| | before | after |
|---|---|---|
| `rep_*` in scope | 513 | 492 |
| renamed | — | 21 |

(The 492 includes one 6-byte import thunk at 0x1400e4cc0, not a body; see
“Scope note”.)

## Confirmation of the b5 finding: the `rep_*` names are stale, not replicas

Batch 5 agent 5 proved this for `0x140000000–0x14006FFFF`. I extended the check
to all 512 bodies in this range with a new pass:

1. **SHA-1 of the exact body bytes** for every function in the program, and a
   comparison of each `rep_*` body against every non-`rep_*` body.
   **0 of 512** `rep_*` bodies is byte-identical to any named function. (Only
   one *structural* twin exists in the whole image, and it is a named→named
   pair.) ICF duplicates would be byte-identical, so the replica premise is
   false here too.
2. **Where the embedded address points** (parsed from `rep_<hex>_<name>`, 496
   rows; 16 rows are synthesised `rep_wrap_0_*` names with no address):
   * **447 inside an unrelated function** (usually mid-instruction),
   * **20 are real function entries**, but the body hash differs from that
     function's body — so the label is still wrong,
   * **11 outside any function** (undefined bytes / gap),
   * **18 point back into the rep function's own body or the excluded tail**.
3. **Names that cannot describe the body:** 85 stale rows carry a `free`
   suffix while their bodies are 100–4800-byte container/game methods; 16
   carry `sqrtf`/`cosf`/`atan2f` while only *calling* the real `sqrtf`/`cosf`;
   one calls `D3DCompileFromFile` and is labelled `MultiByteToWideChar`.

Conclusion: on this build `rep_*` is a signature-database artefact. Every row
in the audit TSV is therefore `stale label` unless the body proved an identity.

## Renames (21) — all with doc plates

### RTTI/vtable-proved destructors and constructors (14)

Class from `vtable[-1] -> CompleteObjectLocator -> TypeDescriptor`, slot from
the vtable, role from the body.

| addr | new name | vtable / RTTI / shape |
|---|---|---|
| 0x140081910 | `ComputeShader_Compile` | slot 0 of 0x140356668/0x140356698 (`ComputeShader`/`CSGlitch`); `D3DCompileFromFile(..., "cs_5_0", 0x800, ...)` then creates the shader through device vtable +0x90, blob at +0x18. |
| 0x140081b40 | `CSGlitch_Destructor` | installs CSGlitch vtable; `~CReObject(this+0x50)`; `ComputeShader_Destructor`. |
| 0x140081b70 | `CSGlitch_ScalarDeletingDestructor` | 0x140356698 slot 3, RTTI `.?AVCSGlitch@@`; chains the two base dtors then `free` on flag. |
| 0x140082c10 | `FileBuf_ScalarDeletingDestructor` | 0x140356790 slot 0, `.?AV?$basic_filebuf@D...@std@@`; `~basic_streambuf` + free on flag. |
| 0x140082c90 | `RenderTarget_ScalarDeletingDestructor` | 0x140356768 slot 0, `.?AVRenderTarget@@`; releases +0x58/+0x50, chains Texture base, free on flag. |
| 0x140082d40 | `TextureSingle_ScalarDeletingDestructor` | 0x140356740 slot 0, `.?AVTextureSingle@@`; releases +0x50/+0x18, chains Texture base, free on flag. |
| 0x1400e7d00 | `Escadra_ScalarDeletingDestructor` | 0x14035e4e0 slot 0, `.?AVEscadra@@`. |
| 0x1400e7dc0 | `IntelPolygon_ScalarDeletingDestructor` | 0x14035dfe8 slot 0, `.?AVIntel_polygon@@`. |
| 0x1400e7e00 | `LastPlayerPosData_ScalarDeletingDestructor` | 0x14035dfa0 slot 0, `.?AULastPlayerPosData@@`; frees the +0x48 Link + `ISerializable_Destructor`. |
| 0x1400e7e80 | `Location_ScalarDeletingDestructor` | 0x14035e670 slot 0, `.?AVLocation@@`; tears down parts, the intrusive item list, +0x2d0/+0x2b8 Links and the +0x288 string. |
| 0x1400e8030 | `MapCraft_ScalarDeletingDestructor` | 0x14035eb28 slot 0, `.?AVMapCraft@@`; frees the +0x310 array. |
| 0x1400e8190 | `Mark_ScalarDeletingDestructor` | 0x14035e040 slot 0, `.?AVMark@@`. |
| 0x1400e81d0 | `Missile_ScalarDeletingDestructor` | 0x14035e998 slot 0, `.?AVMissile@@`; installs `MissileVFTABLE`. |
| 0x14005e290 | `SProperty_Constructor` | installs `SPropertyVFTABLE`, runs `Property::Property`, copies name and value string, stores type tag 2. |

### Body-proved helpers (7)

| addr | new name | evidence |
|---|---|---|
| 0x1400a2ac0 | `String_ThrowInvalidPosition` | 17 B: `std::_Xout_of_range("invalid string position")` + `int3`; sibling of `Vector_ThrowSubscriptOutOfRange`. |
| 0x140006000 | `EscadraName_LessThan` | `compareEscadraString(a,b) >> 31` — strict-less predicate. |
| 0x140017e50 | `CopyCString` | explicit `strlen` loop then `CopyString(dst, src, len)`. |
| 0x140005e20 | `Node_CopyEscadraName` | `CopyEscadraName(dst, this+0xc8)`, returns `dst`. |
| 0x140061dc0 | `LinkedList_ClearFree` | walks an intrusive list, `freeLinkMemory_(node+0x10)`, `free(node)`, re-links the header to itself, zeroes the count. |
| 0x1400fd950 | `List_UnlinkAndFreeNode` | unlinks one node, decrements count, `freeLinkMemory_(node+0x10)`, `free(node)`. |
| 0x14002dda0 | `RbTree_EscadraNameLowerBound` | MSVC `_Lower_bound` walk keyed by `EscadraName` via `compareEscadraString`; returns the out iterator. |

## Stale rows with a partial identity (in the TSV, column 4)

These cannot be uniquely named (they are template instantiations or class-less
stubs) but their identity is known:

* 14 × 52-byte `ShaderData_ResetVTable(); if(flag) free(this)` are the
  **`ConstantBuffer<T>` slot-1 scalar-deleting destructor**; the body is shared
  by every `ConstantBuffer<UCB...>` instantiation (19 vtables), so an
  individual name per address would be wrong. e.g. 0x140089e70 serves
  `ShaderBloom/Blur/Clouds/Color/...`, 0x140087460 serves
  `ConstantBuffer<UCBMatrix@Effect>`.
* 0x140092fb0 — `if (flag) free(this)` deleting-destructor stub, class unknown.
* 0x140006ae0 — `pow(float,int)` forwarding wrapper.
* 0x1400152e0 — `_fdclass() == -1` classification predicate (isfinite-like).
* 0x140013830 — `memmove(dst, src, end-src)`, returns `dst+len`.
* 0x14000de50 — unlink one intrusive node and `free` it (no payload dtor).
* 0x140048bf0 — rate: `field+0x2cc / (GetStats(+0x188)->+0x94 * 60)`.

## Left as `stale label` (492)

Bodies are real, labels are provably unrelated, but no unique name is proven:

* **CRT/std::vector/RbTree machinery** in `0x140000000–0x140070000`
  (`_Change_array`, `_Reallocate_exactly`, `_Destroy_range`, `_Tidy`,
  `_Lower_bound`, `tooLongError`/`_Xlength_error` throw paths). Many are
  structurally identical to an existing named helper; renaming them by analogy
  would create near-duplicate names, which the batch rules forbid.
* **HGE/shader layer** `0x140070000–0x1400B0000` (the `CS*`/`Texture*`
  destructor families not covered above). Their vtables are recorded in
  `/tmp/opencode/vtables.tsv` for a later pass.
* **Game logic** `0x1400B0000–0x140100000` (UI panels, radio text, list
  helpers). Several read/write offsets whose role is not established
  (`+0x94`, `+0x2cc`, `+0x9ac`, `+0x818/+0x820`), so naming would be guessing.

## Scope note

0x1400e4cc0 is a 6-byte import thunk (`jmp _invalid_parameter_noinfo_noreturn`),
not a body; it counts in the 492 and is listed as `stale label`. No function in
agent 1's excluded range was renamed here.

## Output

* TSV: `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`
  `addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`
* Rename/plate reference dump used for the audit: `/tmp/opencode/rep_base.tsv`,
  vtable/RTTI map: `/tmp/opencode/vtables.tsv`.

## Counts

* audited: **513** (512 bodies + 1 thunk)
* renamed + plated: **21**
* stale label left: **492**
* unreadable: **0**
* byte-identical named twins found: **0**
