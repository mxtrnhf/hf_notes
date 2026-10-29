# Ghidra sweep, batch 6 agent 1 — `/EH` funclet ownership (unwind-table pass)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range `0x140337000–0x140350510` (the compiler tail). **448 funclets renamed and
plated; all 926 funclets in the range now have a proven owner.**

No `create_function`, no `save_program`, no tags, no README/STATUS edits, no
commit. Nothing outside `0x140337000–0x14034b77f` was modified (the
`atexit`-destructor cluster above it was not touched, and no `rep_*` was
touched).

Output: `hf_notes/docs/data/funclet-ownership-2026-10-29.tsv` (926 rows,
`funclet_addr → owner_addr → owner_name → member_offset → family → evidence`).

## The open question this pass closes

Batches 4 and 5 all stopped at the same wall: every funclet body has exactly one
xref, from `.pdata`, and the *funclet's own* `RUNTIME_FUNCTION` gives no owner.
This pass confirms why, and gets the owner a different way.

### 1. `.pdata` (RUNTIME_FUNCTION array)

The block Ghidra calls `.pdata` is `0x148078000–0x14808c1ff` (82432 bytes =
6869 records of 12 bytes; `BeginAddress`/`EndAddress`/`UnwindInfoAddress`, all
image-base-relative RVAs). 6863 records are non-empty and sorted by
`BeginAddress`. The `0x1480xxxxx` references seen from functions are exactly the
`BeginAddress` field of one of these records — they are not vtables.

`UNWIND_INFO` parse: `byte0 = version:3 | flags:5`, then `SizeOfProlog`,
`CountOfCodes`, `FrameRegister/FrameOffset`, then `CountOfCodes` 2-byte slots,
**padded to a 4-byte boundary when `CountOfCodes` is odd**, then the handler RVA
(if `UNW_FLAG_EHANDLER`/`UHANDLER`), then the chained triple (if `CHAININFO`).
Skipping the padding silently corrupted the first attempt (handler values read
as `0x44940000` instead of `0x140334494`).

Handler census (1300 distinct handler-data blobs, 1382 RUNTIME_FUNCTIONs):

| handler | functions |
|---|---|
| `__CxxFrameHandler4` (`0x140336594`) | 795 |
| `__GSHandlerCheck_EH4` (`0x140334510`) | 447 |
| `__GSHandlerCheck` (`0x140334494`) | 135 |
| `0x1403365ca` (unnamed, 5 functions) | 5 |

There is **no FH3 data** anywhere in the image (no `0x19930522` `FuncInfo`
magic), so everything is the compressed FH4 format.

### 2. Why the funclet's own unwind record cannot give the owner

The 926 `RUNTIME_FUNCTION` records with `BeginAddress` in
`0x140337000–0x14034b77f` do **not** share their parent's `UnwindInfoAddress`.
They all point at one generic 6-byte-prolog record at `0x1403822b8`, e.g.

```
0x1403372d0 U=0x1403822b8   0x14033f9b0 U=0x1403822b8   0x140344550 U=0x1403822b8
```

(The other 233 `RUNTIME_FUNCTION`s in the assigned range,
`0x14034b780–0x140350510`, are batch-5 agent 4's `atexit` static-object
destructor cluster — `void f(void)`, no EH data, none of them referenced from a
`FuncInfo4`. A naive scan of all of `.rdata` for a destructor's address produces
86 spurious hits there; restricting the search to the handler-data windows, as
described next, removes all 86. That is the main reason the window bound is used
rather than a free scan.)

### 3. The link that works: the parent's FUNCINFO4 funclet list

For every function whose `UNWIND_INFO` carries a handler, the handler data (blob
start = `U + 4 + 2*CountOfCodes [+2 pad] + 4`) is that function's `FuncInfo4`.
Blob end = the next distinct blob start in `.rdata`, which is a sound bound
because handler data is emitted into one contiguous `.rdata` run. For each blob
the pass scans for 4-byte little-endian values that land in
`[0x140337000, 0x14034b780)`; every hit is a funclet address, and the blob's
`BeginAddress` is that funclet's owner. The scan is unaligned on purpose: the
funclet list is a run of `(1 tag byte, u32 funclet RVA)` records, so the RVAs
never sit on a 4-byte boundary.

Verification that this is the real funclet list and not coincidence:

* 6863 records × ~440 KB of `.rdata` gives an expected false-positive count of
  ~0.03 for the whole range; 1436 distinct addresses were found, all of them
  decode as funclet-shaped code at exactly the referenced byte.
* 926 of the hits are `RUNTIME_FUNCTION.BeginAddress` values; the rest are
  intra-funclet thunks (below).
* Independent structural check: for every single-owner funclet the extracted
  member offset is **inside** the owner's body (`offset < owner size`) except two
  cases, both explained in §6.
* The three `Captain`-destroying funclets `0x14033f9b0/0x14033f9f0/0x14033fa30`
  (batch-5 agent 2's `captain` family) come out as three consecutive records of
  one blob whose owner is `!ClickFunc` (`0x14012f120`, 62272 bytes) — i.e. one
  class with three shipping containers at `+0x28a0/+0x27f0/+0x2840`, exactly the
  shape the bodies show.

### 4. Coverage

| | count |
|---|---|
| `RUNTIME_FUNCTION`s in the assigned range | 1159 |
| … of which in the funclet half (`< 0x14034b780`) | 926 |
| … of which `atexit` destructors (not funclets, not mapped) | 233 |
| **funclets in range (`0x140337000–0x14034b77f`)** | **926** |
| funclets with a proven owner | **926 (100 %)** |
| funclets with exactly one owner | 829 |
| funclets shared by 2+ owners (ICF) | 97 |
| funclets that also have a Ghidra function object | 761 |
| funclets with **no** function object (Ghidra missed them) | 165 |
| distinct owning functions | 347 |

Beyond the 926, another **510** referenced addresses in the same range are not
`RUNTIME_FUNCTION.BeginAddress` values at all. They are the ICF side of the
compiler tail: 8–10 byte thunks of the form

```
MOV RCX,[RDX+0x40]   /   LEA RCX,[RDX+0x58]   ; then JMP <real funclet or handler>
```

which are referenced from a `FuncInfo4` but are not funclets with their own
member to destroy. They are not part of the ownership map and are not functions.

### 5. `funclet-ownership-2026-10-29.tsv`

926 rows, one per funclet. `member_offset` is the frame displacement of the
destroyed member (hex, as it appears in the body). `family` is the batch-5
taxonomy. `evidence` carries the `.pdata` record, the `FuncInfo4` address of the
owner, the decoded body operation, the guard word/bit, and the disposition
(`renamed …` / `kept …` / `ICF-shared owners=…; left unnamed`).

Family split of the 926: `string` 382, `freeField` 369, `rethrow` 104,
`linkFree` 40, `vdtor` 16, `vector` 6, `captain` 3, `other` 5, `nobody` 1.

## Renames — 448, every one plated

Rule (user decision, batch 6): `<Owner>_EhCleanup_<member>`, member as
`0x<frame offset>`. Applied only when the owner has a **trustworthy existing
name** and the funclet is still `FUN_*`.

| family | renamed |
|---|---|
| `string` | 296 |
| `freeField` | 102 |
| `linkFree` | 24 |
| `rethrow` | 19 |
| `vdtor` | 7 |
| **total** | **448** (112 distinct owners) |

Names are unique across the program; 124 needed a disambiguating token because
one owner destroys the same frame slot under several guards/sizes:
`…_sz<hex>` (sized `operator delete` — e.g. the 18 `CopyObject` funclets that
all `free(*(frame+0x30))` with 18 different sizes, a union/variant slot),
then `…_b<bit>` (same slot, different construction bit), then a numeric tail.

Largest owners by funclet count: `SomethingWithLevelSerias` 83,
`lootBoxCoins` 37, `Dialog_ExecuteChoiceActions` 35,
`TarkhanGUIDispatchOperator` 26, `salvageMiniGame?` 23,
`Body_BuildPartInfoPanel` 5.

Plate form (4 lines, applied at the funclet address):

> /EH cleanup funclet of `<Owner>` (`0x140000000+0x…`); destroys member `+0x…`
> of the parent frame. Family: `…`.
> Algorithm: called by `__CxxFrameHandler4` with `(exceptionCode,frame)` in
> `(ECX,RDX)`; `RBP:=RDX`; `<guard>`; `<destroy>`.
> Parameters: ECX = exception code, RDX = parent frame pointer; no return value.
> Returns: void. Owner and member recovered from the `.pdata`
> `RUNTIME_FUNCTION` / `FUNCINFO4` funclet table (sweep b6 agent 1).

Verified after the pass: 448/448 planned names present at their addresses,
448/448 plates contain the `FUNCINFO4` provenance sentence, 0 collisions with
pre-existing names.

## Left unnamed — 176 `FUN_*` that do have a proven owner

`0x140337000–0x14034b780` went from 624 `FUN_*` funclets (with owners) to 176.

| why | count |
|---|---|
| ICF-shared body, 2–34 owners each (naming it after one owner would be wrong) | 73 |
| owner is an ICF replica label (`rep_…_free`, `rep_…_New`, `rep_…_memmove`, …) — propagating it would invent an identity | 72 |
| owner name is marked uncertain (`!ClickFunc`) | 27 |
| owner has no function object in Ghidra | 2 |
| owner is itself `FUN_*` | 1 |
| owner named but no member displacement in the body (`0x1403423c0`) | 1 |

The 73 shared bodies are the interesting structural result: MSVC/`/OPT:ICF`
folds byte-identical cleanups, so one funclet address serves many classes.
`0x1403374c0` is referenced by **21** different owners, `0x140338a50` by 34.
Those addresses are the "ownerless clones" the blackboard predicted; they keep
their batch-5 family anchor and are catalogued with their full owner list in the
TSV.

Range state after the pass: **762 function objects** — 176 `FUN_*`, 82 `rep_*`
(untouched), 504 named.

## §6. Anomalies, and what was not done

* `0x14033cdc0` (owner `rep_140311db0_…::_CxxThrowException`) and `0x140342380`
  (owner `FUN_1403423c0`) are the only funclets whose member offset exceeds the
  owner's body size (`+0x78` vs 93 bytes; `+0xa0` vs 89 bytes). Both owners are
  themselves inside the compiler tail, so the `FuncInfo4` that references them
  is itself a folded/replica blob and the "owner" is at best a group of
  identical functions. They are left unnamed and flagged in the TSV.
* **165 funclets have no function object.** They are real code with a
  `RUNTIME_FUNCTION` entry, they have owners, and they are in the TSV, but
  renaming them needs `create_function` (per the blackboard protocol: post,
  wait a cycle, record). They were not created in this pass — batches 4/5 had
  explicitly ruled the range out for creation, and the parent should decide.
  Most are the smallest bodies (0x1d–0x29 bytes) that Ghidra never promoted
  because nothing calls them.
* The 510 thunk entries (§4) would need the same treatment; they are not
  cleanups and should not get `EhCleanup` names at all.
* `FuncInfo4` was only used as an *address oracle*. The full compressed decode
  (state/unwind/try-block maps) was not implemented: the member offset, guard
  bit and destroyed size all come straight out of the funclet body, which is
  cheaper and independently checkable.
* Nothing in this range is game logic. Every one of the 926 funclets is
  compiler-generated `/EH` cleanup for a function defined elsewhere in `.text`.
