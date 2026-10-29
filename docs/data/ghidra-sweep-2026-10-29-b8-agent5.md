# Ghidra sweep, batch 8 agent 5 — `rep_*` re-match in `0x140100000–0x1401FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` function whose entry point is in `0x140100000–0x1401FFFFF`
(batch-7 agent 3's range, second pass / Q2). Start count: **382** `rep_*`
(the blackboard's estimate; 0x14016cd50 `Texture_Load` and everything batch 7
named are already out).

| | count |
|---|---|
| `rep_*` in scope at start | 382 |
| **renamed + plated** | **54** |
| stale label (recorded, not renamed) | 325 |
| unreadable body | 1 (`0x1401a4da0`, unchanged) |
| rows appended to `q2.tsv` | 380 (54 + 325 + 1) |

Two functions in the 382 were renamed by another agent during this pass and are
**not** claimed here: `0x14012c280` (`Gui_CopyConstructor`) and `0x1401c7060`
(`Fleet_CreateEscadraFromShips`). Their rows are left to their owner, so 380 rows
are appended (946 -> 1326 rows).

No `save_program`, no tags, no README/STATUS edits, no commits. Every rename has
a plate (summary / `Algorithm:` / `Parameters:` / `Returns:`).
Audit TSV: `docs/data/rep-audit-2026-10-29-q2.tsv` — appended only.

## Method

1. **Listing + hash.** Scripted list of all 382: entry, old label, body size,
   instruction count, caller count, SHA-1 over the body address set (381
   hashable; `0x1401a4da0` still raises `MemoryAccessException` on its
   uninitialised/overlapping bytes).
2. **Body feature dump.** For every function: callees, referenced string
   literals, referenced named globals, and in-range pointer constants. This is
   what the batch-7 pass could not use from labels alone: it exposes the unique
   GUI keys, HGE media names, container literals (`list too long`,
   `unordered_map/set too long`, `invalid hash bucket count`), the minizip/zlib
   constants and the FNV-1a hash constants.
3. **Targeted decompilation** in batches of <=10 (about 100 bodies total, all
   <=0x2000 B; nothing larger was decompiled). Every rename below was read.
4. **Re-match of prior verdicts.** All 380 rows are appends. A stale row keeps
   the verdict but sharpens column 4 with the concrete callee/string evidence
   found this pass and column 5 with the fresh hash plus the resolved embedded
   target of the old label.

## Renames (54)

| addr | old label | new name |
|---|---|---|
| 0x14011ae30 | `rep_140114f60_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `Squadron_UpdateFuelAndAmmo` |
| 0x14011be00 | `rep_140115f10_PlayRadioSound?` | `Frame_DrawRuptureSprites` |
| 0x14012eeb0 | `rep_140125f70_VCRUNTIME140.DLL::memcmp` | `Gui_SetupSpecialElement` |
| 0x14015d000 | `rep_140151b10_SetBackground?` | `Map_BuildCloudDecor` |
| 0x140161660 | `rep_140156230_CopyString` | `Panel_InitDefaults` |
| 0x1401616e0 | `rep_1401562b0_Property::Property` | `Replica_InitDefaults` |
| 0x140161a10 | `rep_1401565e0_CopyString` | `Slider_InitDefaults` |
| 0x14016e280 | `rep_140162790_New` | `Font_LoadFromFile` |
| 0x140170e30 | `rep__FileSearch_140165340_KERNEL32.DLL::FindClose` | `Texture_LoadAllFromFolder` |
| 0x140172f90 | `rep_1401674a0_API-MS-WIN-CRT-HEAP-L1-1-0.DLL::free` | `StringTable_LoadFromFile` |
| 0x140173910 | `rep_140167e20_USER32.DLL::GetKeyboardState` | `Input_PushEvent` |
| 0x1401794b0 | `rep_14016d8c0_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::atof` | `TextGrid_ParseResourceBlock` |
| 0x140179a80 | `rep_14016de90_API-MS-WIN-CRT-CONVERT-L1-1-0.DLL::atof` | `URFont_ParseResourceBlock` |
| 0x140182250 | `rep_140176640_FastFail?` | `Zip_OpenCurrentFile` |
| 0x1401834a0 | `rep_140177a20_New` | `LinkedList_PushBack` |
| 0x14018d760 | `rep_140180000_WriteToClientLog` | `HIDS_SetActive` |
| 0x14018e9c0 | `rep_140180e90_API-MS-WIN-CRT-MATH-L1-1-0.DLL::ceilf` | `HashMap_InsertStringKey` |
| 0x140193970 | `rep_140185d30_New` | `Joint_QueueDead` |
| 0x140194a50 | `rep_140186d90_New` | `Joint_SetDeadFlagAndQueue` |
| 0x140195460 | `rep_1401877a0_WriteToClientLog` | `Crash_LogExceptionRecord` |
| 0x140195950 | `rep_140187c90_...::~basic_istream<...>` | `Strings_LoadFromFile` |
| 0x1401a26f0 | `rep_140193db0_API-MS-WIN-CRT-MATH-L1-1-0.DLL::ceilf` | `HashMap_FindU64Key` |
| 0x1401a6ea0 | `rep_140197c20_FastFail?` | `Log_CheckError` |
| 0x1401a6f90 | `rep_140198400_FastFail?` | `Node_RenameAndRefreshProperties` |
| 0x1401aedd0 | `rep_14019f2b0_MSVCP140.DLL::std::_Xlength_error` | `HashMap_RehashBuckets` |
| 0x1401af770 | `rep_14019f9c0_MSVCP140.DLL::std::_Xout_of_range` | `Vector_ThrowIndexOutOfRange` |
| 0x1401b0a50 | `rep_1401a0b20_MakeGlobal?` | `Gui_ShowCinematicDialogue` |
| 0x1401b11f0 | `rep_1401a12c0_VCRUNTIME140.DLL::memcmp` | `MapDecal_Constructor` |
| 0x1401b15f0 | `rep_1401a16c0_PlayRadioSound?` | `Gui_DrawDialogHandLine` |
| 0x1401b20f0 | `rep_1401a21c0_FastFail?` | `String_AppendEngSuffix` |
| 0x1401b24b0 | `rep_1401a2580_rightPadInteger` | `Gui_UpdateRamMoral` |
| 0x1401b47c0 | `rep_1401a47e0_FastFail?` | `Game_GetVersionBanner` |
| 0x1401b5ab0 | `rep_1401a59f0_rightPadInteger` | `Creature_SpawnPlaceholder` |
| 0x1401b9df0 | `rep_1401a9d80_LoadParticle?` | `Body_SpawnBurningParticles` |
| 0x1401bad60 | `rep_1401aacf0_VCRUNTIME140.DLL::memcmp` | `Radio_UpdateBandIndicators` |
| 0x1401bb920 | `rep_1401ab8b0_rightPadInteger` | `Gui_ShowSellPrizeDialog` |
| 0x1401bc160 | `rep_1401ac0e0_PlayRadioSound?` | `PlayCheerSound` |
| 0x1401bc600 | `rep_1401ac620_MakeGlobal?` | `Gui_ResetButtonDefaults` |
| 0x1401bce10 | `rep_1401aca30_PlayRadioSound?` | `Scavenge_BuildDirectionLabel` |
| 0x1401c05a0 | `rep_1401b0160_CopyString` | `Roster_CopyIntoVolume` |
| 0x1401c08e0 | `rep_1401b04a0_SetBackground?` | `Map_BuildMarkerDividerPair` |
| 0x1401c28a0 | `rep_1401b0960_SetBackground?` | `Map_BuildMarkerRulerPair` |
| 0x1401c4840 | `rep_1401b25d0_New` | `Gui_BuildBayonetsPanel` |
| 0x1401c4ad0 | `rep_1401b2860_PlayRadioSound?` | `Gui_BuildBayonetRow` |
| 0x1401c5b40 | `rep_1401b2f60_SetBackground?` | `Gui_ShowCursorTooltip` |
| 0x1401c5f20 | `rep_1401b34c0_SetBackground?` | `Body_SetBalloonAppearance` |
| 0x1401ca120 | `rep_1401b50b0_New` | `Gui_CreateBlackOverlay` |
| 0x1401cf1c0 | `rep_1401ba130_FastFail?` | `Dialog_BuildAttitudeList` |
| 0x1401d10c0 | `rep_1401bc030_CopyEscadraName` | `Gui_SpawnBigTextLabel` |
| 0x1401d13d0 | `rep_1401bc340_FastFail?` | `Sprite_SetupHoverVariant` |
| 0x1401ebae0 | `rep_1401d2b90_SetBackground?` | `Gui_BuildPressMousePrompt` |
| 0x1401f1fa0 | `rep_1401d9900_SetBackground?` | `Gui_BuildRamIndicators` |
| 0x1401fefb0 | `rep_1401e4b10_CopyEscadraName` | `Gui_ShowHelpIcon` |
| 0x1401ff260 | `rep_1401e4dc0_PlayRadioSound?` | `FX_SpawnCloudPuff` |

### Proof classes

* **HGE media / I/O loaders** (7): `Font_LoadFromFile` parses `[HGEFONT]`
  `Bitmap`/`Char` lines into a 256-entry glyph table (`+8` pointers, `+0x808`
  x/y, `+0xc08` advance); `StringTable_LoadFromFile` parses
  `[HGESTRINGTABLE]` `name = "value"` into 0x50-byte nodes (value `+0x40`,
  next `+0x48`); `Texture_LoadAllFromFolder` globs `%s/*.png` and allocates
  `PTR_Texture_ScalarDeletingDtor` wrappers; `Strings_LoadFromFile` reads
  `strings.txt` lines into the global array `0x1439ef360` (stride 0x20);
  `Zip_OpenCurrentFile` is minizip `unzOpenCurrentFile` (0xe0 state + 0x8000
  buffer + zlib `1.2.1` + PKZIP key header decrypt); `TextGrid_ParseResourceBlock`
  / `URFont_ParseResourceBlock` build the 0x158/0x148-byte `ResDesc`
  (vtables `0x140366d00` / `0x140366cc0`).
* **GUI screen/widget builders** (17): proved by their unique key set plus the
  `GUI::GUI_2` + `SetBackground_`/`resetGuiStrings`/`SetLink` builder pattern
  (same method as batch-7 agent 3): `GUI_PRESS_BLACK|GUI_PRESS_TXT|PRESS`,
  `RAM_MORAL|RAM_ATTITUDE|RAM_REPUTATION`, `MAPMARK_DEVIDER1/2`,
  `MAPMARK_RULER1/2`, `CURSOR_TEXT|cursor`, `BAYONETS|rifle`, `HLP_ICON`,
  `BLACK`, `ATTITUDE_STATS`, `SCAVENGE_TARKHAN_*`, `HIGHFLEET v.`.
* **Second-stage constructors** (3): `Panel_InitDefaults`, `Replica_InitDefaults`,
  `Slider_InitDefaults` are the bodies called by the batch-7 `*_Constructor`
  wrappers; each writes the class name at `+8`, the class word at `+0x28`, the
  theme strings, and calls vtable slot `0x38`.
* **Container internals** (5): FNV-1a constants `0xcbf29ce484222325` /
  `0x100000001b3` (unordered_map/set), `list too long` splice (std::list),
  `invalid vector subscript` (std::vector::_Xout_of_range replica).
* **Game logic** (22): HIDS per-player activation, MapDecal constructor,
  scavenge direction label, cinematic dialogue, sell-prize dialog, cheer sound,
  bayonet row, rupture sprites, cloud puff, creature placeholder spawn, burning
  particles, radio band update, `DeadJointList` queueing, RAM morale readout,
  crash-dump logger, input event builder.

## Structural findings (for `structures.md`)

* **HGE font object**: glyph pointer table starts at `+8` (index 0..255),
  per-glyph x at `+0x808+n*4`, y at `+0xc08+n*4`; the running maximum glyph Y is
  kept at `+0x1008`; global HGE handle `DAT_1439e8230`. String-table nodes are
  0x50 bytes (`name` at 0, `value` at `+0x40`, `next` at `+0x48`), global HGE
  `DAT_1439e8678`.
* **`strings.txt` array**: 0x20-stride global `std::string` array at
  `0x1439ef360`, filled in file order.
* **`ResDesc` parse-list heads** on the resource parser: `+0x30`, `+0x58`
  (URFont), `+0x60`, `+0x68` (TextGrid). Confirms batch-7 agent 8's per-type
  vtable map and adds that each parser de-duplicates by name and head-inserts.
* **unordered_map layout**: element count `+0x10`, bucket vector `+0x18`
  (2 pointers per bucket), mask `+0x30`, bucket count `+0x38`; nodes are
  0x50 bytes (next `+0`, prev `+8`, `std::string` key `+0x10` with length
  `+0x20` and capacity `+0x28`); keys hashed with FNV-1a.
* **std::list node** for the intrusive lists here: 0x18 bytes
  (`owner +0`, `next +8`, `value +0x10`), sentinel-based, count at owner `+8`,
  max `0x0aaaaaaaaaaaaaaa`.
* **Joint**: `+0x48` dead flag, `+0x58` auxiliary buffer; `DeadJointList`
  (`0x1439ef238`) + `DeadJointCount` (`0x1439ef240`) hold queued dead joints.
* **GUI text-label recipe**: `{align=2}{font=pollock_80}` prefix; big labels use
  depth `0xce4`/`0xd48`, z-order `0x3e`/`0x3d`, `Gui_DrawScaledShape`.
* **Button table**: 11 entries, 0x18 stride, from `DAT_143a15a70` to
  `DAT_143a15ad0`; reset re-presses each with `switch_01`.
* **`HIDS`**: per-player byte at `+0xa8`/`+0xa9`, active flag `+0x60`, ship
  name string at `+0x38`.

## Stale labels left in range (325)

Grouped for the next pass (the appended rows carry the per-function detail):

* **std::list "list too long" helpers, ~25**: identical splice shape with the
  literal `list too long`; they differ only in node/value type. Need caller
  type inference to split; not renamed.
* **std::unordered_map/set "unordered_map/set too long" emplace variants, 6**:
  `0x14018ecd0`, `0x14018efa0`, `0x1401a1c00`, `0x1401a1e90` plus two;
  same FNV-1a template, only the value type differs.
* **ResDesc block parsers, 6**: `0x140179fb0`, `0x14017a2e0`, `0x14017afe0`,
  `0x14017b380` (vtables `0x1403666d0`, `0x140366ce0`, `0x140366c60`,
  `0x140366690`), plus the helpers `0x14017b6b0` ("Unsupported value"),
  `0x14017b780` (indexed variant) and `0x14017ba40` (token skipper). The four
  vtable classes are still unidentified, so no name.
* **Seven `ResDesc` field-copy bodies** `0x140174cd0..0x140177d10`
  (`rep_wrap_0_FUN_14016c7d0`): each calls `FUN_1401783c0` then copies
  descriptor fields `+0xa0..`; one per resource type, type not proved.
* **VMark/VMissile/VExplosion slot-44 and other >0x2000 bodies** were not
  decompiled (rule 6): e.g. `0x140116040` (4363 B), `0x14015a600` (7035 B),
  `0x14018b530` (3563 B), `0x1401c9840` (2263 B).
* **`0x1401a4da0`** remains unreadable (183 B over uninitialised/overlapping
  bytes; `MemoryAccessException` on `EXTERNAL:00000078`).
* **`0x140104df0`** now has a sharper reading: it calls
  `displayClockRadioFreqLables?`, `showCertainLables?`,
  `displayAircraftStrategicMap`, `LoadNameIntoMedia` and uses the fonts
  `vcr_21`/`dinpro_30_reg` — a strategic-map label drawer, but the owning
  screen is not proved.

## Hand-off

* 54 address-keyed renames with plates; old labels preserved in column 2 of the
  appended `q2.tsv` rows.
* Cheap next wins: identify the four unnamed `ResDesc` vtable classes (then the
  6 parsers + 7 copy bodies can all be named), and split the std::list cluster
  by caller value type.
* `0x1401bbeb0` (creature attach + `TUTORIAL` trigger check) and
  `0x140104df0` (strategic-map labels) are the closest remaining game-logic
  candidates; both need one more caller read.
