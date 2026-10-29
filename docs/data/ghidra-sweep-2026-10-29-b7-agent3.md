# Ghidra sweep, batch 7 agent 3 — `rep_*` re-match in `0x140100000–0x1401FFFFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` function with entry point in `0x140100000–0x1401FFFFF`.
Start count: **448** `rep_*` (batch 6 recorded 449 at its end; 0x14016cd50
`Texture_Load` is already named now, so the live set is 448). End: **383**
`rep_*`.

| | count |
|---|---|
| `rep_*` in scope | 448 |
| **renamed + plated** | **65** |
| stale label (partial identity recorded, not renamed) | 382 |
| unreadable body | 1 (`0x1401a4da0`, unchanged) |
| functions created | 0 |

No `save_program`, no tags, no README/STATUS edits, no commits. Every rename
carries a plate (summary / `Algorithm:` / `Parameters:` / `Returns:`).
Audit TSV: `docs/data/rep-audit-2026-10-29-q2.tsv` — 448 rows **appended**
(946 rows total; the 498 batch-6 rows are untouched).

## Method

1. **Listing + hash.** Scripted list of all 448: entry, old label, body size,
   SHA-1 over the body address set, caller count. 447 hashable, 1 unreadable
   (same body as batch 6). No body is byte-identical to another function.
2. **Body feature dump.** For every function: instruction count, callees,
   referenced string literals, referenced data/named globals. This turned up
   direct evidence classes that the batch-6 label-only pass could not use:
   vtable-install bodies (`PTR_<Class>_ScalarDeletingDestructor_*`,
   `<Class>VFTABLE`, `LinkVFTABLE`), `Property::Property` + `AddProperty`
   blocks, and families of small virtuals with one role.
3. **Targeted decompilation** (batches of ≤10) of every candidate rename and of
   the remaining vtable-slot functions, ~90 bodies in total. No bulk
   decompilation; bodies >0x2000 B were skipped (noted below).
4. **Re-match of the prior verdicts.** All 448 addresses were already in the
   batch-6 TSV as stale. Rows are appended only; the new row says what the
   second pass added (body proof for renames, re-confirmed hash for the rest).

## Renames (65)

### Constructors proved by vtable install + class-name string (17)

| addr | new name | proof |
|---|---|---|
| 0x14012abf0 | `GuiBinding_Constructor` | installs GuiBinding vtable, `"GuiBinding"`, stores binding id and appends widget to +0xe70 |
| 0x14012aca0 | `Gui_Constructor` | installs Gui vtable, stores w/h, allocates cols*rows cell array at +0xe78 |
| 0x14012af00 | `List_ConstructorFromPrototype` | installs List vtable + `LinkVFTABLE`, `"List"`, copies prototype fields |
| 0x14012b000 | `List_Constructor` | same vtable, no source object |
| 0x14012b280 | `Replica_ConstructorFromPrototype` | Replica vtable + `Property::Property`, copies +0xe70..+0xec0 |
| 0x14012b380 | `Replica_Constructor` | Replica vtable + `Property::Property` only |
| 0x14012b3d0 | `Slider_ConstructorFromPrototype` | Slider vtable, label string +0xe78, copies prototype |
| 0x14012b4a0 | `Slider_Constructor` | Slider vtable, empty label |
| 0x14011bce0 | `Frame_Constructor` | `Body::Body_Constructor(1)`, Frame vtable, `"Frame"`, type 0x1f |
| 0x14011bc30 | `Frame_CopyConstructor` | same then `copyOverBody` + relink children via +0x220 |
| 0x140194c20 | `SLink_Constructor` | SLink vtable, `"SLink"`, `CODE_SLINK`, attaches to Node |
| 0x140192db0 | `Joint_Constructor` | Joint vtable 0x140368ba8 + 4 `LinkVFTABLE`s, `MakeGlobal_` |
| 0x140192c10 | `Joint_ConstructorWithNodes` | Joint vtable, links two nodes, stores 6 scalars at +0xe4..+0x110 |
| 0x140192a40 | `Joint_CopyConstructor` | Joint vtable, copies source links/fields |
| 0x14012b7a0 | `Gui_Destructor` | Gui vtable, deletes children via slot 0, `Body_Destructor` |
| 0x14012bfc0 | `GuiMapSky_Destructor` | GuiMapSky vtable, frees cell grid, Gui base dtor |
| 0x14011f010 | `FX_Destructor` | FX vtable, unregisters from global FX lists, `ISerializable_Destructor` |

### Destructor / deleting-destructor proof (2)

| addr | new name | proof |
|---|---|---|
| 0x1401a5fc0 | `NPC_Destructor` | NPC vtable, frees 4 std::strings at +0x70/+0x90/+0xb0/+0xd0 |
| 0x14011bd40 | `Frame_ScalarDeletingDestructor` | VFrame slot 0: vtable install, `Body_Destructor`, `if (param_2 & 1) free(this)` |

### VFrame / VSLink / VJoint virtuals (6)

| addr | new name | proof |
|---|---|---|
| 0x14011cbc0 | `Frame_Reflect` | slot 18: checks m_master/m_b2b, logs `ERR: Frame::reflect failed`, calls `Node::Node_Reflect` |
| 0x14011cc60 | `Frame_RemoveBody` | slot 12: `Body::remove`, frees body, notifies +0x1f8, logs `Frame::remove failed` |
| 0x14011c690 | `Frame_BreakingRemove` | logs `Frame::breaking_remove failed`, re-registers bodies via 0x1402b1650 |
| 0x140194f70 | `SLink_SetClassInfo` | slot 7: writes `"SLink"` and class word 0x100000003 |
| 0x140194040 | `Joint_SetClassInfo` | slot 7: writes `"Joint"` and class word 0x200000003 |
| 0x140194080 | `Joint_Relink` | re-resolves m_master/m_A/m_B, relinks +0x80 rings, logs `ERR: Joint::... relink` |

### Per-class `AddProperty` slot 7 and ISerializable slot 5 (4)

| addr | new name | fields / behaviour |
|---|---|---|
| 0x140165a30 | `Gauge_AddProperty` | m_angle_min +0xe70, m_angle_max +0xe74, m_trem +0xe78 (f) |
| 0x140165cb0 | `Slider_AddProperty` | m_render_value b +0xe70, m_is_float b +0xe71, m_overmax f +0xe74, m_backname_bar s +0xe78, m_slider_index i +0xea0, m_slider_l f +0xea4 |
| 0x1401924e0 | `AADefence_AddProperty` | m_classname (SProperty), m_code (ui64Property) |
| 0x1401922b0 | `ISerializable_SetProperty` | shared slot 5: `"m_classname"` -> classname, `"m_code"` -> `_atoi64`; proves slot 5 is the base name/value setter, not an AddProperty |

### Gui hierarchy draws/loads (9)

| addr | new name | proof |
|---|---|---|
| 0x140166260 | `Gauge_Draw` | slot 71: needle-angle interpolation, calls base draw 0x14015af50 |
| 0x140167cc0 | `Slider_Draw` | slot 71: font/colour, `_gcvt` value, rotated label, base +0x350 |
| 0x140167310 | `Panel_Draw` | slot 71: caption build, rotated label, base +0x2d0/+0x350 |
| 0x140163500 | `Panel_Load` | slot 17: `CopyNameIntoMedia_(Media_res,m_backname)` -> +0xe90, `GUI::Load` |
| 0x140163580 | `Replica_Load` | slot 17: EscadraName -> vtable +0x368, `GUI::Load` |
| 0x140163000 | `ObjectList_BuyPart` | slot 111: `_BuyPartShop(...,+0xe90)`, refresh +0x370 |
| 0x14016c830 | `ObjectList_UpdateScrollRange` | slot 110: ceil items/visible, clamp +0x150/+0x151 |
| 0x14012dad0 | `Gui_DrawMiscLabelsIntelBadges` | slot 37: `miscLabelsIntelBadges`, `Frame_ResetCounter` |
| 0x14012db80 | `Gui_SetupPropsSecondaryMapModes` | slot 105: tail-calls `setupPropsSecondaryMapModes` |
| 0x1401636d0 | `Gui_LayoutText` | shared slot 91: converts UTF-8 to glyph records, kerning/tracking, stores width/height +0xd70/+0xd74 |

### HGE media wrappers — UR* 3-slot layout (8)

Each UR* media vtable has slot 1 = lazy create, slot 2 = release; proved by the
bodies, not by the names.

| addr | new name |
|---|---|
| 0x1401789a0 | `URAnimation_Release` |
| 0x140178ab0 | `URFont_Release` |
| 0x140178b60 | `URParticle_Release` |
| 0x140178c10 | `URSprite_Release` |
| 0x140178cc0 | `URStringTable_Release` |
| 0x140179160 | `URParticle_EnsureCreated` |
| 0x140179220 | `URSprite_EnsureCreated` |
| 0x1401793c0 | `URStringTable_EnsureCreated` |

### Other body-proved identities (8)

| addr | new name | proof |
|---|---|---|
| 0x14017db90 | `HGE_ShellExecute` | VHGE_Impl slot 6: `ShellExecuteA(pHGE+0x300,...,"open",3)`, success > 32 |
| 0x1401702b0 | `Media_GetOrCreateResource3` | `CopyNameIntoMedia_(media,3,name)` else alloc 0x120 ResDesc + `HashList_InsertNode(media,3,..)` |
| 0x14011a230 | `MapShipBody_ScanNearbyProfiles` | VMapShipBody slot 85: flags +0x910 when a live body is within 50 units |
| 0x1401b7970 | `GameOver_CheckFlagshipLost` | forms `FLAGSHIP_LOST_1`, plays `dram_hit_01`, checks `REACTOR_DESTROYED` -> `handlePreCampaignMenuLoadScore(1)` |
| 0x1401bc500 | `Gui_ApplyMissionShipMapMode` | `MAPMODE_MISSION_SHIP`, presses `button_03_on`, `addShipsToSilentStrikeGRP_` |
| 0x1401b10e0 | `Creature_AddCombridePart` | copies `MDL_COMBRIDGE_01`, names `"COMBRIDGE"`, recomputes stats |

### Gui screen builders proved by key set + builder callees (11)

All create `Gui` objects (`GUI::GUI_2`/`New`), call `resetGuiStrings`/
`SetBackground_`/`SetBackground?` and set the listed unique keys.

| addr | new name | unique keys |
|---|---|---|
| 0x1401fbcc0 | `Title_BuildMainMenu` | TITLE_CONTINUE/OPTIONS/CREDITS/SHIPWORK/EXIT |
| 0x1401e1140 | `Title_BuildLogoPanel` | LOGO_BACK/LOGO_R/LOGO_L, roll_* |
| 0x1401e52b0 | `Note_BuildPanel` | NOTE_PNL/NOTE_TEXT/NOTE_CLOSE |
| 0x1401e59c0 | `Note_BuildMiniPanel` | NOTE_MINI_PNL/NOTE_MINI_CLOSE |
| 0x1401e4a90 | `Moral_BuildStatsPanel` | MORAL_STATS/MORAL_NAME/MORALE_HELP |
| 0x1401c6a90 | `Dialog_BuildStatsPanel` | DIALOG_STATS + `displayTraitsByLevel` |
| 0x1401c62d0 | `Dialog_BuildBriefingPanel` | END_BRIEFING_LIST/DIALOG_PORTRAY |
| 0x1401c3de0 | `Dialog_BuildNpcStatusPanel` | NPC_STATUS/attitude_star/DIALOG_NAME |
| 0x1401f7ba0 | `Isaiah_BuildPanel` | ISAIAH/ISAIAH_BACK/SCRIPTURE |
| 0x1401da790 | `Hire_BuildFundsPanel` | HIRE_FUNDS/YOUR_FUNDS_LABLE (reads profile +0x2a8) |
| 0x1401b6570 | `Message_BuildAppPanel` | MES_APP |
| 0x1401d0e50 | `Gui_BuildBlueScreenOverlay` | GUI_BLUE/screen_blue/screen_scratches |

## Structural findings for `structures.md` / batch-7 doc

* **VJoint vtable is `0x140368ba8`** (`PTR_LAB_140368ba8` in Ghidra). Three
  constructors install it, and the `"Joint"` class-info virtual writes
  `0x200000003`. VSLink is `0x140368e18`, class word `0x100000003`.
* **VFrame** (`0x140360670`): slot 0 = scalar deleting destructor
  (0x14011bd40), slot 12 = remove-body, slot 18 = reflect. The vtable's slot 0
  function was still named `rep_...free`; it is now
  `Frame_ScalarDeletingDestructor`.
* **VGui slot 71 is the per-class Draw slot**: Gauge, Slider, Panel (and Gui at
  0x140166420) each override it, and every implementation ends by calling a
  Gui base draw (`+0x350`, or 0x14015af50 for Gauge). Slot 91 is shared by all
  widget vtables and is the text-layout routine (`Gui_LayoutText`). Slot 17 is
  per-class `Load` (Panel resolves a texture, Replica resolves an EscadraName).
* **`ISerializable` slot 5** is the base name/value setter
  (`ISerializable_SetProperty`): it understands only `m_classname` and `m_code`,
  so derived classes add their fields through slot 7 `AddProperty`, confirming
  batch 6's 8-slot model with a concrete slot-5 body.
* **UR* media classes are 3-slot tables**: slot 1 lazily constructs the
  underlying HGE object at `+0x90`, slot 2 destroys it and frees the buffer.
  This covers URAnimation, URFont, URParticle, URSprite, URStringTable.
* Gauge/Slider member offsets from the AddProperty plates: Gauge
  0xe70/0xe74/0xe78; Slider 0xe70..0xea4 (see table above).
* `Gui` layout extras seen repeatedly: child vector +0xe70..+0xe80, widget
  strings at +0x1b1 and +0x195, class buffer +0xd08, text width fields
  +0xd70/+0xd74, font name +0xd88, font colour +0xa8c.

## Stale labels left in range (382)

The appended rows keep the batch-6 identity text and add
`re-match b7: hash re-confirmed, still stale`. Specific partial identities added
this pass (not enough for a name):

* `0x14012ebe0` (VGui 101) copies string +0x14c -> +0x199, sets +0x193=1.
* `0x14012ec60` (VGui 102) calls 0x14014f300, clears string +0xcc8, sets +0xc98=0.
* `0x1401640a0` (VReplica 110) re-applies an EscadraName to a 4x4 TextGrid.
* `0x14016bd50` (VReplica 109) clears +0x1ae, calls +0x370 with +0x195, frees a
  by-value string argument.
* `0x14016b6c0` (VPanel 88) calls `copyVariousEscadraBulk`, sets +0xa39=1.
* `0x14016bd20` (VObjectList 108) `SetLink(+0x1ce,param)` then +0x370.
* `0x140185e60` resets the global link/RB-tree tables; embedded `MakeGlobal_`
  matches behaviourally but no class is attached.
* VMark/VMissile/VExplosion slot 44 (0x140119140 / 0x1401195d0 / 0x140116040)
  remain unread or over the 0x2000 limit.
* `0x1401a4da0` is still unreadable (183 B body over uninitialised/overlapping
  bytes); callers are the `std::basic_ios` dtor replicas.

## Hand-off

* The 65 renames are all address-keyed and can be cross-checked against the
  appended q2 rows; the old `rep_` label is preserved in column 2.
* The VJoint/VFrame/UR* slot maps above should go into `structures.md` with the
  batch-6 ISerializable/Property ABI (they complete it: slot 5 body, VFrame
  0/12/18, VGui 17/71/91).
* Remaining cheap wins for a later pass: the six VGui slots above (read but
  ambiguous), the three slot-44 bodies (need >0x2000 allowance), and the 100
  `rep_...free` CRT destructor-shaped bodies, which need caller/vtable evidence
  to separate.
