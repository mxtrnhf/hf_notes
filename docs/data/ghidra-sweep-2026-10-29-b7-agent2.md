# Ghidra sweep batch 7, agent 2 — `rep_*` re-match 0x140000000–0x1400FFFFF

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Scope: every `rep_*` function in `0x140000000–0x1400FFFFF`, excluding every
address listed in `docs/data/funclet-ownership-2026-10-29.tsv` (agent 1's
tail). **492 functions audited** (491 bodies + the 5-byte import thunk at
0x1400e4cc0).

**27 renamed + plated. 465 stale labels left; 0 unreadable.**
No `save_program`, no tags, no README/STATUS edits, no commits, no
`create_function`.

| | before | after |
|---|---|---|
| `rep_*` in scope | 492 | 465 |
| renamed | — | 27 |

## Method

1. Enumerated every `rep_*` in range with a script (address, body size,
   SHA-1 of exact body bytes, embedded address parsed from the label, callee
   set, referenced string literals) into `/tmp/opencode/hf_ghidra_sweep/b7a2_list.tsv`.
2. Re-ran the byte-identical-twin test against all non-`rep_*` functions
   **after** batch 6's 448 funclet renames: **0 of 492** bodies is
   byte-identical to any named function. The "replica" premise is still false;
   every renamed row below was proved from RTTI/vtable class data or from the
   body itself, not from the embedded label.
3. Scanned each body for stores of known vtable bases. 32 in-range
   `rep_*` functions install a vtable; for each, resolved the vtable's
   CompleteObjectLocator → TypeDescriptor (`vtables.tsv` plus a fresh COL
   reader) and classified the role from the body (ctor vs base dtor vs
   scalar-deleting dtor).
4. Decompiled the 32 vtable-installers and ~40 further candidates (game
   logic / HGE layer reached through distinctive callees or literals), and
   proved role before naming.

## Renames (27) — all with doc plates

### RTTI/vtable-proved constructors and destructors (22)

| addr | new name | proof |
|---|---|---|
| 0x14005df60 | `HistoryDesign_CopyConstructor` | installs `HistoryDesignVFTABLE`; copies every field + embedded string from src |
| 0x14005f430 | `fProperty_CopyConstructor` | `copyOverBody()` then copies all fProperty fields, incl. `m_damageCounter`; vtable 0x140352540 COL `.?AVfProperty@@` |
| 0x140081830 | `ComputeShader_ScalarDeletingDestructor` | installs 0x140356668 (`.?AVComputeShader@@`), releases +0x18 via vtable+0x10, `free` on flag |
| 0x140081a40 | `CSGlitch_Constructor` | chains `ComputeShader_Constructor`, installs 0x140356698 (`.?AVCSGlitch@@`) |
| 0x140082610 | `FileBuf_Destructor` | installs 0x140356790 (`.?AV?$basic_filebuf@D...@std@@`), chains `~basic_streambuf` |
| 0x140086fc0 | `EffectMatrixConstantBuffer_Constructor` | alloc 0x68 + `ShaderData_Constructor` + 0x140356ad8 (`.?AV?$ConstantBuffer@UCBMatrix@Effect@@@@`), uploads 0x40 B |
| 0x14008c770 | `ShaderDefault_Constructor` | chains `EffectConstructor`, installs 0x1403570c8 (`.?AVShaderDefault@@`) |
| 0x1400a0970 | `Values_Item_ConstructorWithCallback` | installs 0x140359220 (`.?AUItem@Values@@`), `CopyEscadraName`, binds callback at +0x38 |
| 0x1400e3b80 | `Explosion_CopyConstructor` | Explosion ctor body (Mark::Mark + 0x14035ecb8 `.?AVExplosion@@`) then copies +0x248..+0x261 from src |
| 0x1400e3ce0 | `Intel_CopyConstructor` | `ISerializable::ISerializable` + `IntelVFTABLE` + embedded Link vtables, copies all fields from src |
| 0x1400e3e30 | `Intel_Constructor` | same but single-arg, clears remaining fields |
| 0x1400e3f60 | `LastPlayerPosData_CopyConstructor` | 0x14035dfa0 (`.?AULastPlayerPosData@@`), `ReassignLinkNode` + copy from src |
| 0x1400e4010 | `LastPlayerPosData_ConstructorFromLink` | sets `SetLink(param_2)` into +0x48 |
| 0x1400e40d0 | `LastPlayerPosData_Constructor` | no-arg variant, name/code 0x100003 |
| 0x1400e4150 | `Launched_Constructor` | `Mark::Mark` + `LaunchedVFTABLE` + 3 Link vtables |
| 0x1400e41f0 | `Location_CopyConstructor` | `Mark::Mark` + `LocationVFTABLE` (`.?AVLocation@@`), copies all fields + item list |
| 0x1400e4580 | `EscadraMapShip_Constructor` | installs 0x14035e498 COL `.?AVMapShip@Escadra@@` + Link vtables, copies ship name |
| 0x1400e4cd0 | `Escadra_Destructor` | installs `EscadraVFTABLE`, destroys member lists/Links (base dtor, not deleting) |
| 0x1400e5220 | `IntelPolygon_Destructor` | installs 0x14035dfe8 (`.?AVIntel_polygon@@`), frees +0x18 vertex array |
| 0x1400e5340 | `Mark_Destructor` | installs `MarkVFTABLE`, destroys owned list/strings, chains `Node_Destructor` |
| 0x140073180 | `HistoryDesign_InitBaseFields` | sets literal `"HistoryDesign"` + code 0x100000000003; called by both HistoryDesign ctors |
| 0x1400f7ab0 | `Escadra_InitBaseFields` | sets literal `"Escadra"` + code 0x147, clears lists/Links |
| 0x1400f8290 | `MapCraft_InitBaseFields` | sets literal `"MapCraft"` + code 0x800000001047 |
| 0x1400f8300 | `EscadraMapShip_InitBaseFields` | sets `"Escadra::MapShip"` + code 0x10000000003 |

### Body/string-proved helpers (5)

| addr | new name | evidence |
|---|---|---|
| 0x140086970 | `FileBuf_Sync` | `basic_filebuf::sync`: virtual flush (vtable+0x18) then `fflush(FILE+0x80)` |
| 0x14004af60 | `PlayMorseSound` | `playSFXSound_(9,"morse_01",...)` gated by cooldown +0x990 |
| 0x14004e6f0 | `PlayWeldingSound` | picks `"welding_01"`/`"cancel_01"` from hull ratio, calls `playSFXSound_` |

## Stale rows with a new partial identity (column 4 of the TSV)

* **14 × 52-byte** `ShaderData_ResetVTable(); if(flag) free(this)` — still the
  `ConstantBuffer<T>` slot-1 scalar-deleting destructor (unchanged from b6).
* 0x14004a2f0 — polygon/polygon overlap test: builds two scaled
  `b2PolygonShape` copies and calls the collide dispatcher at 0x1402ed930.
* 0x14008b220 — `operator delete[]` helper for 44-byte (0x2c) elements with
  the MSVC sized-array guard; 0x14008b0b0 — same for 24-byte elements.
* 0x1400e5b30 — Intel copy-assign (`ReassignLinkNode(this+9, src+0x48)` + full
  field copy); 0x1400e5fd0 / 0x1400e6100 — Mark-derived copy helpers.
* 0x1400fe400 — MapShipBody maintenance: merge-sorts the +0x290 owner list and
  rebuilds shells.
* 0x1400eab10 / 0x1400eb460 — Intel serialise/field-copy routines (ISerializable
  + SetLink + sprintf log); 0x1400ec290 — Intel_polygon centroid-like float pass;
  0x1400f1940 — Location bulk op (VectorStride24_Insert + Reallocate).

## Key negative results (why the remaining 465 stay `stale label`)

* The embedded address in the label is wrong for every single row: 0 rows
  point at a function whose body hash matches. For the majority it is not a
  function entry at all (mid-instruction or undefined bytes).
* The bulk of 0x140000000–0x140070000 is std::vector/RbTree/string machinery.
  Renaming those by analogy to an existing helper would create near-duplicate
  names (forbidden by batch rule 8); they are recorded with their callee
  signature instead.
* 0x1400A0000–0x140100000 game logic is reached mostly through vtable calls and
  global property tables, so no unique class/role is proved without guessing
  (offsets +0x94, +0x2cc, +0x9ac, +0x818/+0x820 remain unidentified).
* 0x1400e4cc0 is a 5-byte import thunk (`jmp _invalid_parameter_noinfo_noreturn`),
  listed as `stale label`, not a body.

## Output

* Appended 492 rows to `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`
  (`addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`);
  previous b6 rows kept intact.
* Working dumps: `/tmp/opencode/hf_ghidra_sweep/b7a2_list.tsv`,
  `b7a2_vtstore.tsv`, `b7a2_vtclass.tsv`, `b7a2_twins.tsv` (0 twins).

## Counts

* audited: **492** (491 bodies + 1 thunk)
* renamed + plated: **27**
* stale label left: **465**
* unreadable: **0**
* byte-identical named twins found: **0**
