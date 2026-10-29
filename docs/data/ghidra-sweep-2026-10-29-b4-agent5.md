# Ghidra sweep 2026-10-29 — batch 4, agent 5 (GUI / containers / large leftovers)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Ranges: `0x140120000–0x1401AFFFF` and `0x140200000–0x1402FFFFF`.
Only previously unnamed `FUN_*` functions were renamed; every name carries a
doc plate (summary / `Algorithm:` / `Parameters:` / `Returns:`).
`rep_*` ICF bodies were deliberately left alone (they duplicate already-named
functions).

## Renames

### HGE media layer and resource proxies (0x140174x / 0x140178x / 0x14017cx)

`HGEVFTABLE` (`0x1403672f0`) **is** populated with real code pointers, so the
resource-proxy slot map could finally be resolved. Slots used by the proxies:

| slot | target | meaning |
|---|---|---|
| +0x90 | 0x140174850 | `Resource_LoadFileData` |
| +0x98 | 0x140174840 | file-buffer free |
| +0x138 | 0x14017c440 | `Sound_Load` |
| +0x140 | 0x14017c420 | `Sound_Free` |
| +0x160 | `Music_Load` (named) | music load |
| +0x168 | 0x14017c7a0 | `Music_Free` |
| +0x178 | 0x14017c9c0 | `Music_SetAmplify` |
| +0x1c0 | `Stream_Load` (named) | stream load |
| +0x1c8 | `Stream_Free` (named) | stream free |
| +0x300 | 0x14016cbb0 | **unresolved** (thunk into 0x1400839d0) |
| +0x310 | 0x14016cd50 | **unresolved** (calls MessageBoxA thunk) |

The targets at +0x90/+0x98/+0x138/+0x140/+0x168/+0x178 had **no function
object**; they were created with `create_function` and named (noted here per the
batch rule).

| addr | new name | description |
|---|---|---|
| 0x140174840 | `Resource_FreeFileData` | free of a buffer from `Resource_LoadFileData`. |
| 0x140174850 | `Resource_LoadFileData` | loads a resource from the attached ZIP packs (unz* scan + `uncompressFile_`), else falls back to the HGE disk loader at vtable +0x88. |
| 0x14017c420 | `Sound_Free` | `BASS_SampleFree`. |
| 0x14017c440 | `Sound_Load` | `BASS_SampleLoad`, with decode-via-`BASS_StreamCreateFile` + `BASS_SampleCreate` fallback. |
| 0x14017c7a0 | `Music_Free` | `BASS_MusicFree`. |
| 0x14017c9c0 | `Music_SetAmplify` | `BASS_ChannelSetAttribute(handle, 0x100)` (BASS_ATTRIB_MUSIC_AMPLIFY). |
| 0x140178a60 | `Media_ReleaseSound` | proxy release through slot +0x140. |
| 0x140178b10 | `Media_ReleaseMusic` | proxy release through slot +0x168. |
| 0x140178bc0 | `Media_ReleaseFileData` | proxy release through slot +0x98. |
| 0x140178c70 | `Media_ReleaseStream` | proxy release through slot +0x1c8. |
| 0x140178d20 | `Media_FreeHandle` | calls the handle's own vtable slot 0 (destroy). |
| 0x140178ff0 | `Media_EnsureSound` | lazy `Sound_Load` (slot +0x138). |
| 0x140179100 | `Media_EnsureMusic` | lazy `Music_Load` (slot +0x160) then `Music_SetAmplify` with proxy+0x120. |
| 0x1401791e0 | `Media_EnsureFileData` | lazy `Resource_LoadFileData` (slot +0x90). |
| 0x140179380 | `Media_EnsureStream` | lazy `Stream_Load` (slot +0x1c0). |

### GUI / container internals (0x14012xxxx, 0x14015Cxxx)

| addr | new name | description |
|---|---|---|
| 0x140121560 | `Array_FreeStride24` | frees a 0x18-stride vector block. |
| 0x140121580 | `Array_DestroyRange24` | string range destructor, 0x18 stride. |
| 0x140121870 | `Array_CopyConstruct24` | copy-constructs N 0x18-byte elements. |
| 0x140122a70 | `Vector24_At` | bounds-checked element access, 0x18 stride. |
| 0x1401261c0 | `Array_Resize24` | shrink/grow of a 0x18-stride vector. |
| 0x14012a190 | `PairCaptain_CopyConstruct` | copy-constructs (byte, Captain); Captain at +8. |
| 0x14012a480 | `PairCaptain_CopyConstructFrom` | pair-to-pair copy of the same layout. |
| 0x14012b610 | `Array_DestroyRange88` | range destructor of 0x58-byte elements (+8 sub-object). |
| 0x14012b670 | `Array_FreeStride48` | frees a 0x30-stride block with over-alignment recovery. |
| 0x14012c840 | `Math_Vec2Divide` | 2-D vector divided by a scalar. |
| 0x14012c9a0 | `String_PushBack` | std::string one-char append with SSO handling. |
| 0x14012cb40 | `Gui_ScalarDeletingDestructor` | 0xe80-byte screen object deleting destructor. |
| 0x14015c180 | `Array_DestroyRange88` | same range destructor (ICF-adjacent copy). |
| 0x14015c2d0 | `Array_CopyConstruct88Captain` | copy-constructs 0x58-byte (value, Captain) records. |
| 0x14015c3d0 | `Gui_PushPointerChild` | push_back into the child pointer vector at +0xe70. |
| 0x14015cd50 | `Gui_ClearChildLists` | frees child pointers, Link array and parent back-links. |
| 0x14015cdf0 | `Array_FreeStride88` | frees a 0x58-stride block (over-aligned). |
| 0x14015ce80 | `Gui_RotateChildIndex` | rotates the child index +0xe90 and each child's +0x18 index. |
| 0x14015cf80 | `Array_PopBack88Captain` | erases the last 0x58-byte (value, Captain) element. |

## Skipped / open

* **0x140179410 / 0x140179460** — media proxies using HGE vtable +0x300 / +0x310.
  The slot targets (0x14016cbb0, 0x14016cd50) are a thunk into 0x1400839d0 and a
  `MessageBoxA` wrapper, which does not fit a media type; the owning proxy class
  is not proven, so both stay unnamed.
* **0x1401787a0, 0x1401787f0, 0x140178840, 0x140178890, 0x1401788e0** — five
  identical 70-byte scalar-deleting destructors of the media proxies; a per-class
  name would be a guess (same reason batch 3 skipped their 0x140170xxx twins).
* **0x14017c220 / 0x14017c7c0** — BASS channel helpers (`BASS_ChannelGetInfo` +
  `SetAttribute(chan,1)` / `GetAttribute(chan,0x100)`); which BASS attribute each
  maps to could not be confirmed from the decompile, so left unnamed.
* (filled in below as the sweep continues)

### Fleet / shop generation (0x1401A7xxx, 0x140205xxx, 0x140206xxx)

This cluster resolves the long-open `0x1401a7120` / `0x140205ae0` /
`0x140206060` / `0x140206950` group: they are the **random fleet and shop
generator**, not a UI/rect builder.

| addr | new name | description |
|---|---|---|
| 0x1401a7120 | `Fleet_CreateRandomEscadra` | takes up to five ship counts (five price buckets) plus a max-size pointer, builds the name list, constructs the Escadra, tops it up to >= 8 ships, Fisher-Yates shuffles with MT19937 (seed 0x1571) and stores a random encounter value at fleet+0x56c. |
| 0x1401a7a40 | `Fleet_AddNamedShipToPool` | resolves a hull through `GlobalNode_` vtable +0xb8, reads its price at +0x15f8 and appends (name, price) to the bucket enabled by the five flag bytes (<=15, <=25, <=40, <=75, >75). |
| 0x140205ae0 | `Fleet_GenerateShipNames` | builds the full vanilla hull-name pool, shuffles it with `rand()` and calls the budget selector. |
| 0x140206060 | `Fleet_SelectShipsForBudget` | samples up to 10 records, accumulates prices under budget+20%, keeps the best group with >=1/2/3 ships and copies its names out. |
| 0x140206950 | `Fleet_BuildShopOffer` | hard-coded shop catalogue (Courageous ... Archangel) gated by four flags, with prices from +0x15f8, then the budget selector. |

**Correction to batch 4 agent 4's plate.** `0x1401c2ba0` is named
`Captain_CreatePanelForSlot` there and described as "maps the slot id to a
rectangle preset and forwards it to the generic panel builder 0x1401a7120".
Its arguments are ship counts (0x1e=30, 0x19=25, 0x50=80, 0x78=120,
0x96=150, 0xe1=225, 0x168=360) fed to the fleet generator above, so it is a
**fleet-composition preset switch**, not a captain card. The function is in
agent 4's range and already named, so I did not touch it; question posted on
the blackboard. `0x1401c7270` is likewise in agent 4's range.

### Other named singletons / helpers

| addr | new name | description |
|---|---|---|
| 0x140161ac0 | `Profile_IsInitialised` | `BOOL_147fc6f80 || DAT_147fc6f81` — gate used by `!ClickFunc` and `precombatOk`. |
| 0x14016c130 | `Vector12_Size` | element count of a 0xc-stride vector. |
| 0x14016fed0 | `Array_FreeStride40String` | string range destroy + over-aligned free of a 0x28-stride vector. |
| 0x140170ae0 | `Resource_ClearHashLists` | empties the 13 resource hash buckets at HGE+0x10. |
| 0x140185bd0 | `SingletonUnknown_DeletingDestructor2` | deleting destructor with vtable 0x1403684a0; class not proven, name is structural only. |
| 0x1401875c0 | `Global_ClearLinkNode` | clears the global Link at 0x1403c0d98. |
| 0x1401875e0 | `Global_SetLinkNode` | points that Link at a body (class byte low nibble 0xf) and runs the hover refresh. |
| 0x140188570 | `Input_RemapKeyByMode` | key -> binding lookup using `bindingMapmode` / `bindingOther` / `binding` by game mode. |
| 0x140188740 | `Bindings_FindValueByKey` | red-black lookup in the binding tree at +0x48, value at +0x1c, -1 when absent. |
| 0x14018d8c0 | `Scene_UpdateHoveredNode` | hover/pick refresh; confirms 0x14021b240 is the spatial pick. |
| 0x14021b240 | `Scene_PickNodeAtScreenPoint` | walks the 10000-node-per-cell table at 0x143a531c0, calls vtable +0x2a0 per candidate, special-cases `LOOT_BOX`. |
| 0x140220620 | `Math_AngleInRange` | 2pi-wrapped arc membership test. |
| 0x14024d960 | `ShipDesign_LoadFromFile` | loads an `ED_SAVELOAD_LIST` ship design into the profile (`.png` screenshot, `Creature_UpdateDesignStats`). |
| 0x140295500 | `Profile_LoadSaveFile` | property-stream loader for a save/profile (`m_savename`, `m_scores`, `m_unlocks`, `APP::GLOBAL_TIME`, ...). |
| 0x14029b3e0 | `Hud_DrawMapSignLabels` | draws the `sign_LA29/T7/GPB/NAR/AAM/GUN` map labels. |
| 0x1402da8f0 | `Precombat_BuildShipGroups` | groups fleet ships for the pre-combat screen, clamping each group's bounds to the level and writing creature+0x264. |
| 0x1402d3c10 | `Creature_ComputeBoundsInRect` | part bounds + radius clamped to a rect. |
| 0x1402d5140 | `Scene_IsReadyToExit` | GlobalNode vtable +0x80/+0x90 guard before leaving a scene. |
| 0x1402f5410 | `Sprite_GetMinDimension` | minimum sprite +0x5c over a range of sprite lists. |

### Container / sort clones (0x14019Axxx–0x1401AFxxx)

Named by stride/instantiation, all with plates. Grouped by family rather than
one row per address:

* **std::vector insert / resize / free**: `VectorAmmo_GrowInsert` (0x14019a380),
  `VectorString32_InsertRange` (0x14019abe0), `VectorLink56_InsertAt`
  (0x140196810), `Vector24_InsertValue` (0x1401969d0), `Vector16_InsertValue`
  (0x140196e80), `Vector16_InsertValueAlt` (0x140198980),
  `VectorCaptain_InsertAt` (0x1401973b0), `Vector8_ResizeFill` (0x1401ae260),
  `Vector12_PushBack` (0x140165990), `Vector40_At` (0x1401a6530),
  `Array_Resize24`, `Array_FreeStride8/12/24/40/48/72/88/272`,
  `Array_FreeStride40String`, `Array_FreeStride40Destroy`,
  `Array_ResetStride80` (0x1401ae580).
* **move / copy helpers**: `Array_MoveConstruct32String/40/40Alt/40Byte/40Int/
  40String/48/80/144`, `Array_MoveAssign32`, `Array_MoveBackward32String`,
  `Array_MoveBackwardString32`, `Array_CopyConstruct24/40Vector/40? /48LinkPair/
  56/56Link/80Captain/88Captain/240Link/272/Ammo`,
  `Array_CopyStride12/16/72`, `Array_AssignString32`, `Array_Fill8`,
  `Array_MovePointersRange`, `Array_MoveConstruct240Link(Alt)`.
* **range destructors**: `Array_DestroyStringRange24/32`,
  `Array_DestroyRange40/48LinkPair/56Link/88/Ammo/240Link`,
  `Array_DestroyRangeAmmo`, `Array_DeleteObjects50`, `Array_PopBack88Captain`.
* **sorts**: `Sort_Median3FloatWide`, `Sort_MedianOfNByStats`,
  `Sort_MedianOfNByCompData`, `Sort_PartitionByStatsKey`,
  `Sort_PartitionByFloat`, `Sort_PartitionByFloatF8`,
  `Sort_PartitionByTimeAndF8`, `Sort_IntrosortGeneric8`,
  `Sort_IntrosortGeneric8Alt`, `Math_MaxOfRandomSamples`.
* **trees / maps**: `RbTree_ReleaseNodes`, `RbTree_ReleaseNodesAndPayload`,
  `RbTree_DestroyTreeNodes(Alt)`, `Map_EraseNodeRebalance`,
  `Map_InsertU64Node(Alt)`, `Map_IteratorAdvanceCopy`,
  `List_InitCircular40`, `Ammo_DestroyRecord`, `String_Reset`, `String_Assign`.
* **GUI screen object**: `Gui_ScalarDeletingDestructor` (0x14012cb40),
  `Gui_PushPointerChild` (+0xe70 vector), `Gui_ClearChildLists`,
  `Gui_RotateChildIndex` (carousel index +0xe90 and per-child +0x18),
  `Gui_CreateOverlayElement` (0x1401a68d0, red opaque overlay + `GlobalNode_`).

## Skipped / open

### Large bodies left unnamed (reason: name would be a guess)

| addr | size | what was seen |
|---|---|---|
| 0x1402038e0 | 659 | prologue event spawn: looks up creature `UR`, calls `somethingSpawnShips` + Escadra ctor; event-specific, callers `restOfEventsPrologueAntIsaiah`. |
| 0x1402077c0 | 3.7 KB | prologue/endgame spawn, not read fully. |
| 0x1402114a0 | 2.4 KB | caller `SomethingWithLevelSerias`; float pass, not resolved. |
| 0x140211e60 | 1.4 KB | no strings, large control flow; not resolved. |
| 0x14021cf40 | 8.7 KB (70 KB decompiled) | only caller `repairSlider?`; one `CHECK ERROR` string. Not read. |
| 0x14021b110 | 117 B | name lookup via vtable +0xb8 then vector realloc + `+0x50` add; owning class unproven. |
| 0x14021fdb0 | 88 B | forwards to a `rep_` chunk of `Player_SendThrustCommands`; target ambiguous. |
| 0x140224ec0 | 884 B | scene reset / seria load, caller `!ClickFunc`. |
| 0x14022ad00 | 3.9 KB | `creatureLogic` helper, 4 KB, not read. |
| 0x140232830 / 0x140233490 | 1.5 K / 640 | pre-combat card layout maths (still open from batch 2). |
| 0x140245180 | 5.7 KB | draws `sign_shell_low/mid/hi/torpedo/missile/drone/prize` around ships and sets part +0x224; caller `afterBattleStars??`. Role (result overlay vs incoming-fire markers) not proven. |
| 0x140247850 | 1.8 KB | caller `afterBattleStars??`, no strings. |
| 0x140256a90 | 1.1 KB | frame/hull elevation + floor pass (batch 3 skip). |
| 0x140263700 | 1.4 KB | type-confused vector<...> code, not read. |
| 0x140268a30 | 162 | string repeat/append with confusing memcmp use (batch 3 skip). |
| 0x140269d00 | 731 | move-order direction codes 0x65/0x66/0x67/100; command ids undecoded. |
| 0x14028a980 | 1.2 KB | not read. |
| 0x14028bf80 | 1.2 KB | not read. |
| 0x1402943f0 | 3.6 KB | `Load` at 0x140293f90, DLL<Body> list handling. |
| 0x140296530 | 3 KB | `!ClickFunc` + free thunk caller; large int pass. |
| 0x140297100 | 2.4 KB | prologue event pass, `list too long`. |
| 0x1402a7f60 / 0x1402a8760 / 0x1402a9090 | 2 K / 896 / 615 | campaign/profile, aircraft "HIDDEN" loadout, aircraft-group merge; all still open from batch 3. |
| 0x1402038e0.. | | see above |
| 0x1402f5410 | — | **renamed**; note the "size" is a sprite dimension, not a game value. |

### Small unresolved

* `0x14015f6f0` / `0x14016c2a0` — halve / restore a float at +0x8f8 once,
  guarded by byte +0xc7c. Pair of toggles whose meaning (zoom? volume? scale?)
  is not proven; callers are `setupPropsSecondaryMapModes`.
* `0x14015f7b0`, `0x14015f7e0`, `0x14015f840`, `0x14015f8a0` — `GetStats(body+0x188)`
  getters for stat offsets +0xe8, +0xf0, +0xdc, +0x108. Those offsets are not in
  `structures.md` (documented neighbours: +0xe0 power_need, +0xf8 thrust), so
  naming them would be a guess.
* `0x140162fe0` — `object+0x88 == 0 || *(that+0x28) == 7`; mode-7 gate, class
  unknown.
* `0x14016a040` — resets a block (`vtable+0x48` kill, two lists, 0x40-stride
  vector) called by `makeSoundsForMapInstruments` and
  `setupPropsSecondaryMapModes`; owning type ambiguous.
* `0x14016a100`, `0x14016cf30`, `0x14016cd10`, `0x14016cd30` — one-line
  vtable-forwarding adapters.
* `0x14016dde0` / `0x14016ddf0` — bare setters of +0x1a4 / +0x1a0.
* `0x14016f010` / `0x14016f230` — propagate a value to +0x16c / via
  0x140172ee0 over 0x100-entry arrays; field meaning unknown.
* `0x1401701e0`, `0x1401787a0..0x1401788e0`, `0x1401a82c0/8340/8480/84b0/84e0`,
  `0x1401ae820`, `0x140187890/8b0`, `0x14018f940`, `0x140191f40`,
  `0x14028b340`, `0x140292820` — scalar-deleting destructors / free wrappers
  with unresolved vtables; a per-class name would be a guess.
* `0x140172550`, `0x1401725c0`, `0x140172aa0`, `0x140172b10`, `0x140172ee0` —
  quad/UV setup on a 4x record block with horizontal/vertical flip flags
  (+0x1a0/+0x1a1) and `HGE` vtable +0x2e0 push; likely texture-atlas UV code
  but not proven (could be the TextGrid glyph quads).
* `0x1401783c0` — 0x98-byte struct copy (compiler generated).
* `0x14017c220` / `0x14017c7c0` — BASS channel attribute helpers; the attribute
  id (1 / 0x100) was not decoded.
* `0x140179410` / `0x140179460` — media proxies on HGE slots +0x300/+0x310,
  whose targets do not look like media load/free (see HGE table above).
* `0x140181000`, `0x140181b60`, `0x140182d50`, `0x14018c320`, `0x14018f410`,
  `0x14018f910`, `0x14019ae0f/66/94`, `0x1401a4210/47c0/47f0/4b40/8510` —
  ZIP/inflate helpers, editor selection reset, locale facet getter and
  funclets/small record ctors; not resolvable without the owning types.
* `0x1402130b0` / `0x140213fc0` — get-or-create singleton at `DAT_143a13b08`
  with the +0x3cc status field; only the status transition differs (1 vs 2),
  class unproven.
* `0x140216f00` — sorts fleet by stat +0x15d0 into +0xf8; +0x15d0 unknown.
* `0x14023xxx`/`0x14024xxx`/`0x14025xxx` — remaining mid-size game passes not
  read (see large-bodies table).
* `rep_*` (~120 in range) — ICF duplicate bodies of already-named functions;
  intentionally not renamed.
