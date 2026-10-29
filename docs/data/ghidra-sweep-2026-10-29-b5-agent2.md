# Unnamed-function sweep, 2026-10-29 — batch 5, agent 2

Range: `0x140337000–0x14033FFFF` (upper end `0x14033ffb0`; next function is
agent 3's `0x140340150`).

Program `Highfleet.exe.unpacked.exe` v1.163. **288 function objects**: 241
`FUN_*` and 47 `rep_*`. Result: **8 renamed (all plated), 233 deliberately
left**, all compiler output. No functions created (`create_function` not
applicable — no vtable slots here, see below).

This range is the continuation of the `/EH` cleanup-funclet run that starts
around `0x140336700`. It is **not** game logic and **not** Box2D: no body calls a
`b2*` function and no `b2` vtable slot points into the range. Batch 4 agent 2
reached the same conclusion for the adjacent `0x140340000+` range; this note
carries that taxonomy forward and adds the two families that dominate *this*
half.

## How the range was surveyed

1. Enumerated all function objects in range with a `run_script_inline` pass
   (address, name, body size) → 288 objects, 241 unnamed.
2. Dumped the full instruction list of every unnamed function in two halves and
   classified each body **mechanically** by its call shape:
   `CALL free(0x1403340d0)` → `freeField`; `CALL String_Tidy(0x140006d70)` →
   `string`; `CALL freeLinkMemory?(0x140194d20)` → `linkFree`;
   `CALL _CxxThrowException(0x14033658e)` → `rethrow`; indirect call →
   `vdtor`; anything else → inspected by hand (`captain`).
3. Extracted for each body the immediates that identify its owner field:
   the `MOV EDX,size` of a delete, the guard dword `[RBP+g]` and its `AND
   EAX,mask`, and the `LEA RCX,[RBP+off]` member address. Those four numbers
   are the entire payload of a funclet, so the classification needs no
   decompiler and no guessing.
4. Grouped by family and by (guard, bit) / (size, offset). Cross-checked the
   non-CRT callees (`0x14005e560`, `0x14005e6b0`, `0x1400bee60`, the
   `deallocate`/`DeleteArray*` set) by name before using them in a plate.

Every body is `(int exceptionCode, void *frame)` with the frame arriving in
`RDX` (`MOV RBP,RDX`), so `RBP+off` below always means "member `off` of the
parent object". Each function has exactly **one DATA xref, from the unwind /
funclet table block `0x14808xxxx–0x14808bxxx`** (e.g. `0x1403372d0 <-
148088b54`, `0x14033f9b0 <- 148089bc8`); there are no call xrefs at all. As
batch 4 noted, recovering a funclet's owner therefore needs that table parsed,
not xref walking.

## Cluster map

| family | count | span | destroying callee | identifying data |
|---|---|---|---|---|
| `freeField` — sized `operator delete` of one member | 97 | `0x1403372d0–0x14033feb0` | `free` (0x1403340d0) | `(size, member offset)` pair |
| `string` — guard bit + `String_Tidy(member)` | 101 | `0x1403375d0–0x14033ff80` | `String_Tidy` (0x140006d70) | `(guard offset, bit, string offset)` |
| `linkFree` — guard bit + `freeLinkMemory?(member)` | 22 | `0x1403378c0–0x14033ffb0` | `freeLinkMemory?` (0x140194d20) | `(guard offset, bit, Link offset)` |
| `rethrow` — partial array/container destroy + rethrow | 17 | `0x140337f20–0x14033e650` | per-body `deallocate`/`DeleteArray*`/`Array_*` | callee + frame offsets |
| `vdtor` — guard bit + virtual destructor | 1 | `0x140339100` | `[0x1403511e8]` (indirect) | guard `+0x40` bit 1, subobject `+0x108` |
| `captain` — guard bit + `Captain` subobject dtor | 3 | `0x14033f9b0–0x14033fa30` | `Captain_DestructorSubobject8` / `Captain_Destructor` | guard `+0x80`, 3 bits |

Sizes are tiny throughout (bodies `0x1d–0x42`, i.e. 29–66 bytes; only
`0x14033c580` is 64 and `0x140338110` 66). Nothing in the range exceeds 66
bytes, so the whole range is uniform compiler tail.

## Named (8)

| addr | name | why this one |
|---|---|---|
| `0x1403372d0` | `EhCleanup_DeleteFieldSized` | anchor of the 97-member `freeField` family (largest family in this half) |
| `0x1403375d0` | `EhCleanup_MemberStringBits` | anchor of the 101-member `String_Tidy` family |
| `0x1403378c0` | `EhCleanup_MemberLinkBits` | anchor of the 22-member `Link` family |
| `0x140337f20` | `EhCleanup_PartialArrayRethrow` | anchor of the 17-member partial-array-destroy-then-rethrow family |
| `0x140339100` | `EhCleanup_VirtualMemberDtor` | unique: the only indirect call in the range (through `0x1403511e8`) |
| `0x14033b9c0` | `EhCleanup_StringLadder74` | anchor of the densest run: 28 string members with bits `1..0x80000000` in one dword |
| `0x14033c580` | `EhCleanup_MemmoveRollback` | unique: memmove rollback + saved-size write-back + rethrow |
| `0x14033f9b0` | `EhCleanup_MemberCaptain` | the only funclets here whose destroying callee is a **game** class dtor, not CRT code |

Plates carry the family definition, the parameter/return convention and the
fingerprint of the remaining copies, so any clone can be matched from the plate
alone. All 8 names pass the collision rule (none is a superset of an existing
`EhCleanup_*` token set; batch 4's `EhCleanup_MemberString88`,
`EhCleanup_FreeField70`, `EhCleanup_ArrayThenRethrow`, `EhCleanup_InsertRollback`
remain distinct neighbours).

### `freeField` — 97, `0x1403372d0–0x14033feb0`

`MOV EDX,size / MOV RCX,[frame+off] / CALL free`. The callee is the imported
`free` thunk (5-byte `JMP [IAT]`), i.e. this is MSVC's **sized**
`operator delete(ptr, size)` folded onto `free`; the size is metadata
describing the class being deleted, not an argument `free` uses. So these are
"delete this one heap member of the object under construction" funclets.

Size histogram: `0xe70`×26, `0xa40`×7, `0x128`×5, `0x1a8`×5, `0x38`/`0x40`/
`0x50`/`0x58`/`0x270`/`0xe98`/`0xed0` ×3, `0x18`/`0x28`/`0x30`/`0x60`/`0x68`/
`0x70`/`0x118`/`0x1b8`/`0x618`/`0xea8`/`0xf18` ×2, and singletons
`0x78 0xc0 0x1b0 0x268 0x308 0x340 0x370 0xa58 0xef0 0x1a50`.

Remaining 96 (anchor excluded); format `addr:sz<size>@+<offset>`:

```
0337400:szc0@+50 0337420:sz1a8@+20 0337440:sza40@+60 0337460:sz118@+60
03374a0:sz1a8@+30 03374c0:sze70@+70 03375a0:sze70@+80 03376c0:sze70@+78
03376e0:sz1a8@+68 03377a0:szed0@+38 03377e0:szed0@+48 0337810:sza40@+90
03378f0:sze70@+90 0337920:sz1b0@+30 0337950:sza40@+138 03379e0:sza40@+1d0
0337a10:sza40@+c8 0337ad0:sz1a8@+48 0337af0:sz1a8@+50 0337b50:sze70@+98
0337e20:sz58@+30 0337e60:sz58@+20 0338a10:sza40@+e0 0338a50:sze70@+60
0338c60:sz1a50@+20 0338cb0:sz40@+38 0338ce0:sz40@+58 0338d00:sz58@+58
0338d20:sz38@+58 0339180:sz68@+30 0339240:sz28@+30 0339260:sz38@+40
0339280:sz28@+40 03392b0:sz18@+30 03392d0:sz18@+40 03393c0:sz38@+30
0339530:sz40@+30 0339680:sz30@+30 03396e0:sz78@+30 03397d0:sz60@+40
0339920:sz60@+38 0339950:sz30@+38 0339990:sz50@+30 03399b0:sz50@+38
033a070:sze70@+68 033a810:sze70@+218 033abd0:sze70@+2d0 033ad20:sze70@+318
033ad50:sze70@+320 033ad80:sze70@+328 033adc0:sze70@+330 033ae10:sze70@+340
033aea0:sze70@+378 033aef0:sze70@+388 033af20:sze70@+390 033aff0:sze70@+3c0
033b020:sze70@+3c8 033b070:sze70@+458 033b140:sze70@+410 033c600:sz118@+a8
033c6c0:sze70@+d8 033c790:szf18@+60 033c7b0:szea8@+60 033c7d0:sze98@+70
033c7f0:szf18@+70 033c810:szef0@+68 033c830:szea8@+68 033c850:sze98@+198
033ca10:sz128@+38 033cad0:sze70@+a8 033cb80:sze70@+1e8 033d500:sz70@+88
033d620:sz1b8@+30 033d640:sz1b8@+38 033d8b0:sz128@+20 033d8e0:sz268@+20
033d930:sz370@+e0 033db70:sze70@+c0 033dbd0:sz70@+a8 033dc50:sz308@+40
033de80:sz340@+40 033df90:sz50@+68 033e000:sz128@+98 033e1b0:sza58@+40
033e4b0:sz270@+40 033e4e0:sz270@+88 033e510:sz270@+e0 033ec50:sz68@+58
033f680:sz618@+70 033f6a0:sz128@+70 033f840:sze70@+11f0 033fbf0:sze98@+11f0
033fca0:sza40@+11f0 033fe30:sz128@+11f0 033fe70:sz618@+11f0 033feb0:szed0@+78
```

Two dense runs sit inside this family: the `0xe70` members at
`0x14033abd0–0x14033b140` (members `+0x2d0..+0x458` of one very large object,
all same size) and the `+0x11f0` cluster at `0x14033f840–0x14033fe70`
(five different sizes at the same frame offset — five different member types
puncturing one slot, i.e. a union/variant). Both are copies, so no extra names.

### `string` — 101, `0x1403375d0–0x14033ff80`

`if (*(u32*)(frame+g) & bit) { *(u32*)(frame+g) &= ~bit; String_Tidy(frame+str); }`

15 guard groups (bits are the extracted bit values, not the masks):

| guard | n | span | bits | member offsets |
|---|---|---|---|---|
| `+0x20` | 18 | `0x140337e80–0x14033cc30` | 1,2,4,8,0x10,0x20,0x40,0x80,0x100 | `+0x28..+0x98` |
| `+0x30` | 4 | `0x140338c30–0x14033e150` | 1,2 | `+0x68..+0xe8` |
| `+0x38` | 2 | `0x140338df0–0x140338e20` | 1,2 | `+0x48,+0x108` |
| `+0x60` | 2 | `0x14033ddf0–0x14033de20` | 1,2 | `+0x78,+0xd8` |
| `+0x64` | 1 | `0x140338ab0` | 1 | `+0x148` |
| `+0x68` | 7 | `0x1403375d0–0x14033c480` | 1,2,4,8,0x10,0x20 | `+0xb8..+0x178` |
| `+0x6c` | 1 | `0x140338a70` | 1 | `+0x80` |
| `+0x70` | 2 | `0x14033e060–0x14033e090` | 1,2 | `+0x88` |
| `+0x74` | **28** | `0x14033b9c0–0x14033bfd0` | **1..0x80000000** (all 28) | `+0x2700..+0x2f00` |
| `+0x80` | **21** | `0x140338b40–0x14033f960` | 1..0x200000 minus 0x20000/0x40000 | `+0x158..+0x1e30` |
| `+0x88` | 1 | `0x14033ff80` | 0x10 | `+0x660` |
| `+0x90` | 1 | `0x14033dfd0` | 1 | `+0xb8` |
| `+0x98` | 6 | `0x14033a290–0x14033b250` | 1,2,4,0x10,0x20,0x40,0x100 | `+0x16b0..+0x27f0` |
| `+0x9c` | 1 | `0x14033dda0` | 1 | `+0x158` |
| `+0xc8` | 6 | `0x14033c010–0x14033c120` | 1,2,4,8,0x10,0x20 | `+0x2ac0..+0x2ca0` |

The `+0x74` group is the interesting one and is named
(`EhCleanup_StringLadder74`, `0x14033b9c0`): **28 consecutive construction bits
1..0x80000000** in a single dword, with 28 distinct string members at
`+0x2700..+0x2f00` — one class with 28 `std::string` members and a 32-bit
"constructed" mask, i.e. a big serialised record type. The `+0x80` group is the
same pattern one class over (21 bits, members `+0x158..+0x1e30`, plus a
`0x20000`/`0x40000` member that is not a string — see the `captain` family,
where those same two bits destroy `Captain` objects).

A small structural variant worth knowing: four bodies load the string pointer
with `MOV RCX,[frame+off]` instead of `LEA RCX,[frame+off]` (`0x140338c30`,
`0x14033db30`, `0x14033e120`, `0x14033e150`), i.e. the member is a *pointer to*
a string rather than an embedded string. Body shape is otherwise identical.

### `linkFree` — 22, `0x1403378c0–0x14033ffb0`

Same guard-bit shape, but the member is an intrusive `Link`/list node destroyed
by `freeLinkMemory?` (85-byte body, batch-4 name). This is the single-node
counterpart of batch 4's `EhCleanup_LinkVector24x4` family.

| guard | n | span | bits | member offsets |
|---|---|---|---|---|
| `+0x24` | 2 | `0x14033e0c0–0x14033e0f0` | 1,4 | `+0x30,+0x68` |
| `+0x68` | 1 | `0x14033de50` | 1 | `+0xd0` |
| `+0x74` | 2 | `0x14033b3e0–0x14033b5a0` | 1,4 | `+0x498,+0x4c8` |
| `+0x78` | 3 | `0x140337ba0–0x140337c80` | 1,4,0x10 | `+0x928,+0x958,+0x988` |
| `+0x80` | 1 | `0x14033f6f0` | 0x1000 | `+0x7b8` |
| `+0x88` | 3 | `0x14033fee0–0x14033ffb0` | 1,4,0x40 | `+0x3d0,+0x400,+0x430` |
| `+0x90` | 1 | `0x1403378c0` | 1 | `+0xa0` |
| `+0xb8` | 1 | `0x140337ef0` | 1 | `+0x38` |
| `+0x128` | 1 | `0x14033dab0` | 1 | `+0x30` |
| `+0x158` | 4 | `0x14033dea0–0x14033df30` | 1,2,4,8 | `+0x68,+0x68,+0x80,+0x80` |
| `+0x170` | 1 | `0x14033dd30` | 1 | `+0x70` |
| `+0x1d8` | 2 | `0x14033c700–0x14033c730` | 1,4 | `+0xe8,+0x118` |

`+0x158` contains two pairs (bits 1,2 on `+0x68`; bits 4,8 on `+0x80`) — a
two-link member destroyed twice under different bits, i.e. `Link` and a second
list node sharing an address pattern.

### `rethrow` — 17, `0x140337f20–0x14033e650`

Shape: fetch container base (usually through the 4-byte identity helper
`FUN_1400199d0`, `MOV RAX,RCX / RET`), destroy/deallocate the partially built
buffer, then `_CxxThrowException(NULL,NULL)`. Second column is the destroying
callee; third column the frame slots read, in order.

| addr | size | destroying callee(s) | frame offsets |
|---|---|---|---|
| `0x140337f20` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x40,+0x48,+0x58` |
| `0x140338110` | 0x42 | `Array_DestroyRange48`, `deallocate` | `+0x30,+0x28,+0x80,+0x98,+0x20` |
| `0x1403389d0` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x40,+0x48,+0x50` |
| `0x1403392f0` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x140339370` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x140339430` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x140339480` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x140339700` | 0x2f | `DeleteArray56`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x1403399d0` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x14033c4d0` | 0x35 | `deallocate`, `FUN_1400199d0` | `+0x80,+0x88,+0x38` |
| `0x14033c580` | 0x40 | `memmove` wrapper | `+0x80,+0x38,+0x98,+0x28` |
| `0x14033cc80` | 0x27 | `DeleteArray32` | `+0x68,+0x78,+0x60` |
| `0x14033ccb0` | 0x27 | `deallocate` | `+0x58,+0x68,+0x50` |
| `0x14033cd50` | 0x2a | `deallocate` | `+0x78,+0x88,+0x70` |
| `0x14033d5b0` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x40,+0x48,+0x50` |
| `0x14033e310` | 0x2f | `deallocate`, `FUN_1400199d0` | `+0x60,+0x68,+0x78` |
| `0x14033e650` | 0x3e | `Array_DestroyRange88`, `Array_FreeStride88` | `+0x30,+0xb8,+0xa0,+0x20,+0x38,+0x40` |

The seven 0x2f-byte bodies at `+0x60/+0x68/+0x78` are byte-identical apart from
which `deallocate`-family thunk they call — i.e. six different element types of
one `vector`-like container, each with its own typed `operator delete[]`.
`0x14033c580` is the odd one (one memmove + saved-count write-back, named
`EhCleanup_MemmoveRollback`); `0x14033e650` destroys a range of 0x58-byte
elements in two steps (destroy range, then free stride).

### `vdtor` — 1, `0x140339100`

`if (*(u32*)(frame+0x40) & 1) { clear; [0x1403511e8](frame+0x108); }`.
`0x1403511e8` holds `0x003bb570`; the slot is read by 34 funclets in
`0x140341xxx–0x140346xxx` as well, so this is a shared polymorphic-base virtual
destructor slot, not a one-off. Named `EhCleanup_VirtualMemberDtor`.

### `captain` — 3, `0x14033f9b0–0x14033fa30`

| addr | guard bit | member | callee |
|---|---|---|---|
| `0x14033f9b0` | `0x400000` | `+0x28a0` | `Captain_DestructorSubobject8` (0x14005e560) |
| `0x14033f9f0` | `0x800000` | `+0x27f0` | `Captain_Destructor` (0x14005e6b0) |
| `0x14033fa30` | `0x1000000` | `+0x2840` | `Captain_DestructorSubobject8` (0x14005e560) |

`0x14005e560` is `ADD RCX,8; *RCX = &vftable; JMP 0x14018f7d0` — it destroys a
`Captain` at `member+8`, so `0x14033f9b0`'s member has an 8-byte header before
the `Captain`. These are the only funclets in the range that call a game class
destructor instead of CRT deallocation. Named at `0x14033f9b0`
(`EhCleanup_MemberCaptain`).

## Why the other 233 are left unnamed

* They are byte-identical to a named sibling except for an embedded constant
  (size, frame offset, guard bit, string offset, destroying callee). Naming each
  would add 233 names carrying no information the family plate does not already
  state, and the constant is visible in the body at the address.
* Ownership is still unknown for all of them: the only xref is the unwind table
  at `0x14808xxxx`, so a name like `~SomeClass` would be a guess. Batch 4 agent
  2 flagged the same gap; **it is still open** and applies to this range too
  (see below).
* `create_function` is not appropriate: no vtable slot, no code pointer and no
  call target points into the range — every entry is referenced only as a
  funclet-table DATA entry.

## `rep_*` in range (47, untouched)

All keep the `rep_` prefix because each already carries the name of its target:
`rep_wrap_0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` (20×),
`rep_..._VCRUNTIME140.DLL::_CxxThrowException` (15×),
`rep_..._deallocate` (6×), `rep_..._deallocateString?` (5×),
`rep_1403141b0_\`eh_vector_destructor_iterator'` (1×). They are identical to
their named targets, so renaming would duplicate names.

## Open question (unchanged from batch 4, now covering this range too)

Funclet **ownership** — which class each of the 241 funclets cleans up — cannot
be recovered by xrefs; it needs the unwind/funclet table at `0x14808a000`
parsed (each row gives the owning function's `UnwindMapEntry`/`TryBlockMapEntry`
and hence the parent address and its try-level). That table would also collapse
the `freeField`/`string` offsets into concrete member layouts (size at `off`
means the class at `off-size` in the parent). Worth one dedicated pass in a
later batch: with the parent addresses, the ~230 clones become 20-30 class maps
rather than 230 anonymous functions.

## Verification

* 288 objects in range before the pass; 241 `FUN_*`; 8 renamed + plated; 233
  `FUN_*` remain (re-counted after the pass with the same enumeration script).
* Every name+plate applied in separate transactions; all returned `status:
  success`.
* No `save_program`, no tags, no README/STATUS edit, no commit performed.
* Nothing outside `0x140337000–0x14033FFFF` was modified; `create_function` was
  not used.
