# Ghidra sweep, batch 5 agent 3 — `0x140340000–0x140347FFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range contained **354 functions**: 9 already named by batch 4 (agent 2), 345 unnamed
(`FUN_*`/`rep_*`). **32 renamed, all plated. 313 left unnamed.**

No `create_function`, no `save_program`, no tags, no README/STATUS edits, no commit.

## What the range actually contains

This is the **first half of the compiler tail** and nothing else. There are **no
`atexit` static-object destructors in this range**: cluster B of batch 4
(`void f(void)` global destructors, 0x14034b780–0x140350500) starts at
`0x14034b780`, i.e. inside **agent 4's** range (`0x140348000–0x140350510`).
Likewise node `dtor$1` (0x14034a550) is outside this range. So there is nothing to
pair with an initialiser table here, and no coordination with agent 4 was needed
for naming. See "Hand-off to agent 4" below for the boundary detail.

Everything in `0x140340150–0x140347fff` is MSVC `/EH` cleanup funclets plus `/GS`
and `_eh_vector_destructor_iterator_` helpers, with the standard
`(int exceptionType, void* frame)` ABI.

## Survey method

1. `run_script_inline` over `getFunctionManager().getFunctions(lo,true)`, printing
   name, size and a normalised instruction signature for every `FUN_*`/`rep_*`.
   Result: **354 functions / 345 unnamed**.
2. Clustered by instruction shape + callee set. Only **46 shape clusters** exist,
   and the three large ones are 171 / 107 / 8 members. Unlike the batch-4 note's
   claim of "many byte-identical copies", the copies here are **not byte
   identical**: each carries a different frame displacement, so an exact-body
   grouping yields 333 groups. The redundancy is a *template* repeated with a
   different frame offset.
3. Therefore the grouping unit used is **destroying callee + frame offset** (the
   instruction from the batch-5 blackboard), not exact bytes. One representative
   per distinct `(template, offset family)`; the plate states the sibling count.
4. Verified 8 representatives by decompiling before naming; all 32 plates were
   applied in one transaction afterwards.

## Cluster map (whole range)

| cluster | callee / body | count | named in range |
|---|---|---|---|
| A1 member-string, direct `String_Tidy(frame+S)` under guard bit at `frame+G` | `String_Tidy` | 167 | `EhCleanup_MemberString20/30/44/50/60/64/68/70/74/78/7C/A0/A8` (13) + pre-existing `EhCleanup_MemberString88` (0x140340150) |
| A2 member-string through pointer `String_Tidy(*(frame+S))` | `String_Tidy` | 3 | `EhCleanup_PointerToString` (0x140344480) |
| A3 `free(*(void**)(frame+off))` | `free` | 107 | `EhCleanup_FreeField20/28/30/38/40/60/68/78/80/88/108/110/118` (13) + pre-existing `EhCleanup_FreeField70` (0x140344030) |
| A4 `freeLinkMemory_(frame+link)` under guard bit | `freeLinkMemory_` | 8 | `EhCleanup_MemberLink` (0x140340250) |
| A5 `basic_ios::~basic_ios(frame+disp)` under guard bit | `~basic_ios` (ext) | 9 | pre-existing `EhCleanup_IosDestructor` (0x140341b90) |
| A6 `basic_ios::~basic_ios(*(frame+p)+0xa8)` under guard bit | `~basic_ios` (ext) | 2 | `EhCleanup_IosDestructorIndirect` (0x140341b20) |
| A7 `basic_ios::setstate(failbit)`, returns 0 | `setstate` (ext) | 2 | pre-existing `EhCleanup_IosSetState` (0x140341960) |
| A8 `_eh_vector_destructor_iterator_` | `_eh_vector_destructor_iterator_` | 2 | `EhCleanup_StringVector32x16` (0x1403448b0); pre-existing StringVector40x18 / LinkVector24x4 elsewhere |
| A9 `_CxxThrowException` + partial-array destroy | `_CxxThrowException` | 44 | pre-existing `EhCleanup_ArrayThenRethrow` (0x140341ca0) only |
| A10 pointer-fixup / insert rollback + rethrow | `_CxxThrowException` | 2 | `EhCleanup_RollbackThenRethrow` (0x140342460), `EhCleanup_StringVectorInsertRollback` (0x140342300); pre-existing `EhCleanup_InsertRollback` (0x140342490) |

Counts of A1/A3 include the pre-existing `EhCleanup_MemberString88` and
`EhCleanup_FreeField70` members. The 46 raw shape clusters are just A1/A3/A9 split
by offset/destroy routine; the table above is the semantic map.

### A1 — guard offsets and family sizes

`guard 0x20` 1, `0x30` 1, `0x44` 3, `0x50` 1, `0x60` 60, `0x64` 5, `0x68` 13,
`0x70` 43, `0x74` 17, `0x78` 4, `0x7c` 2, `0x88` 15, `0xa0` 1, `0xa8` 1.
The guard is a bitfield word; the tested bit varies (bit 1 in most, bit 2/4/8 in
some). The string offset is independent of the guard offset — e.g. guard `0x70`
covers strings at 0x78…0xfe0, guard `0x88` covers 0xc0…0xf40. That is why the
family is keyed by guard offset only.

### A3 — field offsets and family sizes

`+0x20` 2, `+0x28` 3, `+0x30` 23, `+0x38` 5, `+0x40` 2, `+0x60` 5, `+0x68` 2,
`+0x70` 21, `+0x78` 12, `+0x80` 3, `+0x88` 4, `+0x108` 2, `+0x110` 2, `+0x118` 2;
the remaining 21 functions free a singleton offset (`0x48…0x1a8`). The batch-4
note's "106 at frame+0x38" is not what the disassembly shows: `+0x38` has 5
members and `+0x30` is the largest (23). `+0x38` now has its own name.

## Renames (32, all plated)

| addr | name | siblings |
|---|---|---|
| 0x140342e60 | `EhCleanup_MemberString20` | guard 0x20, str 0x58 (1) |
| 0x140344550 | `EhCleanup_MemberString30` | guard 0x30, str 0x88 (1) |
| 0x140345a90 | `EhCleanup_MemberString44` | guard 0x44, str 0xa8 (3) |
| 0x1403458e0 | `EhCleanup_MemberString50` | guard 0x50, str 0xa0 (1) |
| 0x140346190 | `EhCleanup_MemberString60` | guard 0x60, str 0x100 (60) |
| 0x140343e00 | `EhCleanup_MemberString64` | guard 0x64, str 0x118 (5) |
| 0x1403432c0 | `EhCleanup_MemberString68` | guard 0x68, str 0x80 (13) |
| 0x1403404f0 | `EhCleanup_MemberString70` | guard 0x70, str 0x8a0 (43) |
| 0x140345010 | `EhCleanup_MemberString74` | guard 0x74, str 0x1728 (17) |
| 0x140342ca0 | `EhCleanup_MemberString78` | guard 0x78, str 0xd0 (4) |
| 0x1403436b0 | `EhCleanup_MemberString7C` | guard 0x7c, str 0x190 (2) |
| 0x1403475c0 | `EhCleanup_MemberStringA0` | guard 0xa0, str 0x150 (1) |
| 0x140344900 | `EhCleanup_MemberStringA8` | guard 0xa8, str 0x110 (1) |
| 0x140344480 | `EhCleanup_PointerToString` | pointer member, 3 |
| 0x140342970 | `EhCleanup_FreeField20` | 2 |
| 0x140342bf0 | `EhCleanup_FreeField28` | 3 |
| 0x140342fd0 | `EhCleanup_FreeField30` | 23 (largest free family) |
| 0x140340f60 | `EhCleanup_FreeField38` | 5 |
| 0x140347430 | `EhCleanup_FreeField40` | 2 |
| 0x140341240 | `EhCleanup_FreeField60` | 5 |
| 0x1403433e0 | `EhCleanup_FreeField68` | 2 |
| 0x140343980 | `EhCleanup_FreeField78` | 12 |
| 0x140343260 | `EhCleanup_FreeField80` | 3 |
| 0x140343500 | `EhCleanup_FreeField88` | 4 |
| 0x140343480 | `EhCleanup_FreeField108` | 2 |
| 0x140343a20 | `EhCleanup_FreeField110` | 2 |
| 0x1403444e0 | `EhCleanup_FreeField118` | 2 |
| 0x140340250 | `EhCleanup_MemberLink` | `freeLinkMemory_`, 8 |
| 0x140341b20 | `EhCleanup_IosDestructorIndirect` | `*(frame+0x30)+0xa8`, 2 |
| 0x1403448b0 | `EhCleanup_StringVector32x16` | 0x20 x 0x10 strings |
| 0x140342460 | `EhCleanup_RollbackThenRethrow` | single pointer fixup |
| 0x140342300 | `EhCleanup_StringVectorInsertRollback` | string-vector insert |

`rep_*` anchors were avoided on purpose: several free-field funclets are labelled
`rep_wrap_0_..._free` by ICF even though their body is a `(frame+off)` funclet and
not the `free` wrapper (e.g. 0x140341260 `+0x30`, 0x1403429b0 `+0x40`). Those are
correctly excluded from §4 "provably wrong name" territory because the *target*
they replicate is still `free`; the bodies simply call it with a frame field.
FUN_ anchors were chosen instead.

## Deliberately left — 313

| what | count | reason |
|---|---|---|
| A1 member-string copies of named offset families | 153 | same template and same guard offset as a named representative; only the string offset differs, and the plate documents the range of offsets |
| A3 free-field copies | 93 | same template as a named representative; per-offset names for singletons would encode only the number that is already in the disassembly |
| A9 partial-array-destroy-then-rethrow | 43 | 44 distinct destroy routines (`Array_DestroyRange240Link`, `RbTree_FreeAllNodes`, `DeleteArray56`, `deallocate`, …) but one template; batch 4's single `EhCleanup_ArrayThenRethrow` plate covers the mechanism, and naming each would disclose the destroyed container type without adding navigation value |
| A8/A7/A5/IOS copies | 4 | same body as a named representative |
| `rep_*` ICF replicas | 20 | already named after their real target (CRT `free`, `deallocate`, `_CxxThrowException`, `~basic_ios`, `setstate`) |

## Hand-off to agent 4

* Destructor cluster B starts at **0x14034b780**, not in this range. The first
  `void f(void)` global destructors and their `atexit` pairing are entirely
  `0x14034b780+`.
* `_eh` funclets continue to 0x14034b390 (batch-4 figure); my last funclet-shaped
  entries are 0x140347b90/0x140347c30. `0x140347c30` is
  `rep_14031c6b0_..._CxxThrowException` and was left as a replica.
* The 9 pre-existing names in my half are unchanged: `EhCleanup_MemberString88`
  (0x140340150), `EhCleanup_IosSetState` (0x140341960), `EhCleanup_IosDestructor`
  (0x140341b90), `EhCleanup_ArrayThenRethrow` (0x140341ca0),
  `EhCleanup_InsertRollback` (0x140342490), `EhCleanup_CHNPointerVector`
  (0x140342c60), `EhCleanup_StringVector40x18` (0x140343860),
  `EhCleanup_FreeField70` (0x140344030), `EhCleanup_LinkVector24x4`
  (0x140346f80).

## Counts

* total functions in range: **354** (9 were already named)
* renamed this pass: **32** (all plated)
* named in range now: **41**
* named-by-me-but-with-misleading-sibling-name: 0
* `FUN_*`/`rep_*` left: **313**
* created: **0**
