# Ghidra sweep batch 8, agent 4 — `rep_*` re-match 0x140000000–0x1400FFFFF (Q1)

Program `Highfleet.exe.unpacked.exe` v1.163 (project `HighfleetServer`).
Scope: every current `rep_*` function in `0x140000000–0x1400FFFFF` minus every
address in `docs/data/funclet-ownership-2026-10-29.tsv` (both the
`funclet_addr` and `owner_addr` columns; 1,269 unique addresses, 122 below
`0x140100000`).

**410 functions audited. 26 renamed + plated. 384 stale labels left (each with a
sharper identity than batch 7). 0 unreadable.**

No `save_program`, no tags, no README/STATUS edits, no commits, no
`create_function`.

| | before | after |
|---|---|---|
| `rep_*` in scope | 410 | 384 |
| renamed this pass | — | 26 |
| q1 rows appended | — | 410 |

The drop from batch 7's 492 to 410 is the 55 funclet-owner renames done by
agents 3/7 plus batch 7's own 27.

## Method

1. Enumerated the current `rep_*` set with an inline script (entry, body size,
   SHA-1 of the exact body bytes, current label, callee set, instruction
   string references, callers) into `/tmp/opencode/hf_ghidra_sweep/b8a4_list.tsv`,
   `b8a4_refs.tsv`, `b8a4_callers.tsv`, `b8a4_vtstore.tsv`.
2. Rebuilt the RTTI reader for this binary: **the COL stores its
   `TypeDescriptor` / `ClassHierarchyDescriptor` pointers as 32-bit image
   relative offsets at COL+0x0C / COL+0x10**, not as 64-bit pointers. With that
   correction 247 vtables in `0x140300000–0x1403A0000` resolve; 13 in-scope
   `rep_*` bodies reference one and each was decompiled and classified
   (constructor vs base destructor vs deleting destructor vs factory).
3. Fresh byte-identical-twin test against every currently named function:
   the only hash matches are the 26 functions renamed in this same pass
   (self-matches). **0 genuine named twins** — the "replica" premise is still
   false.
4. Decompiled in batches of ≤10. Every rename below is proved from the body
   (vtable install, class literal, chained constructor/destructor, or unique
   string/callee), never from the embedded label.

## Renames (26) — all with doc plates

### Lifecycle / RTTI-proved (11)

| addr | new name | proof |
|---|---|---|
| 0x14005e0d0 | `HistoryDesign_Constructor` | `ISerializable::ISerializable` + `HistoryDesignVFTABLE` + `HistoryDesign_InitBaseFields`, then copies name/code/string/property fields from the source record (the copy ctor is 0x14005df60) |
| 0x140082b90 | `FileOStream_Destructor` | installs `.?AV?$basic_ofstream…` (0x140356810), chains `FileBuf_Destructor`, `~basic_ostream`, `~basic_ios` |
| 0x1400871e0 | `Effect_BaseDestructor` | installs `EffectVFTABLE`, frees owned shader/property vectors, leaves `IShader` vtable; the deleting wrapper `Effect_Destructor` @0x1400874a0 calls it |
| 0x14008e290 | `ShaderDeferringCloseAndPrebloom_Constructor` | `EffectConstructor` + 0x140357310 `.?AVShaderDeferringCloseAndPrebloom@@` |
| 0x140093d50 | `ShaderGlitch_Constructor` | `EffectConstructor` + 0x140357d90 `.?AVShaderGlitch@@` + `CSGlitch_Constructor` |
| 0x1400e5040 | `Intel_Destructor` | `IntelVFTABLE`, destroys owned NPC/strings/Links, chains `ISerializable_Destructor` |
| 0x1400e5290 | `Launched_Destructor` | `LaunchedVFTABLE`, frees Links/name, chains `Mark_Destructor` |
| 0x1400e5b30 | `Intel_CopyAssign` | `ReassignLinkNode(this+0x48,src+0x48)` + full scalar/string/polygon copy, ends on virtual +0x30; called by `Intel_CopyConstructor` |
| 0x1400ec290 | `Intel_RecomputeCentroid` | averages `IntelPolygon` vertices, writes +0xb8/+0xbc when +0x88 == 2 |
| 0x1400fde10 | `IntelPolygonList_AppendCopy` | 0x40-byte list node with `IntelPolygon` vtable 0x14035dfe8 + `Property_CopyAssign` + link |
| 0x1400f9090 | `Escadra_DestroyAndSelectNextFleet` | player-escadra branch finds another fleet with speed>0 and calls `MapUi_SelectFleet`, then `Node_KillSelf` |

### Factories (2)

| addr | new name | proof |
|---|---|---|
| 0x1400839d0 | `RenderTarget_Create` | device vtable +0x28/+0x38/+0x48 create texture + views, allocates 0x60 B, installs `TextureSingle` then `RenderTarget` vtables (inlined derived ctor) |
| 0x1400852b0 | `TextureSingle_CreateFromMemory` | `D3DX11CreateTextureFromMemory`, allocates 0x58 B, `TextureSingle` vtable; called twice by `Texture_Load` |

### `InitBaseFields` family (3)

Same shape as the already-named `Escadra_InitBaseFields` / `MapCraft_InitBaseFields`:
class-name literal + numeric code + property-record load.

| addr | new name | proof |
|---|---|---|
| 0x1400f7db0 | `Intel_InitBaseFields` | name `"Intel"`, code 0x203, `INTEL_INIT` |
| 0x1400f80d0 | `Location_InitBaseFields` | name `"Location"`, code 199, `"City_generated.seria"` |
| 0x1400f8370 | `Mark_InitBaseFields` | name `"Mark"`, `CODE_MARK`, `MARK_INIT` |

### STL `basic_filebuf` virtual overrides (7)

The binary already had `FileBuf_Destructor/_ScalarDeletingDestructor/_Sync/_SetBuf/_PBackFail/_Lock/_Unlock`;
these complete the vtable.

| addr | new name | proof |
|---|---|---|
| 0x140085bf0 | `FileBuf_Overflow` | `overflow`: pending char via FILE at +0x80, put-area maintenance |
| 0x140086210 | `FileBuf_SeekOff` | `seekoff`: flush, `_fseeki64`/`fgetpos`, `_Reset_back` |
| 0x1400862e0 | `FileBuf_SeekPos` | `seekpos`: flush, `fsetpos`, rebuild get area |
| 0x1400869c0 | `FileBuf_Underflow` | `underflow`: buffered char / refill with `ungetc` pushback |
| 0x140086d70 | `FileBuf_Xsgetn` | `xsgetn`: buffered copy + `fread` |
| 0x140086ee0 | `FileBuf_Xsputn` | `xsputn`: put-area copy + `fwrite` |
| 0x140083860 | `FileBuf_Close` | `close`: `fwrite` pending, `fclose(+0x80)`, `_Init` |

### Misc (3)

| addr | new name | proof |
|---|---|---|
| 0x140088db0 | `Shader_CompileFromFile` | builds `Shaders/<name>.hlsl`, `D3DReadFileToBlob`+`D3DCompileFromFile`, caches `.bin`, `"Missing Shader File"` box; shared by `PShader_CompileFromFile`/`VShader_CompileFromFile` |
| 0x1400ea6e0 | `Location_CreateMapGuiNode` | creates a GUI node registered as `MAP_LOCATION`, links +0x2d0 ↔ node, hides it |
| 0x1400f0f00 | `MapShipBody_ClearOwnerList` | virtual-deletes each member of the list head at +0x288, frees nodes, zeroes +0x290 |

(Counts: 11 lifecycle + 2 factories + 3 init + 7 filebuf + 3 misc = 26.)

## New sharper stale identities (no rename, still `stale label`)

These are the rows where the role is now proved but a unique, non-colliding
name is not:

* 0x14004a2f0 — body overlap test: two `b2PolygonShape` copies scaled by 0.05
  from the shapes at +0x168/+0x178, passed to the b2 collide dispatcher
  0x1402ed930.
* 0x1400e8f70 — `Node::add` override that inserts a missile property and
  renumbers children by missile field +0x168.
* 0x1400e9100 — ship-part reinit: `TransferShopItem`, `DefinePart(ALL_PARTS,name)`,
  clears Links, invokes part vtable slot +0x48.
* 0x1400f05a0 — linked-list teardown whose elements use the `Escadra`
  destructor 0x1400e36a0.
* 0x1400f74b0 — profile lookup by name: walks `Get_Profile()` escadra list,
  `memcmp` of the +0xb0 names.
* 0x1400f8e00 — distance predicate: sqrt(squared delta +0x150/+0x154 vs
  +0x25c/+0x260) < 100.
* 0x1400f5080 — grid-cell → world position (rotation +0x15c, 10-unit spacing).
* 0x1400f0620 — escort offset: keeps +0x2d0 150..500 units from the target
  along heading +0x530.
* 0x1400ea840 — repair-point distribution: proportional `ceilf` split over
  property children, calls `GetStats`.
* 0x1400eea70 — garrison transfer: merge adjacent fleet, reassign Links,
  `"TO GARRISON - 1"`/`"- 2"`.
* 0x1400ba0f0 — creates `EVENT_DISCONTENT_01` trigger when the player owns
  more than one escadra.
* 0x1400dda20 — editor: destroys first player creature, `EDITORCPP`, refreshes
  `ED_SHPWRK_LIST`.
* 0x1400f3c10 / 0x1400f4070 — missile motion offset vs backward offset along
  heading, both with `CHECK ERROR … Escadra.cpp` NaN logging.
* 0x1400f85d0 / 0x1400f89b0 — collect every editor part-library global into a
  vector and forward it + `*(this+0x520)` to `BuyPartShop` (0x140204140) /
  0x140204230.
* 0x1400f9170 / 0x1400f92b0 — paired map-mode on/off: child scale fields
  +0x564.., flag +0x461, `MAPMODE_THRUST_SLIDER` 1.0 vs 0.0, missile +0x16c.
* 0x1400f9460 — statistics display (`CalculateStats`/`GetStats` +
  `WriteToClientLog`).

All other stale rows now carry: body size, SHA-1, whether the embedded label
target is a function entry, the first string literals, up to two callers and
the callee signature.

## Negative results

* The embedded address in the label is still not the function's identity:
  the target is not a function entry for the overwhelming majority (mid-instruction
  or undefined bytes). 0 rows point at a same-body function.
* 0x1400E4CC0 is a 5-byte import thunk (`jmp _invalid_parameter_noinfo_noreturn`),
  not a body — recorded as `stale label`.
* The remaining 0x140000000–0x140070000 population is std::vector / RbTree /
  string / fstream machinery. Renaming by analogy to an existing helper would
  create the near-duplicate names forbidden by batch rule 8; it is recorded with
  the callee/string signature instead.
* 14 of the 52-byte `ShaderData_ResetVTable(); if(flag) free(this)` bodies remain
  the templated `ConstantBuffer<T>` slot-1 deleting destructor. They are not
  individually nameable without inventing per-instantiation suffixes.

## Output

* Appended **410** rows to `hf_notes/docs/data/rep-audit-2026-10-29-q1.tsv`
  (`addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`);
  the 1,006 batch-6/7 rows are untouched (file now 1,416 rows).
* Working dumps: `/tmp/opencode/hf_ghidra_sweep/b8a4_list.tsv`,
  `b8a4_refs.tsv`, `b8a4_callers.tsv`, `b8a4_vtstore.tsv`,
  `b8a4_funcentries.txt`, `b8a4_exclude.txt`.

## Counts

* audited: **410**
* renamed + plated: **26**
* stale label left: **384**
* unreadable: **0**
* byte-identical named twins: **0**
