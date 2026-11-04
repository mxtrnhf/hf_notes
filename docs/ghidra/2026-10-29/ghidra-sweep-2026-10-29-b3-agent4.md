# Ghidra sweep 2026-10-29 — batch 3, agent 4 (app / frame / input / pre-combat / ship cards)

Range: `0x140170000–0x1401FFFFF`. Program `Highfleet.exe.unpacked.exe` v1.163
(`HighfleetServer`). Only `FUN_*` / `rep_*` functions were touched; every name
below was applied with `rename_function_by_address` and given a doc-style plate
comment (summary / `Algorithm:` / `Parameters:` / `Returns:`).

Batch 2 agent 4 already worked this range (input stack, ZIP layer, pre-combat
builders, title/landing/victory/dialog screens); those names were left alone.
**68 renames applied.**

One finding up front: after batch 2, `0x1401D0000–0x1401FFFFF` has **no unnamed
`FUN_*` left at all** (only `rep_*` ICF copies), so the screen builders the note
asked about (title, preselect, landing, victory, shop, quit menu) are done. The
remaining unnamed set in this range is container/CRT internals and the `rep_*`
duplicate bodies.

## Renames

### HGE / zlib / resource layer (0x140173000–0x140185000)

| addr | new name | description |
|---|---|---|
| 0x1401734a0 | `Math_FastInverseSqrt` | quake-style `1/sqrt` with the 0x5f3759df bit trick and one Newton step. |
| 0x140173e20 | `Resource_ParseNextToken` | HGE `.res` lexer: skips `;` comments, returns int/float/quoted string/keyword tokens; type at +0, text at +4, cursor at +0x88, line at +0x98. |
| 0x140174130 | `String_ParseHexUInt` | hex string -> uint, both cases folded, any non-digit clamps to 0xf. |
| 0x140178930 | `HashList_InsertNode` | head-inserts a node into one bucket of a chained hash list (next at +0x98). |
| 0x14017f370 | `Crc32_GetTable` | returns the address of the constant 256-entry CRC-32 table. |
| 0x14017f760 | `Inflate_BuildFixedTables` | builds the fixed Huffman literal/length + distance tables once (static flag, 0x50005..0x90009 base/extra pairs). |
| 0x140180fa0 | `Inflate_FreeState` | frees the inflater window (state+0x30) and state through the stream's free hook; returns -2 (Z_STREAM_ERROR) when incomplete. |
| 0x140181c00 | `Zip_OpenArchive` | scans backwards for `PK\x05\x06`, parses the end-of-central-directory (with the ZIP consistency checks, -0x67 on mismatch) and allocates the 0xe0-byte reader state. |
| 0x140183880 | `Input_JoystickVectorInsert` | inserts an 0xf0-byte joystick record at a position, growing the vector. |
| 0x140184420 | `LinkVector_InsertAt` | inserts a freshly constructed Link into the 0xf0-stride vector. |
| 0x140184640 | `RbTree_FreeAllNodes` | recursive node free, payload untouched. |
| 0x140184750 | `RbTree_FreeLinkNodes` | recursive node free with `freeLinkMemory_` on the payload. |
| 0x140184e10 | `Link_InitDefault` | Link constructor: `LinkVFTABLE`, empty name/list, id, HGE time, 26-char name cap. |
| 0x1401855e0 | `Array_DestroyRange32Ptr` | frees the +8 pointer of every 0x20-byte element of a range. |
| 0x140185680 | `List_FreeChain` | frees a singly linked list of 0x10-byte nodes. |
| 0x1401856f0 | `RbTree_DestroyHeaderTree` | destroys a tree that owns only its nodes (header node last). |
| 0x1401858f0 | `Link_Destructor` | Link destructor body: node list at +0x98, name std::string, embedded Link at +0x18. |
| 0x140187760 | `VectorLink_Reset` | destroys and re-seats a vector of 0xf0-byte Links. |

### Allocators, maps, serializers (0x140188000–0x140192000)

| addr | new name | description |
|---|---|---|
| 0x140188040 | `AllocArrayStride8` | 8-byte element array, 32-byte alignment for blocks >= 0x1000. |
| 0x1401884d0 | `Array_FreeStride32` | frees a 0x20-stride array (over-aligned raw pointer recovery). |
| 0x140188520 | `Array_FreeStride240` | same for 0xf0-stride arrays. |
| 0x140188ab0 | `Bindings_LookupUpperBound` | `std::map::upper_bound` on key +0x1c of the binding tree at +0x48, returns the value at +0x20, -1 when absent. |
| 0x140190b50 | `Serialize_WriteInt64Field` | writes `<name>@<value>\n` for a 64-bit field (name at +8, value at +0x30, cache at +0x38). |
| 0x140190bb0 | `Serialize_WriteInt32Field` | same for a 32-bit field. |
| 0x1401911e0 | `Serialize_WriteUInt64Field` | same for an unsigned 64-bit field. |
| 0x140191620 | `HashMap_EraseRange` | erases a range of string-keyed nodes, hashing with FNV-1a and indexing with the mask at map+0x30. |
| 0x140191f10 | `HashMap_Clear` | empties a chained hash map without freeing the bucket table. |

### Input / bindings / hovered-element helpers (0x140188700–0x14018e000)

| addr | new name | description |
|---|---|---|
| 0x1401887c0 | `Input_MapHatToKeyModern` | hat -> virtual-key permutation for pad type +0xe8 == 1 (PS5 / Xbox Series X / names containing "PS"). |
| 0x140188860 | `Input_MapHatToKeyLegacy` | hat -> virtual-key permutation for pad type +0xe8 == 0. |
| 0x140188940 | `Input_FindJoystickByPlayerIndex` | linear scan of the pad vector by player index at +0xe4. |
| 0x140188a00 | `Input_FindJoystickIndex` | same scan returning the element index or -1. |
| 0x140188b00 | `Gui_GetHoveredElementPosition` | copies the hovered element's +0x128 position. |
| 0x140188b50 | `Gui_GetHoveredElementScreenPos` | hovered element position through `get_screen_pos`. |
| 0x140188bb0 | `Gui_GetHoveredNodeScreenPos` | hovered element position through `Node_GetScreenPosition`. |
| 0x140188c00 | `Link_InitBaseFields` | common Link base init: name "Undef.", id, HGE time, default colour/scale/flags. |
| 0x1401891c0 | `Input_IsMoveDownHeld` | per-player flag +0xe0 (+1 on y in `Input_RebuildMoveVector`). |
| 0x140189200 | `Input_IsMoveLeftHeld` | per-player flag +0xdf (-1 on x). |
| 0x140189240 | `Input_IsMoveRightHeld` | per-player flag +0xe1 (+1 on x). |
| 0x140189280 | `Input_IsMoveUpHeld` | per-player flag +0xde (-1 on y). |
| 0x1401892c0 | `Input_IsRotateLeftFlagHeld` | per-player rotation flag +0xe2. |
| 0x140189300 | `Input_IsRotateRightFlagHeld` | per-player rotation flag +0xe3. |
| 0x140189340 | `Gui_ClampHoveredElementToScreen` | clamps the hovered element's position to +-half frame, then `setXposYpos`. |
| 0x1401893e0 | `Input_DispatchPadDirectionKey` | hat value -> virtual-key press (0x1004..0x1017), plus the hat 0xf back/escape chain (load/save/quit/retry/landmode). |
| 0x140189620 | `Input_DispatchPadDirectionKeyUp` | release counterpart of the above. |
| 0x14018dbd0 | `Gui_SetHoveredElementPosition` | moves the hovered element and its Box2D body (element+0x178) with the 0.05 world scale. |

### Ship links / parts / battle bookkeeping (0x140193000–0x1401BE200)

| addr | new name | description |
|---|---|---|
| 0x140193160 | `Part_Turret_DeserializeFields` | virtual deserializer of the turret/gun-mount fields (`m_stat`, `m_master_id`, `m_A_id`, `m_B_id`, `m_shiftAx/Ay/Bx/By`, `m_type`, `m_render_type`, `m_length(_max/_min)`, `m_angle_enable/_reference/_min/_max`, `m_motor_enable/_torque/_speed`, `m_cw`); unknown keys go to the ISerializable base. |
| 0x140194220 | `ShipLink_DrawTetherLine` | draws the world-space line between the two bodies of a link (anchors via vtable +0xe8, `ShipLink_Zoom` then `Gfx_DrawWorldLine`). |
| 0x140194ae0 | `ShipLink_StopJointMotor` | stops the revolute-joint motor when the link is in state 1. |
| 0x140194b10 | `ShipLink_EnsureJoint` | recreates the Box2D joint when the cached body pointers no longer match the linked bodies. |
| 0x1401b4490 | `Gui_ApplyLensDistortion` | the CRT barrel distortion of a screen point (normalise, y^2/9 term, floor). |
| 0x1401b5420 | `Ballistics_PredictHit` | simulates a shell for up to 10 s (gravity 9.82, drag 0.05) against nearby creatures and returns hit flag + closest miss distance. |
| 0x1401b6e00 | `Gun_SwapAmmoCounters` | rotates the four ammo counters (+0x850..+0x85c) of every gun in both escadra lists, folding the fractional reserve at +0x860 into the new total. |
| 0x1401bc280 | `Arcade_ClearCreatureSlots` | zeroes the arcade creature slot array up to 0x143a1c260. |
| 0x1401bc6b0 | `Battle_ApplySurvivorState` | applies the post-battle state of each ship still in `PRESELECT_DECK`: copies damage properties, removes the entry from the damage list, recalculates stats/fuel, repair timer 10.0, re-adds to the escadra, then clears the preselect GUI names and level bounds. |
| 0x1401bcab0 | `ShipLink_SnapBodyToAnchor` | snaps the second body of a link onto the first body's anchor/angle and recurses into its child links. |
| 0x1401bccb0 | `ShipLink_SnapAllBodies` | snaps every attached body of a creature (or of its children) with weight 1.0 (1.2 for hulls > 1.5e7) and sets the rebuild flag +0xb48. |
| 0x1401bdc20 | `Battle_ChooseDeployShip` | picks the next ship to deploy: builds the unavailable list, sorts by +0xf8, filters by repair/state thresholds and returns a Link copy (or an empty link). |
| 0x1401be100 | `Creature_FlattenTreeIntoVector` | flattens a creature tree into a vector of (creature, counts) 0x10-byte records. |

### Pre-combat text rows (0x1401C0BE0)

| addr | new name | description |
|---|---|---|
| 0x1401c0be0 | `Precombat_BuildStatRows` | creates one GUI text element per (label, value) pair through the text factory 0x1400671d0; called at the end of `Precombat_BuildCardLayout` and `Precombat_BuildMapLayout` and by `buildPrecombatScreen`, i.e. the stat/name rows on the ship cards. |

### Sort / container algorithm cores (0x14019C000–0x1401A0000)

| addr | new name | description |
|---|---|---|
| 0x14019c6d0 | `Sort3ByValue3D8` | three-element sort by the double at object+0x3d8. |
| 0x14019c740 | `Sort3ByMemcmp` | three-element sort through the memcmp functor in the 4th argument. |
| 0x14019c7d0 | `Sort3ByStats` | three-element sort by `GetStats`. |
| 0x14019c890 | `Sort3_DescendingMemcmp` | three-element sort, memcmp operands swapped (descending). Name kept with an underscore because the token-subset rule rejects `Sort3ByMemcmp*`. |
| 0x14019d1c0 | `Sort_IntrosortFloat` | introsort core for a float range (median-of-three, Hoare partition, smaller-half recursion). |
| 0x14019d4a0 | `Sort_IntrosortByValue3D8` | introsort core ordering by object+0x3d8. |
| 0x14019e530 | `Sort_IntrosortByStats` | introsort core ordering by `GetStats`. |
| 0x14019f710 | `Sort_HeapSiftByValue3D8` | heapsort sift-down by object+0x3d8. |
| 0x14019fbd0 | `Sort_HeapSiftByStats` | heapsort sift-down by `GetStats`. |

## Notes for the docs

* **Per-player input record** (stride 0xf0 in the global vector
  `DAT_1439e9388..DAT_1439e9390`): player index `+0xe4`, pad type `+0xe8`,
  six held flags `+0xde..+0xe3`. `+0xde` up, `+0xdf` left, `+0xe0` down,
  `+0xe1` right, `+0xe2`/`+0xe3` rotation. `Input_RebuildMoveVector`
  (0x14018d6c0) turns the four move flags into the move vector at `+0x10`;
  `Player_SendThrustCommands` (0x1402a9300) reads the two rotation flags.
  Which of `+0xe2`/`+0xe3` is Q and which is E is still open.
* **Hat mapping**: `Input_HandleJoystickEvent` (0x14018ac30) looks at the SDL
  hat event, picks `Input_MapHatToKeyModern` for pad type 1 (PS5, Xbox Series X,
  any name containing "PS") or `Input_MapHatToKeyLegacy` for 0, then feeds the
  result to `Input_DispatchPadDirectionKey` / `...Up`. Both maps are plain
  16-entry permutations; hat value 0xf inside the dispatcher is the "back"
  action that runs the whole ESC/dialog chain.
* **Ship cards**: the per-card stat rows come from `Precombat_BuildStatRows`,
  not from the card builder itself — useful if a mod wants to add its own row:
  the function just iterates (label, value) pairs and calls the generic text
  factory, so a new pair plugs in at the same place.
* **ZIP layer**: `Zip_OpenArchive` completes the picture batch 2 started with
  `Zip_ReadLocalFileHeader` / `Zip_ReadInt32BE` / `Zlib_Adler32`; the inflater
  half is `Inflate_BuildFixedTables` + `Inflate_FreeState`.

## Skipped / open

| addr | what it does / why skipped |
|---|---|
| 0x140170140, 0x140170190, 0x1401787a0, 0x1401787f0, 0x140178840, 0x140178890, 0x1401788e0 | seven identical scalar-deleting destructors that all set the same vtable `PTR_FUN_140366650` (ICF clones of resource subclasses). A per-address class name would be a guess. |
| 0x140178a60, 0x140178b10, 0x140178bc0, 0x140178c70, 0x140178d20, 0x140178ff0, 0x140179100, 0x1401791e0, 0x140179380, 0x140179410, 0x140179460 | one family of lazy resource-proxy getters (file name at proxy+0xa0, handle cached at +0x90, HGE vtable slot called on miss: +0x90, +0x98, +0x138, +0x140, +0x160, +0x168, +0x1c0, +0x1c8, +0x300, +0x310). `HGEVFTABLE` is BSS-initialised (only `CreateHGE` references it), so the slot -> resource-type map (texture / effect / font / target / stream) cannot be read statically. Whoever dumps the vtable can name them `Media_EnsureTexture` etc. in a minute. |
| 0x1401783c0 | 0x98-byte struct copy (compiler generated). |
| 0x140187c00, 0x140187ca0, 0x140187e40, 0x140187f60, 0x140187fd0, 0x140188740, 0x14019abe0, 0x14019ae0f/66/94, 0x1401a0740/07f0/0930/1090/15a0, 0x1401a2140/21c0/2240/2aa0/2e50/2f60, 0x1401a3bc0/3e50/4210/47c0/47f0, 0x1401a4a60..0x1401a5f10, 0x1401a6250/6400/6530, 0x1401a82c0..0x1401a8510, 0x1401ae260..0x1401af7b0 | `std::vector` / `std::map` / sort-internals and range destroy/relocate copies for the 0x18/0x20/0x28/0x38/0xf0/0x188/0x398-byte element types, plus scalar-deleting destructors of small property classes with unresolved vtables. Compiler output, not game logic. |
| 0x140193090 | clamps a float at +0xd8 between +0xdc/+0xe0 and pushes it into a Box2D joint (type 3 -> +0xa4, type 10 -> +0x90, scaled by 0.05). Could be motor speed or arm length; not resolved, so left alone. |
| 0x1401941f0 | refresh of the object at +0x58 through `rep_14025ecf0`; the callee's role was not read. |
| 0x1401a0560, 0x1401a0610, 0x1401a07f0 | divide-and-conquer max/min element over `GetStats` / float fields; the exact `std::` algorithm (max_element vs minmax) is not certain. |
| 0x1401a7120 | 0x920-byte alloca-heavy builder: takes a rect and five grid coordinates, builds a vector of strings/cells and a 1248-dword scratch array. Called only by 0x1401c2ba0. Not identified. |
| 0x1401c2ba0 | 11-way switch over shape ids 1..0xb feeding 0x1401a7120 with atlas coordinates (0x19/0x32/0x4b/0x50/0x78/0x96/0xe1); its only caller is `Scene_ResetGlobalLinks`. Looks like a background/decal grid seed when a scene resets, but "hull plating" would fit the coordinates equally well - left open. |
| 0x1401c7270 | 9.7 KB particle spawner (`Media/Prt/sparcles.psi`, `debris.psi`), called from `World_ThermalPass`. Still unresolved from batch 2: identity depends on the caller. Decompiled size exceeds the batch limit, `disassemble_function` only confirms the particle strings. |
| `rep_*` (≈330 left in range) | ICF duplicate bodies of already named functions (`rep_14018b530_InputTask`, `rep_*_GetStats`, `rep_*_SetBackground?`, `rep_*_compData`, ...). Left as-is on purpose so the originals stay distinguishable. |
