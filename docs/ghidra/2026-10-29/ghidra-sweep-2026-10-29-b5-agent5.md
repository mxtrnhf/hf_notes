# Ghidra sweep, batch 5 agent 5 — `0x140000000–0x14006FFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range started with 219 unnamed functions counted without thunks (12 `FUN_*` +
207 `rep_*`). **15 renamed, all plated** (4 `FUN_*`, 11 `rep_*`). No
`save_program`, no tags, no README/STATUS edits, no commits, no
`create_function` calls.

| | before | after |
|---|---|---|
| `FUN_*` in range | 12 | 8 |
| `rep_*` in range | 207 | 196 |
| total functions in range | 699 | 699 |

The static-initialiser half of the range was finished by batch 4 agent 3
(`ghidra-sweep-2026-10-29-b4-agent3.md`); nothing there was re-touched. The
work here is the remaining exception/EH plumbing plus a set of **provably
mis-named `rep_*` destructors** found through MSVC RTTI.

## Renames — exception / EH plumbing (4 `FUN_*` + 1 `rep_*`)

| addr | new name | evidence |
|---|---|---|
| 0x140019990 | `EhCleanup_InvalidParameterWrapper` | 20-byte wrapper: tail-calls `_invalid_parameter_noinfo_noreturn` (0x140011630) with `(param_2, param_3, param_1)`. Only callers are `/EH` funclet bodies at 0x140336d3d and 0x1403380e0. |
| 0x1400199b0 | `EhCleanup_FreeWrapper` | 20-byte wrapper forwarding to the `free` replica at 0x140055d80; called only from funclets / `_CxxThrowException` replicas (7 xrefs). |
| 0x1400199d0 | `EhCleanup_IdentityWrapper` | 4-byte `return param_1`; used as the cleanup/deleter callback of ~40 funclets (every call site is inside an exception-unwind body). |
| 0x140055f20 | `RefCountObj2_GetDeleter` | `return 0` stub, slot 3 of vtable 0x140354a38 whose RTTI is `.?AV?$_Ref_count_obj2@V?$map@I_N...@@std@@`; matches the `_Get_deleter` override. |
| 0x140055f30 | `Vector_ThrowSubscriptOutOfRange` | 17 bytes: `std::_Xout_of_range("invalid vector subscript")` then `int3`; 0x140354a10 (the address it loads) is the literal string, not a vtable. |

## Renames — destructors proved by RTTI / vtable slot (10)

Every one of these was named `rep_<addr>_..._free`,
`rep_..._invalid_parameter_noinfo_noreturn` or `rep_..._sqrtf`, i.e. the
embedded target was provably unrelated to the body (see the `rep_*` section).
The class comes from `vtable[-1] -> CompleteObjectLocator -> TypeDescriptor`,
the role from the body and the slot index.

| addr | new name | class / slot / shape |
|---|---|---|
| 0x1400054e0 | `AADefense_ScalarDeletingDestructor` | RTTI `.?AVAADefence@@`, vtable 0x140352320 **slot 0**; stores vptr, releases +0x138, frees four `Link` sentinels, deletes at `flag&1`. |
| 0x140005570 | `std_exception_ScalarDeletingDestructor` | RTTI `.?AVexception@std@@`, vtable 0x140352288 **slot 0**; `__std_exception_destroy(this+8)` then `flag&1`. |
| 0x140007040 | `AircraftLogic_Destructor` | stores `AircraftLogicVFTABLE`; tears down three RbTrees (+0x120/+0x130/+0x140), four `Link` sentinels, heap vector at +0xd8; ends with `ISerializable_Destructor`, **no free** → complete-object dtor. |
| 0x140007270 | `AircraftLogic_ScalarDeletingDestructor` | vtable 0x1403525a8 **slot 0**; calls 0x140007040, then `flag&1`. |
| 0x1400072b0 | `FProperty_ScalarDeletingDestructor` | RTTI `.?AVfProperty@@`, vtable 0x140352540 **slot 0**; `Property_Destructor` + `flag&1`. |
| 0x1400174d0 | `Body_Destructor` | stores `BodyVFTABLE`; destroys b2 body/fixture, notifies children, frees every member container and the +0x110 RbTree; called as base dtor by `Creature_Destructor` and the Body deleting dtor. |
| 0x140055e70 | `RefCountObj2_MapUIntBool_ScalarDeletingDestructor` | vtable 0x140354a38 **slot 2** (RTTI `_Ref_count_obj2<map<unsigned int,bool>>`); vptr + `flag&1`. |
| 0x140055ec0 | `RefCountObj2_MapUIntBool_Destructor` | same vtable **slot 0**; destroys the owned `std::map` at +0x10 (RbTree walk + free), does not free `this`. |
| 0x14005e240 | `HistoryDesign_Constructor` | RTTI `.?AUHistoryDesign@@`; calls `ISerializable::ISerializable`, stores `HistoryDesignVFTABLE`, zeroes name/property fields, calls the CopyString helper 0x14006f6a0. |
| 0x1400600d0 | `HistoryDesign_ScalarDeletingDestructor` | vtable 0x140354bb0 **slot 0**; releases +0x48, frees the name buffer, `ISerializable_Destructor`, `flag&1`. |

## `rep_*`: the embedded names are not replicas — systematic finding

Batch 4's note described the remaining 207 `rep_*` as "ICF-merged replicas"
and advised leaving them. That is **not** what these functions are. Evidence:

1. **No byte-identical twin exists.** I SHA-1 hashed the raw bytes of every
   function in the program and compared all 207 `rep_*` bodies against every
   other function: **0 of 207** have an identical body anywhere in the image.
   ICF folding cannot leave 207 distinct-but-identical copies, so the
   "replica" premise is false.
2. **The embedded address is usually not a function entry and often not even
   in another function.** Of the 199 names that parse as `rep_<hex>_<name>`:
   174 embedded addresses fall *inside* an unrelated named function (usually
   mid-instruction), 14 fall inside the rep function's **own** body, only 8
   are real function entries, 3 are undefined bytes. Example:
   `rep_140057220_..._sqrtf` at 0x140059230 (2090 bytes) — 0x140057220 is
   inside 0x140056a10, which is itself a mis-named `rep_..._sqrtf`.
3. **Sizes are incompatible with the imports they claim.** `sqrtf`/`atan2f`/
   `free`/`memmove` replicas of 1–5 KB: 0x140056a10 = 4841 B "sqrtf",
   0x14002bb50 = 4716 B "MakeGlobal?", 0x14005f430 = 2228 B
   "Property::Property", 0x1400625a0 = 2150 B "free", 0x140059230 = 2090 B
   "sqrtf". Only 14 of the 207 bodies are <= 64 bytes; the genuinely tiny ones
   are the only plausible CRT replicas.

Conclusion: the `rep_*` prefix on this program is an unreliable
signature-database artefact, **not** evidence of identity. It should not be
trusted for xref reasoning, and "it is a replica, leave it" is unsafe. The 11
renames above are the subset I could disprove and re-identify in this pass;
the rest still need body-level identification.

Reps that are already known to be mis-named but whose **body lies outside my
range** (reported, not renamed):

| address | current bogus name | what it really is |
|---|---|---|
| 0x14025d060 | `rep_14025d060_..._free` (agent 9 range) | base-class destructor called at the end of `AADefense_ScalarDeletingDestructor` (0x1400054e0) and `Body_Destructor` (0x1400174d0); it is `free(this)`-shaped in the decompiler but both callers pass a live object. |
| 0x1402b1a80 | `rep_1402b1a80_MakeGlobal_()` (agent 9 range) | callee of the per-element loop in `FUN_140027f90` (only call site). |
| 0x1400eaef0 | `rep_1400eaef0_..._free` (agent 6 range) | body at 0x140061dc0, 118 bytes. |
| 0x140153be0 | `rep_140153be0_compData` (agent 7 range) | body at 0x14002dda0. |

Notable in-range reps whose embedded target is also in-range but wrong, left
for a dedicated pass (each needs its body read): `0x140059230` (2090 B
"sqrtf"), `0x14005b1b0` (1328 B "sqrtf"), `0x1400625a0` (2150 B "free"),
`0x14005f430` (2228 B "Property::Property"), `0x1400664c0` (2130 B
"ShipCards?"), `0x14002bb50` (4716 B "MakeGlobal?").

## Left in range (no action)

`FUN_*` (8):

| addr | size | why left |
|---|---|---|
| 0x14000ad80 | 0xb | `return *(int*)(this+0x190) != 0`, single caller `Projectile_DetonateOnImpulse`; field role unknown. |
| 0x140017d10 | 0x24 | one virtual forwarder through a locator-resolved slot; single data xref at 0x14807905c, owner table unknown. |
| 0x140019310 | 0x6f | vtable **slot 36** of Creature/Body/MapShipBody/Frame (adjacent to `Creature_EnableBody` slot 38, `Creature_DisableBody` slot 40): sets byte +0x9e0 = 1, calls slots +0x290/+0x280, stamps `_Xtime_get_ticks`. No callers; semantics not provable. |
| 0x140019380 | 0x30 | paired **slot 37**: clears +0x9e0, calls slot +0x298, `Frame_ResetCounter`. No callers. |
| 0x1400211a0 | 0x23b6 | > 0x2000, not decompiled per rule 6. |
| 0x140027f90 | 0x78 | loops the vector at +0x350 and calls 0x1402b1a80 when `elem+0x58 != 0`; callers `?BuyPartShop` / `memcmp_editor`; element role unknown. |
| 0x1400458c0 | 0xd0e | `Frame_ClassifyPartMix`-dispatched (cases 4/5/6) collector that walks parts, filters `Body_IsMountedOrPaired == 0` and flag bits 0x80/0x100, offsets positions with `setXposYpos` and inserts float-pair-keyed `Link`s into `param_2`. Candidate `Body_CollectLoosePartsForMix`, but the caller/type meaning is not established — left. |
| 0x140049cd0 | 0x23 | `param_2 <= *(int*)(this+0x2e8) && *(float*)(this+0x248) != 0`; callers `creatureLogic`, `mainDialogWithChoices`, `!ClickFunc`; the two field roles are unknown (suspect "requirement/afford" check, not provable). |

`rep_*` (196): see the section above — mis-named, but each needs a body-level
read. All 207 in-range `rep_*` embedded targets point at CRT/DLL import names
or at unrelated code; none of those names is a replica of the body.

## Possible `create_function` (not executed — brief said not expected here)

`0x140018b60` is **Body's deleting destructor** (`??_EBody`): real
instructions, no function object, and it is **slot 0 of vtable 0x140352a30**
(RTTI `.?AVBody@@`). Body:
`CALL 0x1400174d0 (Body_Destructor); TEST BL,1; JZ return; MOV EDX,0xa40;
MOV RCX,RDI; CALL <operator delete with size>`. sizeof(Body) = 0xa40 matches
`Body_Constructor` (0x140015ed0). If the batch owner wants it, create
`Body_ScalarDeletingDestructor` at 0x140018b60 and plate it; nothing else in
the range lacks a function object at a vtable slot.

## Counts

* renamed: **15** (5 exception/EH plumbing, 10 RTTI-proved destructors/ctor)
* `FUN_*` left in range: **8**
* `rep_*` left in range: **196** (embedded names unreliable, see above)
* functions created: 1 identified but **not** created (0x140018b60)
