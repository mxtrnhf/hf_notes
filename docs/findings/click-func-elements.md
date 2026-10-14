# ClickFunc element-name catalog (v1.163)

The GUI element names that `ClickFunc` (`FUN_14012f120`, see [click-func.md](click-func.md)) compares a clicked element against. This is the "Next step" of that note, done. It is a **lower bound**, not the full list of clickable elements.

## Method
- Read-only Ghidra script over `FUN_14012f120` (v1.163). Every call to `stringCompLengthAndContent` (`0x140004a70`) was collected, and the string literal found within 10 instructions before the call was taken as the compared name.
- A literal is paired with the nearest preceding string reference, so a few pairings could be wrong; this was not hand-verified per entry [guess about accuracy].
- "Seen" counts are the number of `CLICK` lines with that element name in the 4 probe logs (`hf_probe_build/logs/*/probe.log`) plus the game's current `probe.log`.
- Groups below are by name prefix; within a group rows keep the function's address order (the tests run roughly title/menu, map, landing/city, shop/supplies, shipworks, editor). Group assignment is by prefix, not by verified screen [guess].

## Numbers [observed]
- 256 compare calls, 252 unique names (names repeat where the same element is tested twice: `ED_SHPWRK_EXIT` x3, `KEY_SPACE` x2, `KEY_ESC` x2, etc.; the table shows the first address and `(xN)`).
- One test at `0x140135d75` had no readable string nearby: listed as `<none>`.
- 43 of the 252 names appear in the CLICK logs; 209 were never seen.
- The catalog is NOT complete: 21 names seen in CLICK logs are missing from it (section below). The function also calls `FindGuiElement` x89, `memcmp` x42 and `FUN_140006d70` x185, so other elements are matched by other means (prefix compares or similar) [guess].

Bold "yes" in the last column marks names relevant to mod ideas (buy/refuse, supplies, landing, map, test buttons).

## Catalog

### Title / options (32)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x140130d7a` | `TITLE_TUTORIAL` | - |  |
| `0x14013106d` | `TITLE_DELETE` | 2 |  |
| `0x14013131c` | `TITLE_DELETE_SKIRMISH` | - |  |
| `0x1401314bc` | `PROFILE_RESET_YES` | - |  |
| `0x1401314f7` | `PROFILE_RESET_SKIRMISH_YES` | - |  |
| `0x140131532` | `PROFILE_RESET_NO` | - |  |
| `0x140131545` | `PROFILE_RESET_SKIRMISH_NO` | - |  |
| `0x140131558` | `TITLE_CONTINUE` | 3 |  |
| `0x1401315cf` | `TITLE_CREDITS` | 1 |  |
| `0x140131652` | `TITLE_SKIRMISH` | - |  |
| `0x1401316c9` | `TITLE_SKIRMISH_PVP` | - |  |
| `0x14013177f` | `TITLE_SLOT` | 3 |  |
| `0x140131851` | `TITLE_SLOT_SKIRMISH` | - |  |
| `0x140131920` | `TITLE_SHIPWORK` | 2 |  |
| `0x1401319a3` | `TITLE_OPTIONS` | 1 |  |
| `0x140131a1a` | `TITLE_EXIT` | - |  |
| `0x140131a91` | `TITLE_LANGUAGE` | - |  |
| `0x140131b68` | `TITLE_WINDOWED` | 1 |  |
| `0x140131cdc` | `TITLE_DITHERING` | - |  |
| `0x140131ddd` | `TITLE_STRETCH` | 3 |  |
| `0x140131ee1` | `TITLE_GLITCH` | - |  |
| `0x140131ffe` | `TITLE_CONTROLS` | - |  |
| `0x14013207a` | `TITLE_CONTROLS_HOTSEAT` | - |  |
| `0x1401320f6` | `TITLE_BACK` | 1 |  |
| `0x140132172` | `TITLE_CONTROLS_BACK` | - |  |
| `0x1401372ce` | `PRESELECT_DONE` | 2 |  |
| `0x140137343` | `SCR_EDITOR_SKIRMISH` | - |  |
| `0x14013736f` | `PRESELECT_HARD` | 4 |  |
| `0x14013767b` | `PRESELECT_NPLAYERS` | - |  |
| `0x14013772f` | `PRESELECT_CARD` | 9 |  |
| `0x140137b2c` | `PRESELECT_DECK` | - |  |
| `0x14013e3ad` | `TITLE_CONTROLS_RESET` | - |  |

### Quit/save/load (24)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x14013081f` | `QUIT_CANCEL` | - |  |
| `0x14013083c` | `QUIT_CAMPAIGN` | - |  |
| `0x14013088a` | `QUIT_SAVEGAME` | 1 |  |
| `0x1401308ac` | `QUIT_LOADGAME` | - |  |
| `0x1401308d0` | `QUIT_TO_EDITOR` | - |  |
| `0x1401308fe` | `QUIT_TITLE` | - |  |
| `0x140130b52` | `QUIT_TITLE_NO_ASK` | - |  |
| `0x140130b65` | `QUIT_WINDOWS` | - |  |
| `0x140130b9b` | `QUIT_RESTART` | - |  |
| `0x140130be6` | `LOADGAME_CANCEL` | - |  |
| `0x140130c0a` | `LOADGAME_TITLE` | - |  |
| `0x140130c30` | `SAVEGAME_CANCEL` | - |  |
| `0x140130c54` | `SAVEGAME_SLOT` | 1 |  |
| `0x140130c7e` | `SAVENAME_CANCEL` | - |  |
| `0x140130ca2` | `SAVENAME_OK` | 1 |  |
| `0x140138303` | `RETRY_YES` | - |  |
| `0x140138365` | `RETRY_CANCEL_LANDING` | - |  |
| `0x140138474` | `QUIT_CANCEL_LANDING` | - |  |
| `0x140138536` | `RETRY_NO` | 4 |  |
| `0x140138862` | `UNPAUSE_YES` | - |  |
| `0x1401388c2` | `UNPAUSE_NO` | - |  |
| `0x14013d4fc` | `LOADGAME_SLOT` | - |  |
| `0x14013e3c7` | `QUIT_UNSAVED_YES` | - |  |
| `0x14013e3de` | `QUIT_UNSAVED_NO` | - |  |

### Map (MAP_, MAPMODE_, MAPMARK_) (50)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x1401321ee` | `AA_RETREAT` | - |  |
| `0x14013227f` | `VIC_BADGE_MEDALS` | - |  |
| `0x140132319` | `MAP_MAP` | 4 |  |
| `0x14013280b` | `MAPMARK_MARK` | - |  |
| `0x140132860` | `cursor_eraser` | - |  |
| `0x14013289d` | `MAPMARK_RULER1` | - |  |
| `0x1401328b4` | `MAPMARK_RULER2` | - |  |
| `0x1401328cb` | `MAPMARK_DEVIDER1` | - |  |
| `0x1401328e2` | `MAPMARK_DEVIDER2` | - |  |
| `0x1401328f9` | `MAP_LOCATION` | 4 | **yes** |
| `0x140132e1b` | `MAP_ESCADRA` | 5 | **yes** |
| `0x14013328c` | `MAP_CRAFT` | - |  |
| `0x1401335ab` | `MAP_MISSILE` | - |  |
| `0x1401338a9` | `MAP_RADIOGRAMM` | - |  |
| `0x140133c7a` | `MAPMODE_MISSILE_FIRE` | - |  |
| `0x140133cf1` | `MAP_REINFORCE` | - |  |
| `0x140133d27` | `TERMINAL_INTEL_BUY_SF` | - |  |
| `0x140133ef0` | `TERMINAL_INTEL_BUY_TAC` | - |  |
| `0x140134024` | `TERMINAL_INTEL_BUY_TRADE` | - |  |
| `0x1401341fc` | `MAP_MINIFIG` | - |  |
| `0x1401342cf` | `NOTE_CLOSE` | - |  |
| `0x1401343a6` | `NOTE_MINI_CLOSE` | - |  |
| `0x140134462` | `PLAYERMADE_DELETE_YES` | - |  |
| `0x1401345cf` | `PLAYERMADE_DELETE_NO` | - |  |
| `0x14013464d` | `MAPMODE_RADIO_HANDSET` | - |  |
| `0x140134722` | `MAPMODE_MISSION_FULLTANK` | - | **yes** |
| `0x1401347fe` | `MAPMODE_MISSION_HALFTANK` | - | **yes** |
| `0x14013481b` | `MAPMODE_CARGO_CLOSE` | - |  |
| `0x140134900` | `MAPMODE_INSTRUMENTS_RULER` | - |  |
| `0x1401349ee` | `MAPMODE_INSTRUMENTS_DEVIDER` | - |  |
| `0x140134a5b` | `MAPMODE_INSTRUMENTS_PENCIL` | - |  |
| `0x140134afd` | `MAPMODE_INSTRUMENTS_ERASER` | - |  |
| `0x140134b6a` | `MAPMODE_MISSILE_SW` | - |  |
| `0x140134c1f` | `MAPMODE_MISSION_IRST` | - |  |
| `0x140134c32` | `MAPMODE_MISSION_RADAR` | - |  |
| `0x140134c45` | `MAPMODE_MISSION_RADAR_HI` | - |  |
| `0x140134d0a` | `MAPMODE_INTERCOM` | - |  |
| `0x140134de2` | `MAPMODE_SCREEN_ON` | - |  |
| `0x140134e96` | `MAP_CHART_ON` | - |  |
| `0x140134fb0` | `MAPMODE_RADAR_SHORT` | - |  |
| `0x1401350f0` | `MAPMODE_RADAR_CONT` | - |  |
| `0x140136287` | `RADIO_AUTO` | - |  |
| `0x14013644d` | `RADIO_SPEAKER` | - |  |
| `0x140136520` | `RADIO_POWER` | - |  |
| `0x1401365b2` | `SHIFT_CARD_BUTTON` | - |  |
| `0x1401366d6` | `RADIO_SAVE` | - |  |
| `0x140136946` | `MAPMODE_RADAR_SECTOR` | - |  |
| `0x140136a00` | `MAPMODE_RADAR_GROUND` | - |  |
| `0x14013e387` | `RADIO_SCAN` | - |  |
| `0x14013e39a` | `RADIO_BEARING_SWITCH` | - |  |

### City / landing (LANDMODE_, HOUSE_, SUPPLIES_, AMMO_, FUEL_, BUY_, SELL_) (33)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x140130706` | `RESCUE_REMOVE_FIRE` | - |  |
| `0x1401307a2` | `LOOT_BUTTON` | - |  |
| `0x1401351c1` | `EDC_TEST_LANDING` | - | **yes** |
| `0x1401353e7` | `PRELANDING_MINIFIG` | - |  |
| `0x1401355c8` | `PRELANDING_OK` | 2 | **yes** |
| `0x1401356a2` | `PRELANDING_CANCEL` | - |  |
| `0x140135712` | `PREDEFENDING_MINIFIG` | - |  |
| `0x140135860` | `PREDEFENDING_OK` | - |  |
| `0x140136a49` | `LANDMODE_SHIPWORKS` | - | **yes** |
| `0x140136a7f` | `LANDMODE_NPC` | - |  |
| `0x14013701f` | `HOUSE_SUPPLIES` | 5 |  |
| `0x14013706b` | `LANDMODE_RUINED_CITY` | - |  |
| `0x1401370b1` | `LANDMODE_EXIT` | 6 | **yes** |
| `0x1401370db` | `SUPPLIES_EXIT` | 5 | **yes** |
| `0x1401370fa` | `SUPPLIES_AMMO` | 4 | **yes** |
| `0x14013712d` | `AMMO_BUY_ENTRY` | - | **yes** |
| `0x140137140` | `FUEL_BUY_SLIDER` | 3 | **yes** |
| `0x140137ce8` | `AMMO_SELECT` | - |  |
| `0x140137e31` | `AMMO_SELECT2` | - |  |
| `0x140137f91` | `ORDER_SELECT` | - |  |
| `0x140137fee` | `ORDER_SELECT2` | - |  |
| `0x140138083` | `HOUSE_EXT_01` | - |  |
| `0x1401380c5` | `HOUSE_INT_01` | - |  |
| `0x1401380e5` | `CARD_DELETE` | - |  |
| `0x140138132` | `CARD_ACTIVE` | 9 |  |
| `0x140138152` | `DESK_CLOSE` | - |  |
| `0x14013825a` | `PRECOMBAT_OK` | 4 |  |
| `0x1401382a6` | `DESK_OK` | 2 |  |
| `0x1401382d7` | `DESK_ENVEL` | - |  |
| `0x140138564` | `BUY_BUY` | 4 | **yes** |
| `0x1401386ff` | `BUY_REFUSE` | - | **yes** |
| `0x140138784` | `SELL_YES` | - |  |
| `0x14013883f` | `SELL_NO` | - |  |

### Dialogue / NPC names (18)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x1401358ff` | `DIALOG_ANS` | 3 |  |
| `0x140135928` | `KEY_SPACE (x2)` | - |  |
| `0x140135944` | `KEY_ESC (x2)` | - |  |
| `0x140135ba7` | `TARKHAN_HELP` | 2 |  |
| `0x140135be1` | `ASK_REINFORCE_TUTORIAL` | - |  |
| `0x140135d75` | `<none>` | - |  |
| `0x140135f48` | `DIALOG_ANS_DESIRE` | - |  |
| `0x140135f99` | `GL_GLOSSARY` | 3 |  |
| `0x1401360f7` | `DIALOG_ARGUMENT` | - |  |
| `0x140136b13` | `HARISHID` | - |  |
| `0x140136b47` | `OMAR` | - |  |
| `0x140136b7b` | `HELLO_OMAR_1` | - |  |
| `0x140136baf` | `GIRL` | - |  |
| `0x140136be3` | `KNIGHT` | - |  |
| `0x140136c17` | `AIRBORNE` | - |  |
| `0x140136c4b` | `SCOUT` | - |  |
| `0x140136c7f` | `HISSID` | - |  |
| `0x140136cb3` | `VETERAN` | - |  |

### Shipworks (ED_SHPWRK_) (22)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x1401388d9` | `ED_SHPWRK_LAND` | 1 |  |
| `0x140138976` | `ED_SHPWRK_BUY_SHIPS` | - |  |
| `0x140138b97` | `ED_SHPWRK_HIRE_CAPTAIN` | - |  |
| `0x140138d66` | `HIRE_CAPTAIN_YES` | - |  |
| `0x140138e22` | `HIRE_CAPTAIN_NO` | - |  |
| `0x140138e35` | `TRAIN_CAPTAIN_NO` | - |  |
| `0x140138eb3` | `ED_SHPWRK_DESIGN` | - |  |
| `0x140138f5d` | `ED_SHPWRK_CARD_DELETE` | - |  |
| `0x1401392da` | `ED_SHPWRK_CARD_DELETE_PANEL_YES` | - |  |
| `0x140139364` | `ED_SHPWRK_CARD_DELETE_PANEL_NO` | - |  |
| `0x140139377` | `ED_SHPWRK_AUTO` | 1 |  |
| `0x14013998a` | `ED_SHPWRK_UNDO` | - |  |
| `0x1401399f2` | `SAVE_DESIGN_OK` | - |  |
| `0x140139c29` | `ED_SHPWRK_EXIT (x3)` | 1 |  |
| `0x140139c69` | `SAVE_DESIGN_CANCEL` | - |  |
| `0x140139dd2` | `SHPWRK_REPAIR_SELECT` | - |  |
| `0x140139e31` | `AUTO_REPAIR_SLIDER_OK` | - |  |
| `0x140139eca` | `AUTO_REPAIR_SLIDER_CANCEL` | - |  |
| `0x140139f39` | `ED_SHPWRK_SELL` | - |  |
| `0x14013a819` | `ED_SHPWRK_MINIFIG` | - |  |
| `0x14013a9eb` | `ED_SHPWRK_NEXT_YES` | - |  |
| `0x14013aaf3` | `ED_SHPWRK_NEXT_NO` | - |  |

### Editor (ED_*, EDC_*, EDITOR_*) (70)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x140138057` | `SCR_ED_RUN` | - |  |
| `0x14013ab06` | `ED_LIBRARY_OBJCREATE` | - |  |
| `0x14013abf4` | `ED_IMAGE_MASK_MESH` | - |  |
| `0x14013ac34` | `ED_IMAGE_MASK_CLEAR` | - |  |
| `0x14013ac67` | `ED_IMAGE_IMAGES` | 18 |  |
| `0x14013ada8` | `ED_SUB_ADD` | - |  |
| `0x14013adca` | `ED_SUB_LIST` | - |  |
| `0x14013ade7` | `ED_MESH_MODUL` | - |  |
| `0x14013ae7f` | `ED_MESH_BOX` | - |  |
| `0x14013af19` | `ED_MESH_CIRCLE` | - |  |
| `0x14013afa2` | `ED_SLOTS_FERMA` | - |  |
| `0x14013b03e` | `ED_SLOTS_ROTOR` | 1 |  |
| `0x14013b0ba` | `ED_SLOTS_MODUL` | - |  |
| `0x14013b136` | `ED_SLOTS_ROTATION` | - |  |
| `0x14013b1b2` | `ED_SLOTS_BUILDING` | - |  |
| `0x14013b22e` | `ED_PROP_LAYER1` | - |  |
| `0x14013b2d2` | `ED_PROP_LAYER2` | - |  |
| `0x14013b372` | `ED_PROP_LAYER3` | - |  |
| `0x14013b412` | `ED_PROP_LAYER4` | - |  |
| `0x14013b4b2` | `ED_PROP_LAYER5` | - |  |
| `0x14013b552` | `ED_PROP_LAYER6` | - |  |
| `0x14013b5f2` | `ED_PROP_LAYER7` | - |  |
| `0x14013b692` | `ED_PROP_LAYER8` | 1 |  |
| `0x14013b735` | `ED_PROP_LAYER9` | - |  |
| `0x14013b7d5` | `ED_PROP_LAYER10` | - |  |
| `0x14013b875` | `ED_PROP_LAYER11` | - |  |
| `0x14013b915` | `ED_PROP_LAYER12` | - |  |
| `0x14013b9b5` | `ED_PROP_GLOGIC_ON` | - |  |
| `0x14013ba5b` | `ED_PROP_FLOOR_ON` | - |  |
| `0x14013baf3` | `ED_PROP_FLOOR_AUX` | - |  |
| `0x14013bb93` | `ED_PROP_FLOOR_SUP` | - |  |
| `0x14013bc33` | `ED_PROP_FLOOR_EXTRA` | - |  |
| `0x14013bcd3` | `ED_PROP_LEFTTHRUST` | - |  |
| `0x14013bddb` | `ED_PROP_RIGHTTHRUST` | - |  |
| `0x14013beeb` | `ED_PROP_LEG` | - |  |
| `0x14013c01e` | `ED_PROP_CANNON_01` | - |  |
| `0x14013c15a` | `ED_PROP_CANNON_02` | - |  |
| `0x14013c29a` | `ED_IMAGE_SPRITES` | - |  |
| `0x14013c2bf` | `ED_IMAGE_BACKGROUND` | - |  |
| `0x14013c32b` | `ED_IMAGE_MIDGROUND` | - |  |
| `0x14013c397` | `ED_IMAGE_TILE` | 2 |  |
| `0x14013c408` | `ED_IMAGE_ADJUST` | 2 |  |
| `0x14013c479` | `ED_IMAGE_RENDERMESH` | - |  |
| `0x14013c4af` | `ED_SLOTS_TYPE1` | - |  |
| `0x14013c557` | `ED_SLOTS_TYPE2` | - |  |
| `0x14013c5f7` | `ED_SLOTS_TYPE3` | - |  |
| `0x14013c697` | `ED_SLOTS_TYPE4` | - |  |
| `0x14013c737` | `ED_SLOTS_TYPE5` | - |  |
| `0x14013c7d7` | `ED_SLOTS_TYPE6` | - |  |
| `0x14013c877` | `ED_SLOTS_TYPE7` | - |  |
| `0x14013c917` | `ED_SLOTS_TYPE8` | - |  |
| `0x14013c9ba` | `ED_SLOTS_TYPE9` | - |  |
| `0x14013ca5a` | `ED_SLOTS_TYPE10` | - |  |
| `0x14013cafa` | `ED_SLOTS_TYPE11` | - |  |
| `0x14013cb9a` | `ED_SLOTS_TYPE12` | - |  |
| `0x14013cc3a` | `ED_SLOTS_TYPE_M` | - |  |
| `0x14013ccda` | `ED_SLOTS_TYPE_S` | - |  |
| `0x14013cd7a` | `ED_SAVELOAD_SAVE` | - |  |
| `0x14013d222` | `ED_SAVELOAD_LOAD` | - |  |
| `0x14013d4b9` | `ED_SAVELOAD_LIST` | - |  |
| `0x14013d619` | `EDC_RESET` | - |  |
| `0x14013d7b7` | `EDC_TEST_FIGHT` | 2 | **yes** |
| `0x14013e086` | `EDITOR_EXIT_YES` | 2 |  |
| `0x14013e0af` | `EDITOR_EXIT_NO` | - |  |
| `0x14013e0d3` | `EDITOR_LOAD_YES` | 2 |  |
| `0x14013e12b` | `EDITOR_LOAD_NO` | - |  |
| `0x14013e14f` | `EDITOR_RESET_YES` | - |  |
| `0x14013e178` | `EDITOR_RESET_NO` | - |  |
| `0x14013e19c` | `EDITOR_OVERWRITE_YES` | - |  |
| `0x14013e363` | `EDITOR_OVERWRITE_NO` | - |  |

### Other (3)

| First test | Name | Seen | Mod idea |
|---|---|---|---|
| `0x140130933` | `Hall.seria` | - |  |
| `0x14013094e` | `Preselect.seria` | - |  |
| `0x140130969` | `PreselectSkirmish.seria` | - |  |
Note: `EDC_TEST_LANDING` is listed under City / landing and `LOADGAME_SLOT` under Quit/save/load because of prefix rules; both sit near the editor part of the function by address.

## Seen in CLICK logs but not in this catalog [observed]
`?`, `BUY_SLIDER`, `EDC_SAVELOAD`, `EDC_TEST`, `EDC_TEST_DIF`, `ED_CREATE`, `ED_IMAGE_MASK`, `ED_IMAGE_SCALEX`, `ED_OBJECT`, `ED_OBJECT_PANEL`, `ED_OBJ_IMAGE`, `ED_OBJ_MESH`, `ED_OBJ_PROP`, `ED_OBJ_SLOTS`, `ED_SAVELOAD`, `GL_LIST_BUTTON`, `INV_SLIDER`, `INV_SLOT`, `LOOT_BOX`, `MAPMODE_LAND`, `pN#8`.

These are handled by something other than a plain `stringCompLengthAndContent` against a literal (prefix test, `FindGuiElement` lookup, `memcmp`, or a pointer compare) [guess]. Several look like containers, sliders or lists (`*_SLIDER`, `*_SLOT`, `ED_OBJ_*`, `*_PANEL`), which fits a different matching path.

## Live-test recipe
1. Run the game with probe v2.x and `hook_clicks` on.
2. Pick a name from the Seen `-` rows (209 never seen), e.g. `TITLE_CREDITS` or `PROFILE_RESET_NO`; get to its screen and click the element.
3. Compare with the `CLICK` line the probe prints: the element name (`gui+0xa40`) should equal the catalog name. A match confirms the pairing; a different name, or no CLICK line, means the literal was paired wrongly or the element is not clickable by that route.
4. Record confirmed names back here by changing `-` to a count. Clicking names from the section above does not need a test; they are already seen.

## Unknowns
- Which branch (if any) in the decompilation each catalog name leads to; only the test address is known.
- How the 21 non-catalog names are matched.

See also [click-func-branches.md](click-func-branches.md) for decompiled branches of BUY_BUY, FUEL_BUY_SLIDER and the MAPMODE_MISSION fuel presets.
