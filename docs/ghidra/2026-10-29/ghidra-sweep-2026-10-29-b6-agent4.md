# Ghidra sweep, batch 6 agent 4 — `rep_*` in `0x140200000–0x1402FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Range contains 851 functions, of which **361 were `rep_*`** at start.
**34 renamed, all plated.** No `save_program`, no tags, no README/STATUS edits,
no commits, no `create_function`.

| | before | after |
|---|---|---|
| `rep_*` in range | 361 | 327 |
| `FUN_*` in range | 15 | 15 (untouched) |
| named (non-`rep_`/`FUN_`) in range | 475 | 509 |

Audit table: `rep-audit-2026-10-29-q3.tsv` (361 rows, one per original `rep_*`,
`addr<TAB>old_label<TAB>verdict<TAB>new_name_or_identity<TAB>evidence`).

## Confirmation of batch 5's finding

Batch 5 agent 5 proved the `rep_*` labels are a signature-database artefact, not
ICF replicas, on `0x140000000–0x14006FFFF`. The same holds here, independently:

1. **No byte-identical twin.** SHA-1 of the raw bytes of all 5,155 function
   bodies: **0 of 361** in-range `rep_*` bodies match any other function in the
   image. ICF folding cannot leave 361 distinct-but-identical copies, so the
   "replica" premise is false for this range too.
2. **Normalised-instruction twins: also 0.** I built a relocation-normalised
   signature (mnemonic + operand kinds, scalars kept, code targets replaced by
   callee name, data targets by string value) for every function and compared
   all 361: no `rep_*` matches any named function even after normalisation.
   These are not copies of anything already named.
3. **Embedded targets are mostly not functions.** Of 350 names that parse as
   `rep_<hex>_<name>`:

   | embedded target points at | count |
   |---|---|
   | inside an unrelated function (mid-instruction) | 259 |
   | undefined bytes | 54 |
   | a real function entry | 3 |
   | no embedded address (`rep_wrap_0_*`, `rep__File_*`) | 11 |

   The three "entry" hits are themselves `rep_*`/unnamed (`0x14026e240` →
   `0x14024c690`, `0x140281aa0` → `0x14025f7f0`, `0x140286a60` →
   `0x14005e3f0`), so none of them is real identity evidence either.
4. **Sizes contradict the imports.** `sqrtf`/`free`/`memcmp` "replicas" of
   2–5 KB: `0x140217470` = 8,650 B "cosf", `0x1402e3580` = 4,845 B
   "deallocateString?", `0x1402e1420` = 2,855 B "operator<<" (actually
   `Sprite_SerializeToStream`), `0x1402dbb20` = 3,879 B "free".

**Method used for re-identification** was body-first, never the label:
`run_script_inline` listing (address, size, embedded target, body SHA-1,
callees, string literals, CALL/DATA xrefs), a global body-hash index, a
feature/Jaccard match against named functions (callee set ∪ string set), a
`RUNTIME_FUNCTION`-xref scan, a vtable/RTTI resolver, then targeted
`batch_decompile` (≤10 at a time) to read the body of each candidate. A name was
applied only when the body itself proved the role. 34 bodies did; the other 327
are catalogued as `stale label` with their structural evidence and a partial
identity tag. No name was taken from an embedded target.

Vtable scan note: only **one** in-range `rep_*` is referenced from a vtable
(`0x140210450`, slot 1 of `0x140369340`, whose RTTI could not be resolved). The
remaining 360 have only `.pdata` data xrefs (`0x1480xxxx`) or table pointers
(`0x1403axxxx`), so RTTI could not be used as a mass-identification channel in
this range.

## Renames (34)

All of these had an embedded label (or `rep_wrap_*` wrapper label) that the body
disproves. Old labels are preserved in the TSV.

### Object model / destructors (2)

| addr | new name | body evidence |
|---|---|---|
| 0x14027f310 | `Node_Destructor` | stores `NodeVFTABLE`; unlinks from `DeadNodeList`, calls master vtable, `SetLink(...,0)` per link, deletes joints via vtable slot 0 and children via the `ISerializable` destructor slot, frees all DLL cells/heads, name, `freeLinkMemory_` on owner/link2/master, then `ISerializable_Destructor`. This is the base destructor that batch 5 could see only as a caller of the (stale) name `rep_14025d060_..._free`; its real address is in this range. |
| 0x14027f930 | `Node_ScalarDeletingDestructor` | `Node_Destructor(this)` then `if (flag & 1) free(this)`; returns `this`. |

### File / profile I/O (5)

| addr | new name | body evidence |
|---|---|---|
| 0x140212850 | `ShipDesign_EnumerateDesignFiles` | `SetCurrentDirectoryA("Objects/Designs")`, `SetCurrentDirectoryA("Ships")`, `FindFirstFileA`/`FindNextFileA`, keeps names ending `.seria`, looks them up in the global design tree; callers `ShipDesign_LoadFromFile`, `DrawShipworksScreen`. |
| 0x14021a2d0 | `Profile_EnumerateSeriaFiles` | generic directory lister `(path, outVector, requireSeria, prefixPath)`; `SetCurrentDirectoryA(param_1)`, `FindFirstFileA`, `.seria` suffix test, optional `path + "/"` prefix; caller `Profile_LoadSavesFromFolder`. |
| 0x1402169d0 | `File_EnumerateSubdirectories` | appends `/*.*` and collects only entries with `FILE_ATTRIBUTE_DIRECTORY`, skipping `.`/`..`, into a `std::string` vector; caller `Profile_EnumerateScreenshots`. |
| 0x1402412f0 | `File_DeleteFolderRecursive` | `FindFirstFileA` loop: `DeleteFileA` for files, recursive self-call for directories, then `RemoveDirectoryA(path)`. |
| 0x140292840 | `Profile_BuildSavePath` | builds `Saves/Profile_<id>/` or `SavesSkirmish/Profile_<id>/` from `*(profile+0xb0)` and `rightPadEscadraWithParam`. |

### Serialization (4 + 1 mesh)

| addr | new name | body evidence |
|---|---|---|
| 0x1402e1420 | `Sprite_SerializeToStream` | `ISerializable::SerializeHeader` then writes every Sprite key: `m_type`, `m_position.x/y`, `m_angle`, `m_z`, `m_scale.x/y`, `m_tile`, `m_adjust`, `m_animation_name/filename/speed`, `m_stage`, `m_opacity`, `m_ambient`, `m_mask`, `m_focusable`, `m_color.r/g/b/a`, `m_slot_constrain`, `m_debris`, `m_anistates`, `m_blend_mode`, `m_animation_mode`, `m_param_*`, `m_outlineBold`. |
| 0x1402de300 | `Sprite_DeserializeFromStream` | logs `Deser starts for object %s`, expects `{`, then matches keys `m_classname`, `m_name`, `m_animation`, `m_delay`, `m_mode`, `m_scale`, … and writes the corresponding members. |
| 0x1402dd440 | `Slot_SerializeToStream` | `m_master.id`, `m_block.id`, `m_bind`, `m_type`, `is_master`, `is_slave`, `m_position.x/y`, `craftOid`, `isRightDirection`. |
| 0x14027efe0 | `Mesh_SerializeToStream` | writes `m_classname=Mesh`, `m_size=<n>` and n float pairs from the vertex array; returns 0 if the stream is closed. |
| 0x1402e6f90 | `VideoSettings_RegisterProperties` | sets defaults (enabled, `maxParticles=20000`), then `AddProperty` for `VideoSettings_maxParticles`, `..._isRenderClouds`, `..._isRenderBloom`, `..._isShowRain`, `..._isRenderProfiler`, … |

### Property registration / constructors (9)

| addr | new name | body evidence |
|---|---|---|
| 0x14023fbd0 | `Npc_RegisterProperties` | 20+ `AddProperty` calls: `m_name`, `m_fullname`, `m_description`, `m_location`, `m_ship_first`, `m_ship_first_seed`, `m_diplomacy`, `m_greetings`, `m_joined`, `m_arrested`, `m_dead`, `m_tarkhan`, `m_nation`, `m_female`, `m_age`, `m_loyalty`, `m_arch_fear/gerat/romani/faith/right/force/wealth`. |
| 0x14023f880 | `Item_RegisterIndexCountProperties` | `AddProperty("m_index" @this+0x48)`, `AddProperty("m_count" @this+0x4c)`; decompiler types `this` as `Item *`; caller is the Item constructor 0x140293bb0. |
| 0x14023f970 | `Keybind_Constructor` | `CopyString("Keybind")`, `+0x28 = 0x2000000003`, registers `m_keycode` and `m_itemcode`. |
| 0x14023fa80 | `PositionScale_RegisterProperties` | `m_position.x`, `m_position.y`, `m_scale` as FProperty. |
| 0x140282140 | `StatList_RegisterProperties` | VProperty `m_stats` bound to `StatListBase`. |
| 0x1402ac160 | `PointWithAge_RegisterProperties` | `position.x`, `position.y`, `age` as FProperty. |
| 0x140293bb0 | `Item_Constructor` | `CopyString("Item")`, `ISerializable` ctor, `Item_RegisterIndexCountProperties`, `List_MergeSortByStat154`. |
| 0x140292fa0 | `Npc_Constructor` | `CopyString("NPC")`, default name `"Paladin Mk2"`, randomises gender/age/nation via HGE slot +0x108, calls the property-registration vtable slot. |
| 0x1402ac0b0 | `RadioBeacon_Constructor` | `CopyString("RadioBeacon")`, `+0x28 = 0x40000`, base ctor via vtable +0x38, inserts into the global beacon list. |

### Loadout library (3) + profiler (2)

| addr | new name | body evidence |
|---|---|---|
| 0x14028bb70 | `Loadout_BuildLibrary` | creates a `Node(0x128)`, names it `"LOADOUTS_LIBRARY"`, `DefinePart` for every `PLANE_TLL` part. |
| 0x14028c5e0 | `Loadout_BuildUnreadyCraftsLibrary` | creates `"CRAFTS_UNREADY_LIBRARY"`, `Fleet_SetCompData(...,1,0)` then `DefinePart(ALL_PARTS, …)`. |
| 0x14028c760 | `Loadout_RebuildLibraryFromProfile` | clears the owner's `Link` lists and string-pair vector, recreates `"LOADOUTS_LIBRARY"`, `Fleet_SetCompData(owner+0x540,0,1)`, then repopulates from the profile comp data. |
| 0x1402ab080 | `Profiler_CreateMainLoopNode` | creates the Profiler_Node labelled `"MAIN LOOP"` under `"PROFILER"`; user `PrepareMainLoop`. |
| 0x1402ab180 | `Profiler_Node_Constructor` | class name `"Profiler_Node"`/`"IObject"`, copies the label, initialises the child vector. |

### Video / map / city / HUD (6)

| addr | new name | body evidence |
|---|---|---|
| 0x14027e6c0 | `Video_LogDdrawMemoryInfo` | `LoadLibraryA("ddraw.dll")` + `DirectDrawCreateEx`, four `GetAvailableVidMem` queries, `WriteToClientLog` of `VIDEO MEMORY TEST…`, `Texture memory…`, `Non-local…`, `Local…`. |
| 0x1402fbdb0 | `Map_RenderSkyLayers` | scans `GlobalNode_` children for bodies named `MAP_MAP`/`MAP_SKY`/`MAP_SKY2`, swaps their depths, sets the sky zoom (`powf`) and draws through `RenderState_ConstructorEx`. |
| 0x1402d51b0 | `City_InitBuildingTypes` | clears/refills the global building table with `{code, "build_hydro_01"…"build_telecom_02", height, scale}`; called from `Scene_IsReadyToExit`. |
| 0x1402f47e0 | `Hud_TransformMarkerToScreen` | `cosf`/`sinf` of the marker angle, `TARGET_SCREEN_*`, `FAST_SHAKE_*`/`SLOW_SHAKE_*`, `ZOOM_LEVEL` scaling, `Hud_MarkerSetColor`, marker draw. |
| 0x140280bb0 | `Node_Reflect` | walks children calling vtable +0x90, logs `ERR: Node::reflect failed with %s, m_id %i`. |
| 0x1402dd2e0 | `Slot_LogRelinkError` | `WriteToClientLog("ERR: Slot::relink failed, with m_master.id = %i." / "... m_block.id = %i.")`. |

### Misc (3)

| addr | new name | body evidence |
|---|---|---|
| 0x1402860a0 | `Map_ThrowInvalidKey` | `std::_Xout_of_range("invalid map<K, T> key")`, no return. |
| 0x1402e4c00 | `Sound_CompactAudioChannelArrays` | walks 13 global audio-channel arrays, destroys inactive objects through their vtable and compacts the surviving slots; called from `App_ReloadSeria`. |
| 0x14027f310/0x14027f930 | see Node pair above | |

## Left as `stale label` (327)

Every row is in the TSV with its old label, structural evidence (embedded-target
class, callees, strings, callers, "no byte-identical twin") and a partial-identity
tag. Grouped:

| partial identity | count |
|---|---|
| container/sort/CRT-style helper (RbTree/Map/Link/vector/mem* callees) | 87 |
| unidentified (no strings, few distinctive callees) | 82 |
| math/vector helper (one or two of sqrtf/cosf/sinf/powf/floorf/atan2f) | 40 |
| member cleanup / free helper (`free` + small body) | 37 |
| constructor-like object builder (calls `New`/copy helpers) | 20 |
| container-growth helper (`vectorTooLong`/`_Xlength_error`/insert) | 19 |
| serializable / deleting destructor variant | 14 |
| serializable constructor variant | 8 |
| strategic-map / radio-panel UI helper | 7 |
| GUI panel / skin builder | 4 |
| menu-dialog widget builder | 4 |
| logging / diagnostic helper | 3 |
| campaign/tutorial event helper | 2 |

High-value leads for a later pass (provable but not fully identified here):

* `0x1402e3580` (4,845 B) — copies a filename, splits the last 3 characters,
  `String_Tidy`/`CopyString`; strings `bladaway`, `fire_03`, `ricochet`,
  `war_attack` — a sound-effect name/resource resolver, not `deallocateString?`.
* `0x1402e1420`/`0x1402de300` are the only two Sprite (de)serializers; the
  matching `0x1402dd440` Slot and `0x14027efe0` Mesh partners are named.
* `0x1402898f0`, `0x140289970`, `0x140289b70`, `0x140289ca0` are four distinct
  member destructors called **only** from `Location_Destructor`; naming them
  needs the Location field offsets (not established here).
* `0x140293dc0`, `0x140293ea0` — 218/234 B `memcmp` + `free`; called from
  `rightPadInteger` / `spawnEndgameShips?`, role not proven.
* `0x1402fa610` (6,041 B) — biggest body in the range, HUD render pipeline; not
  decompiled (over the 0x2000-byte rule).
* `0x140217470` (8,650 B, label "cosf") — second biggest; body calls
  `_Init_thread_header/_Init_thread_footer` + `cosf`, i.e. a function-local
  static initialiser that repeats a trigonometric body; left untouched.

## Counts

* renamed: **34**, all plated
* stale label recorded: **327**
* unreadable / skipped (>0x2000 B, not decompiled): **0** in this range needed a
  body read to be rejected; the two >0x2000 B bodies above are catalogued
  structurally only.
* `rep_*` left in range: **327**
* `FUN_*` untouched: **15**
* functions created: **0**
