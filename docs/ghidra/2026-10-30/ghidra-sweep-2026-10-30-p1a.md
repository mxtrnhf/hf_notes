# Ghidra sweep, Phase 1a — funclet owner walk (`0x140336730–0x140350510`)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`. Only the
1.163 program was opened and written; the 1.151 program was never switched to.

Scope: the 40 funclets left open by batch 10 — the 36 with a recorded owner but
no provable identity, the aliased `0x140342380`, and the three CRT EH thunks
`0x14034b6b8/743/75b`. The three CRT thunks were closed by Phase 1b in parallel
(`0x14034b6b8` -> `` `eh_vector_destructor_iterator'_EhCleanup_0x60 ``,
`0x14034b743` -> `CRT_AccessViolationFilter`, `0x14034b75b` ->
`CRT_SehFilterExeThunk`); this pass only records them.

**Result: 37 funclets resolved by the walk; 20 closed (18 renamed + 2 created),
17 left open with reasons, 3 closed by Phase 1b. 17 owners renamed + plated;
2 further owners were renamed concurrently by another session and the matching
funclets were aligned to the live names.** No `save_program`, no tags, no
README/STATUS edits, no commit. Every write went through the plugin's
transactional endpoints, so no transaction was leaked.

| | count |
|---|---|
| open funclets in scope | **40** |
| resolved to a primary parent | **37** (+3 CRT) |
| closed (renamed) | **18** |
| closed (created + named) | **2** |
| owners renamed + plated by this pass | **17** |
| owners renamed concurrently by another session | **2** |
| still open | **17** |
| closed by Phase 1b | **3** |

## 1. Method — the binary uses `__CxxFrameHandler4`, not the classic FuncInfo

The first attempt to scan for `0x19930520/21/22` found **zero** hits in the whole
image. The personality routine behind every EHANDLER `.pdata` row is
`__CxxFrameHandler4` (IAT thunk `0x140336594`). MSVC's FH4 removed the magic
number and replaced the fixed tables with a compressed FuncInfo4. The walk is:

1. **`.pdata`**: `0x148078000–0x14808c1ff`, 6863 `RUNTIME_FUNCTION` records of
   12 bytes (`BeginRVA`, `EndRVA`, `UnwindRVA`).
2. **UNWIND_INFO**: at `imageBase+UnwindRVA`. `version_flags = byte[0]`,
   `count = byte[2]`. If `flags & 2` (UNW_FLAG_EHANDLER) the handler block is at
   `unwind + 4 + 2*count`, padded to 4 bytes. The block is
   `ULONG handlerRVA; ULONG FuncInfo4RVA;`.
3. **Handler RVAs observed**: `0x334494` (135), `0x336594` (795, the FH4 thunk),
   `0x334510` (447), `0x3365ca` (2). All four carry the same FH4 encoding, so all
   were parsed (restricting to `0x336594` alone loses ~580 parents and is why
   the first pass left 7 funclets unresolved).
4. **FuncInfo4** at `imageBase+FuncInfo4RVA`:
   `header` byte (bit0 isCatch, bit1 isSeparated, bit2 BBT, bit3 UnwindMap,
   bit4 TryBlockMap, bit5 EHs, bit6 NoExcept); optional `bbtFlags` compressed
   int; then `dispUnwindMap` (int32), `dispTryBlockMap` (int32),
   `dispIPtoStateMap` (int32), and `dispFrame` (compressed int) only for catch
   funclets. All `disp*` are image-relative.
5. **Compressed integers** are the .NET encoding: the low 4 bits of the current
   byte select a length/shift (`s_negLengthTab` / `s_shiftTab`); the value is
   read from the four bytes ending at that byte. In a walker:
   `v = readU32(p - neg - 4) >> shift; p -= neg;` (note `neg` is negative).
6. **Funclet set**: an `UnwindMapEntry4` is `(nextOffset << 2) | type`, then for
   types 1/2 a 4-byte `action` RVA and a compressed `object` offset, for type 3
   a 4-byte `action` RVA. A type-3 `action` is a per-parent cleanup funclet; the
   `action` of types 1/2 is a shared destructor and is not a per-parent funclet.
   `TryBlockMap4` → `HandlerMap4` gives catch funclets via `dispOfHandler` and
   the continuation addresses; both are relative to the parent unless
   `contIsRVA` is set.
7. **Owner**: the primary function whose map references the funclet. A catch
   funclet may itself own a FuncInfo4 (isCatch=1) that references a nested
   handler; such a chain is followed upward until the first address that is not
   itself referenced by any map. This is what resolves `0x140342380`.

Validation: the walk reproduces the already-closed rows of
`funclet-ownership-2026-10-29.tsv` exactly (e.g. `0x1403372d0`/`0x1403372f0` →
`0x140017e70`, `0x140342300`/`0x1403423c0` → `0x14019abe0`) and reproduces the
batch-10 owner for every one of the 36 contested rows. It is a data-driven walk,
not address adjacency.

The walker was run offline against the raw `.pdata`/`.rdata` extracts
(`pdata_raw.bin`, `rdata_raw.bin`) after the AWT script thread hung on the
unbounded handler-count loop noted on the blackboard; the offline version clamps
all counts and validates pointers. Every result was then re-checked against the
live program with `get_function_by_address`.

## 2. Resolved table

`closed` = renamed/plated this pass; `closed_p1b` = done by Phase 1b.

| funclet | owner (resolved) | member | family | status | basis / reason |
|---|---|---|---|---|---|
| `0x1403368e0` | `0x140006670 / 0x1400dfa70` | `0x70` | rethrow | **open** | handler referenced by two primary parents (shared ICF catch funclet) |
| `0x140336c40` | `0x1400112c0 / 0x14011ba00` | `0x60` | vdtor | **open** | ICF-shared by WriteString and WriteCharArray |
| `0x140336d60` | `0x1400127f0` | `0x50` | rethrow | **closed** | created + named VectorStride4_InsertValue_EhCleanup_0x50 |
| `0x140336d90` | `0x1400128f0` | `0x50` | rethrow | **closed** | named VectorStride8_InsertValue_EhCleanup_0x50 |
| `0x140336dc0` | `0x140012a30 / 0x1402e5a00` | `0x60` | rethrow | **open** | handler referenced by two primary parents (shared ICF catch funclet) |
| `0x140336e30` | `0x140013160` | `0x80` | rethrow | **closed** | named VectorStride4_InsertRange_EhCleanup_0x80 |
| `0x140336e70` | `0x140336ea0 et al.` | `0x88` | other | **open** | nested catch-funclet chain; no unique primary parent |
| `0x140336f50` | `0x1400146e0 / 0x14016fa00 / 0x1401a0460` | `0x50` | rethrow | **open** | handler referenced by three primary parents (shared ICF catch funclet) |
| `0x1403377e0` | `0x140023580` | `0x48` | freeField | **open** | Body vtable slot 81; GUI label builder but slot order does not prove the method name |
| `0x140338110` | `0x140058270` | `0x80` | rethrow | **closed** | named VectorStride48_InsertMove_EhCleanup_0x80 |
| `0x1403392f0` | `0x140089300` | `0x60` | rethrow | **closed** | named VectorStride36_ResizeDefault_EhCleanup_0x60 |
| `0x140339370` | `0x140089b90` | `0x60` | rethrow | **closed** | named VectorStride20_ResizeDefault_EhCleanup_0x60 |
| `0x140339430` | `0x14008ba20` | `0x60` | rethrow | **closed** | named VectorStride24_ResizeDefaultAlt_EhCleanup_0x60 |
| `0x140339480` | `0x14008c5a0` | `0x60` | rethrow | **closed** | named VectorStride40_ResizeDefault_EhCleanup_0x60 |
| `0x140339700` | `0x140090fd0` | `0x60` | rethrow | **closed** | named VectorStride56_ResizeDefault_EhCleanup_0x60 |
| `0x1403399d0` | `0x14009b090` | `0x60` | rethrow | **closed** | named VectorStride12_ResizeDefault_EhCleanup_0x60 |
| `0x14033c4d0` | `0x1400bb800` | `0x80` | rethrow | **closed** | named VectorStride8_InsertRange_EhCleanup_0x80 |
| `0x14033c700` | `0x1400c12a0` | `0xe8` | linkFree | **open** | editor/map tick; operation name not provable |
| `0x14033c730` | `0x1400c12a0` | `0x118` | linkFree | **open** | same owner as 0x14033c700 |
| `0x14033cbd0` | `0x1400ddcd0` | `0x38` | string | **open** | per-frame tutorial trigger cascade; only a summary is provable |
| `0x14033cc00` | `0x1400ddcd0` | `0x38` | string | **open** | same owner as 0x14033cbd0 |
| `0x14033cc30` | `0x1400ddcd0` | `0x38` | string | **open** | same owner as 0x14033cbd0 |
| `0x14033cc80` | `0x1400df450` | `0x60` | rethrow | **closed** | named VectorStride32_InsertDefault_EhCleanup_0x60 |
| `0x14033cd50` | `0x1400dfde0` | `0x70` | rethrow | **closed** | named VectorStride12_InsertValue_EhCleanup_0x70 |
| `0x14033ce50` | `0x1400e0370` | `0x50` | rethrow | **closed** | created + named VectorStride8_InsertNodeRange_EhCleanup_0x50 |
| `0x14033dab0` | `0x1400f4210` | `0x30` | linkFree | **open** | refuel-partner evaluation; not separable from Escadra_FindRefuelTarget |
| `0x14033dd30` | `0x140104df0` | `0x70` | linkFree | **open** | location-map draw step; not distinguishable from the other displayLables helpers |
| `0x14033e310` | `0x14011e440` | `0x60` | rethrow | **closed** | named VectorStride4_ResizeFill_EhCleanup_0x60 |
| `0x14033e4e0` | `0x140121c50` | `0x88` | freeField | **open** | FX spawner; effect name is a parameter, no distinguishing string |
| `0x14033e510` | `0x140122200` | `0xe0` | freeField | **open** | FX spawner; effect name is a parameter, no distinguishing string |
| `0x1403410f0` | `0x14016f6a0 / 0x140198130 / 0x140198410` | `0x80` | rethrow | **open** | handler referenced by three primary parents (shared ICF catch funclet) |
| `0x140341460` | `0x140183e00 / 0x140197210` | `0x60` | rethrow | **open** | handler referenced by two primary parents (shared ICF catch funclet) |
| `0x140341e10` | `0x140197510` | `0xa0` | rethrow | **closed** | named VectorStride40_InsertCopy_EhCleanup_0xa0 |
| `0x140341ef0` | `0x1401986f0` | `0x70` | rethrow | **closed** | named VectorStride24_InsertValue_EhCleanup_0x70 |
| `0x140341f50` | `0x140198ac0` | `0x60` | rethrow | **closed** | named VectorStride16_InsertValue_4_EhCleanup_0x60 |
| `0x140341fb0` | `0x140198eb0` | `0x70` | rethrow | **closed** | named VectorStride12_InsertValueAlt_EhCleanup_0x70 |
| `0x140342380` | `0x14019abe0` | `0xa0` | rethrow | **closed** | nested 0x342380 <- 0x3423c0 (catch funclet) <- root VectorString32_InsertRange; named VectorString32_InsertRange_EhCleanup_0xa0_2 |
| `0x14034b6b8` | `0x140334174` | `0x60` | other | **closed_p1b** | Phase 1b: `eh_vector_destructor_iterator'_EhCleanup_0x60 |
| `0x14034b743` | `0x140334358` | `-` | nobody | **closed_p1b** | Phase 1b: CRT_AccessViolationFilter |
| `0x14034b75b` | `0x140334c54` | `-` | other | **closed_p1b** | Phase 1b: CRT_SehFilterExeThunk |

### The aliased `0x140342380`

The recorded owner `0x1403423c0` is not a primary function: it is a catch funclet
of `VectorString32_InsertRange` (`0x14019abe0`). The walk shows
`0x140342380 <- handler of 0x1403423c0 (try 2)` and
`0x1403423c0 <- handler of 0x14019abe0 (try 2)`. The funclet's body is an
end-pointer rollback: read `puVar1 = *(frame+0xb0)`, free the vector at
`frame+0xa0` through `EhCleanup_FreeWrapper`, restore `*puVar1 = *(frame+0xb8)`,
then `_CxxThrowException`. The root owner is therefore
`VectorString32_InsertRange`; the funclet is named
`VectorString32_InsertRange_EhCleanup_0xa0_2` (the `_2` distinguishes it from
the sibling `0x1403422b0`). This is the case the batch-10 note flagged as
unprovable from the body alone — the FuncInfo4 chain proves it.

## 3. Owners renamed (17)

Stride is proven from the allocation size / index scale in the owner body, not
from the funclet. The old labels were stale `rep_*` ICF-replica labels (mostly
CRT imports) and were provably wrong for the body.

| owner | old label | new name | proof |
|---|---|---|---|
| `0x1400128f0` | `rep_..._Change_array` | **VectorStride8_InsertValue** | single-element insert; `>>3`, `AllocateArrayOf8Byte`, one value written into the gap |
| `0x140013160` | `rep_..._Change_array` | **VectorStride4_InsertRange** | range insert; `>>2` / `*4`, `memmove` of the source range |
| `0x140058270` | `rep_...free` | **VectorStride48_InsertMove** | `New(n*0x30)`, `Object_MoveRange30` move-construct |
| `0x140089300` | `rep_...memmove` | **VectorStride36_ResizeDefault** | resize; `*0x24`, zero-fill of the new range |
| `0x140089b90` | `rep_...memmove` | **VectorStride20_ResizeDefault** | resize; `*0x14`, zero-fill |
| `0x14008ba20` | `rep_...memmove` | **VectorStride24_ResizeDefaultAlt** | resize; `*0x18`, zero-fill (name `Alt` because `VectorStride24_ResizeDefault` already exists at `0x1402e67e0`) |
| `0x14008c5a0` | `rep_...New` | **VectorStride40_ResizeDefault** | resize; `*0x28`, zero-fill |
| `0x140090fd0` | `rep_...New` | **VectorStride56_ResizeDefault** | resize; `*0x38`, zero-fill |
| `0x14009b090` | `rep_...invalid_parameter` | **VectorStride12_ResizeDefault** | resize; `*0xc`, zero-fill |
| `0x1400bb800` | `rep_...memmove` | **VectorStride8_InsertRange** | range insert; `>>3`, `AllocateArrayOf8Byte` |
| `0x1400dfde0` | `rep_...invalid_parameter` | **VectorStride12_InsertValue** | single-element insert; `*0xc`, value copied into the gap |
| `0x14011e440` | `rep_...New` | **VectorStride4_ResizeFill** | resize-fill; `*4`, new slots filled from the value pointer |
| `0x140197510` | `rep_...vector<CHN*>` | **VectorStride40_InsertCopy** | copy-insert; `*0x28`, `AllocArrayStride40`, `Array_CopyConstruct40Vector`, nested-vector copy |
| `0x1401986f0` | `rep_...free` | **VectorStride24_InsertValue** | single-element insert; `*0x18` |
| `0x140198eb0` | `rep_...free` | **VectorStride12_InsertValueAlt** | single-element insert; `*0xc` (name `Alt` because `0x1400dfde0` takes the plain name) |
| `0x1400127f0` | `rep_..._Change_array` | **VectorStride4_InsertValue** | single-element insert; `>>2`, one 4-byte value into the gap |
| `0x1400e0370` | `rep_...memmove` | **VectorStride8_InsertNodeRange** | range insert from a linked node range; `>>3`, `AllocateArrayOf8Byte`, value at `node[2]` |

Two further owners were renamed by another session between the resolution pass
and the apply pass; this pass did not touch them and aligned the matching
funclets to the live names:

| owner | live name | matched funclet |
|---|---|---|
| `0x1400df450` | **VectorStride32_InsertDefault** | `0x14033cc80` -> `VectorStride32_InsertDefault_EhCleanup_0x60` |
| `0x140198ac0` | **VectorStride16_InsertValue_4** | `0x140341f50` -> `VectorStride16_InsertValue_4_EhCleanup_0x60` |

## 4. Funclets closed (20)

All funclet plates record the owner, the frame member, the release helper and the
rethrow. Bodies were read before naming.

| funclet | new name |
|---|---|
| `0x140336d60` | **VectorStride4_InsertValue_EhCleanup_0x50** (created) |
| `0x140336d90` | **VectorStride8_InsertValue_EhCleanup_0x50** |
| `0x140336e30` | **VectorStride4_InsertRange_EhCleanup_0x80** |
| `0x140338110` | **VectorStride48_InsertMove_EhCleanup_0x80** |
| `0x1403392f0` | **VectorStride36_ResizeDefault_EhCleanup_0x60** |
| `0x140339370` | **VectorStride20_ResizeDefault_EhCleanup_0x60** |
| `0x140339430` | **VectorStride24_ResizeDefaultAlt_EhCleanup_0x60** |
| `0x140339480` | **VectorStride40_ResizeDefault_EhCleanup_0x60** |
| `0x140339700` | **VectorStride56_ResizeDefault_EhCleanup_0x60** |
| `0x1403399d0` | **VectorStride12_ResizeDefault_EhCleanup_0x60** |
| `0x14033c4d0` | **VectorStride8_InsertRange_EhCleanup_0x80** |
| `0x14033cc80` | **VectorStride32_InsertDefault_EhCleanup_0x60** |
| `0x14033cd50` | **VectorStride12_InsertValue_EhCleanup_0x70** |
| `0x14033ce50` | **VectorStride8_InsertNodeRange_EhCleanup_0x50** (created) |
| `0x14033e310` | **VectorStride4_ResizeFill_EhCleanup_0x60** |
| `0x140341e10` | **VectorStride40_InsertCopy_EhCleanup_0xa0** |
| `0x140341ef0` | **VectorStride24_InsertValue_EhCleanup_0x70** |
| `0x140341f50` | **VectorStride16_InsertValue_4_EhCleanup_0x60** |
| `0x140341fb0` | **VectorStride12_InsertValueAlt_EhCleanup_0x70** |
| `0x140342380` | **VectorString32_InsertRange_EhCleanup_0xa0_2** |

The two created functions required a blackboard post and one wait cycle
(`**@p1a -> creation**` on `blackboard_p0p1.md`). Both `.pdata` extents were
checked to be real code (`0x140336d60-0x140336d87`, `0x14033ce50-0x14033ce8d`)
and both end inside the extent.

## 5. Still open (17) — reasons

### Shared handlers (7) — naming after one parent would be wrong

| funclet | parents |
|---|---|
| `0x1403368e0` | `0x140006670`, `0x1400dfa70` |
| `0x140336c40` | `0x1400112c0` (WriteString), `0x14011ba00` (WriteCharArray) |
| `0x140336dc0` | `0x140012a30`, `0x1402e5a00` |
| `0x140336e70` | nested catch-funclet chain (`0x140336ea0`, `0x140336f00`, `0x14033c510`, `0x14033c580`); no unique primary parent |
| `0x140336f50` | `0x1400146e0`, `0x14016fa00`, `0x1401a0460` |
| `0x1403410f0` | `0x14016f6a0`, `0x140198130`, `0x140198410` |
| `0x140341460` | `0x140183e00`, `0x140197210` |

These are ICF-folded catch funclets; the project convention keeps shared
funclets unnamed. One line each: *handler referenced by 2+ primary parents, so any
single-owner name would be wrong.*

### Subsystem / FX owners whose operation is not provable (10)

| funclet | owner | reason |
|---|---|---|
| `0x1403377e0` | `0x140023580` | Body vtable slot 81 — builds a Replica label GUI, but slot order does not prove the method name (batch 10 reached the same conclusion) |
| `0x14033c700` | `0x1400c12a0` | editor/map tick: fills a body vector, dedups, handles the editor preselect back-stack; operation name not separable |
| `0x14033c730` | `0x1400c12a0` | same owner |
| `0x14033cbd0` | `0x1400ddcd0` | per-frame tutorial trigger cascade (`TUTORIAL_*`); only a summary is provable |
| `0x14033cc00` | `0x1400ddcd0` | same owner |
| `0x14033cc30` | `0x1400ddcd0` | same owner |
| `0x14033dab0` | `0x1400f4210` | Escadra refuel-partner evaluation; cannot be separated with certainty from `Escadra_FindRefuelTarget` |
| `0x14033dd30` | `0x140104df0` | location-map draw step; not distinguishable from the other `displayLables*` helpers |
| `0x14033e4e0` | `0x140121c50` | FX spawner; the effect name is always a parameter and there is no distinguishing string/RTTI/vftable store |
| `0x14033e510` | `0x140122200` | FX spawner; same as `0x140121c50` |

### Phase 1b (3) — closed in parallel

`0x14034b6b8`, `0x14034b743`, `0x14034b75b` are CRT EH glue. Phase 1b named and
plated them; see `ghidra-sweep-2026-10-30-p1b.md` §1.

## 6. Data-file update

`funclet-ownership-2026-10-29.tsv` now has a trailing `status` column. The 20
rows closed here are `closed`, the 17 rows still open in this scope are `open`,
and the 3 Phase 1b rows are `closed_p1b`; all other rows are blank. The
`0x140342380` row was corrected from the neighbour owner `0x1403423c0` to the
root `0x14019abe0`. Three closed funclets had no row (`0x140336d60`,
`0x140336d90`, `0x140336e30`); rows for them and for the five no-row shared
handlers were appended at the end without reordering the existing table.
