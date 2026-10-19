# UI events, screens, gold, location and fleet (probe v2.0 run)

Question: can the probe say, in words, which screen the game is on, what was clicked, what text and sounds a screen uses, when gold changes, where the player is and what the fleet does? Run: probe v2.0 (crate `hf_probe`, commit `417667c`, DLL sha256 `57238a25...`, 464,384 bytes) on Steam 1.163, 2026-10-14, started 14:21:31 (modloader log), with QoL loaded (elevation hint `window`; **refuel and speed disabled** in `qol.json`). Tags: legend in `../../README.md`. Logs are preserved outside the repo in `$HF_DEV/hf_probe_build/logs/2026-10-14_1421_v2.0/` (`probe.log` 5432 lines, `probe_ammo_raw.txt`, `modloader.log`, `client.log`, `error.log`). Background and the earlier runs: [probe-run-1.md](../runs/probe-run-1.md).

## Result in one table
All four hooks installed (`HOOK click/text-key/sound/level-load installed`), the game ran about 5 minutes and exited normally (`client.log` "Clientlog finished", `error.log` "Errorlog finished") [game]. Lines: MEM 1840, TEXT 1503, SOUND 1064, KEY 314, MOUSE 250, LOAD 133, CLICK 95, NOISE 43, MODE 43, AMMO 38, FLEET 36, HELD 24, GOLD 18, WHEEL 14, LOCATION 6, HOOK 4, PROFILE 2.

| Event | What it gives | Verdict |
|---|---|---|
| `CLICK` | the named GUI element of every accepted click, plus the handler address | works, readable timeline of the whole session [game] |
| `TEXT` | localised-string keys a screen asks for, per screen | works; says what a screen shows [game] |
| `SOUND` | sound names with the caller | works [game] |
| `GOLD` / `PROFILE` | cash changes, validated by purchases | works [game] |
| `LOCATION` | city name, second name, type, script and level file of the current location | works [game] |
| `FLEET` | player fleet position, speed, heading, fuel and capacity | works [game] |
| `LOAD` | loaded `.seria` path | **read the wrong argument in v2.0**, fixed in v2.1 (not yet run) |

## How the entry hooks work [code]
A function entry has RSP = 8 mod 16 (return address just pushed) while patchy's register saver expects 0 mod 16. Layout used for every hook: `sub rsp,8`, patchy `preserved_call(hook, setup, none)`, `add rsp,8`, the stolen instructions, jump back to `entry+N`. The hook runs **before** the stolen bytes, so the registers still hold the caller's arguments. The original return address sits at `[rsp+0xC8]` when the setup bytes run (8 + 7 pushes of 8 + 0x88) and is loaded into an argument register the hook does not need: `mov r9,[rsp+0xc8]` = `4C 8B 8C 24 C8 00 00 00`, or R8 with `4C 8B 84 24 C8 00 00 00`. Proof it is right: the click caller `+0x12d16d` lies inside `GUI::HandleClick` (`0x14012d050`), the static caller of the hooked function [game+code]. Each hook has its own `PatchSession` and its own byte pre-check and can be switched off in `probe.json` (`hook_clicks`, `hook_text_keys`, `hook_sounds`, `hook_level_load`, `watch_gold`, `watch_fleet`, `watch_location`).

| Hook | Entry | Arguments used | Stolen bytes (N) |
|---|---|---|---|
| click | `FUN_14012f120` | RCX context, RDX `gui*`, R8D button, R9 = caller (the original R9D was `[gui+0xa80]`) | 26: `40 55 53 56 57 41 54 41 55 41 56 41 57 48 8d ac 24 f8 d3 ff ff b8 08 2d 00 00`; the function then does a RIP-relative `call __chkstk`, so the copy stops before it |
| text key | `0x1401ae090` (localised string lookup) | RCX out `std::string*`, RDX key `char*`, R8 = caller | 12: `40 53 55 57 41 55 41 57 48 83 ec 50`; the next instruction is RIP-relative |
| sound | `0x1402e30e0` (Ghidra `playSFXSound?`) | RCX kind, RDX name `char*`, R8 node, R9 = caller | 15: `48 8b c4 48 89 58 08 48 89 68 10 48 89 70 18` |
| level load | `0x140225930` (Ghidra `LoadSeriaFile`) | RCX destination object, **RDX path**, R9 = caller | 26: `48 89 5c 24 08 48 89 74 24 10 55 57 41 56 48 8d 6c 24 d0 48 81 ec 30 01 00 00` |

Sound callers include `BuyPartShop`, `BulletImpact`, `DetachShips`, `ElectronicRadarTutorial`, `FUN_140073560` and `FUN_14007eb50`. Level-load callers include `FUN_14012f120`, `FUN_140233710`, `FUN_140240b90`, `Load` `0x140293f90`, `PrepareMainLoop` `0x1401ad5a0`, `loadSeriaForLibraries?` `0x1400d09a0`, `loadShipBackups?` `0x14023cd00` and the wrapper `0x140225c00`.

See also [click-func.md](click-func.md): `FUN_14012f120` is the 1.163 version of the 1.151 function `!ClickFunc`.

## Clicks [game+code]
Only clicks the GUI **accepted** are logged: the hook sits on `FUN_14012f120`, called at the end of `GUI::HandleClick` (`0x14012d050`); hooking the hit test would log every miss.

| Field | Where | Notes |
|---|---|---|
| element name | C string at `gui+0xa40` | the field `FindGuiElement` (`0x1401a9170`, list `GUI_ELEMENTS`) compares [code]; not always set: printed `?` for some, once `pN#8` |
| class | `std::string` at `gui+0x8` | `Gui`, `List`, `Slider` |
| value | 4 bytes at `gui+0xa80` | an int, but `1082130432` = 4.0f, `1065353216` = 1.0f, `1073741824` = 2.0f, `1091567616` = 9.0f on `GL_LIST_BUTTON`: a float on list buttons and sliders [guess for the meaning] |
| effect | `std::string` at `gui+0xad8` | v2.0 called it `action`; the values (`gui_mil_focus`, `gui_red_opaq`, `gui_hud_white`, `editor_white`, `slider_green`) are **Distortion resource names** defined in `Media/Dst/distortion.res`, not Animation names [file]; the getter for that type is `0x140170270` (type 0xb, see [images-and-sprites.md](images-and-sprites.md)). So `+0xad8` is the element's distortion (hover/focus effect) name; v2.1 prints it as `fx` |

Caller offsets: `+0x12d16d` for GUI clicks, `+0x12f2b8` for List clicks.

Element names seen, in the order of use: `TITLE_OPTIONS`, `TITLE_STRETCH`, `TITLE_WINDOWED`, `TITLE_BACK`, `TITLE_SHIPWORK`, `INV_SLOT` (editor palette slot), `EDC_SAVELOAD`, `GL_LIST_BUTTON` (class `List`), `EDITOR_LOAD_YES`, `EDC_TEST`, `EDC_TEST_DIF` (Slider), `EDC_TEST_FIGHT`, `PRECOMBAT_OK`, `RETRY_NO`, `EDITOR_EXIT_YES`, `TITLE_CONTINUE`, `TITLE_DELETE`, `TITLE_SLOT`, `DESK_OK`, `DIALOG_ANS`, `GL_GLOSSARY`, `PRESELECT_CARD`, `CARD_ACTIVE`, `PRESELECT_HARD`, `PRESELECT_DONE` (new-game presets), `HOUSE_SUPPLIES`, `FUEL_BUY_SLIDER` (Slider), `SUPPLIES_AMMO`, `BUY_SLIDER` (Slider), `BUY_BUY`, `SUPPLIES_EXIT`, `LANDMODE_EXIT`, `MAP_LOCATION`, `MAP_MAP`, `LOOT_BOX`, `PRELANDING_OK`, `ED_SHPWRK_LAND`, `ED_SHPWRK_EXIT`, `QUIT_SAVEGAME`, `SAVEGAME_SLOT`, `SAVENAME_OK`.

## Which flag is which screen [game, anchored by the clicks just before each change]
This **supersedes** the earlier note that shop screens simply "use the battle branch": the branch is right, and the flags now say which screen it is.

| Dispatcher branch and flag | Screen | Anchor and text keys |
|---|---|---|
| other (`0x14030f250`) | title screen and every loading frame (about 0.05 to 0.3 s between screens) | title keys `OPTIONS_GAMMA`, `TITLE_FLASHES`, `OPTIONS_VOLUME`, `OPTIONS_SOUNDS`, `OPTIONS_MUSIC` |
| editor (`IsInEditor` = 1) | ship editor, the TEST panel and the **city shipworks** | `TITLE_SHIPWORK`, `EDC_*`, `INV_SLOT` |
| battle branch, `bb7` (`IS_IN_ARCADE_BATTLE` `0x147fc6fb7`) | combat (TEST drive and real fights) | after `EDC_TEST_FIGHT` / `PRECOMBAT_OK`; keys `HONOR_LABLE`, `RETREAT_LABLE`, `TADS_*`, `SHIP_NAME_*`, `KMH`, `*_MSG` |
| campaign branch, `campaign_d2` then `campaign_d0` (`0x147fc6fd2`, then `0x147fc6fd0`) | strategic map | keys `RADAR_MAP_LABLE`, `FUEL_MAP_LABLE`, `SHORT_MSL/AAM/SPD/RNG/CREW/LVL/MORAL`, `PROPHET_OMAR_*`, `STATS_*`, `REPUTATION`, `LOCATION_NAME_UR` |
| battle branch, `bc8` (`0x147fc6fc8`) | landed in a city: the landing hub with event and dialogue text | after `PRELANDING_OK`; keys `EVENT_BLESSING_01_1`, `CONTINUE_TEXT`, `REPUTATION`, `FLEET_MORAL` |
| battle branch, `bc9` (`0x147fc6fc9`) | the **supplies / shop screen** (also the fuel purchase) | after `HOUSE_SUPPLIES`; keys `LOCATION_NAME_*` for the whole map list |
| battle branch, `bd4` (`0x147fc6fd4`) | after `ED_SHPWRK_LAND` (leaving the city shipworks): flight HUD text, the landing / take-off arcade sequence [guess for the meaning] | keys `SUPPLIES`, `ENGINE_TEMPERATURE`, `TADS_*`, `SHIP_NAME_Sevastopol`, `KMH`, `ASM/AAM/GPB/FUEL/EVAC/FSS_TADS` |

Timeline of the run (probe seconds): title 0-26, editor 26-80, TEST combat 80-134, editor 134, title / continue / new-game presets 136-156, map 156-170, landed 170.9, supplies 171.6-183, map 184, combat 198-217, map 217-230, landed 230, city shipworks 239-250, landing sequence 250-282, shipworks 282, supplies 287, map 289.

## TEXT [game]
The dedupe set is reset at every `MODE` change and keys are counted once per `(key, caller)`, so the numbers are **first-seen keys per screen, not usage counts**: from 2 to 211 per screen (editor 70-211, map `d0` 47-73, supplies `bc9` 95-109, landing `bc8` 5-100). Each screen prints its own text list, which is the closest thing to a "what does this screen show" answer.

## SOUND [game+code]
Calling the same function from a mod (argument table, the volume-pointer pitfall): [../sound.md](../sound.md).

126 distinct names. Top: `engine_rocket_down_01` 167 (kind 8), `explosion_med_01..04` about 40 each (kind 1), `shell_in_med_01` 41 (kind 11), `shell_out_small_01..03`, `shell_out_small2_*`, `shell_out_enemy_med_*` and `shell_out_enemy_tiny_*` (kind 2 = enemy fire), `alarm_small_07`, `combat_lock`, `turbine_01` (kind 7), `missile_run_02` (kind 12), `buzz_01`, `sold_01`, `beep_01`. Counts are lower bounds (the same sound within 100 ms is folded). The first argument ("kind") is a category [guess]. `error.log` has `ERR: SX::play failed to get effect = radio_landing_start_02` at game time 0:4:15:54, which matches the `SOUND radio_landing_start_02` line at probe 254.630 s: the name reaches the game intact, the failure is inside `SX::play`, a missing asset in the game itself (seen with QoL and the probe loaded; the vanilla `hge.log` also reports a missing `.mp3`).

## Gold [game]
`PROFILE` and `GOLD` replicate `Get_Profile` (`0x140292a90` -> `0x140292ab0`) without calling it: if `[0x147fc6f81]` is non-zero and `[0x147fc6870]` is non-zero, that pointer; else the list chosen by `[0x147fc6f80]` (`0x147fc6880`/`888`, or `ProfileListStart` `0x147fc68b8` / `ProfileListEnd` `0x147fc68c0`), indexed by `ProfileNumber` `0x147fc6878`, 8-byte elements. Cash is the `i32` at `Profile + 0x2a8`.
* Title: `PROFILE 0x17872c10 gold=0` (12.2 s). New game: `PROFILE 0x1787cbf0` at 139.7 s, then `GOLD 0 -> 128682`, `-15260`, `-15260`, `-13935`, `+44455` back to 128682 while clicking the new-game cards (149-151 s).
* Shop: gold changes **live while `FUEL_BUY_SLIDER` is dragged** (172.4-172.66 s: -390, -57, -56, -19 five times, -598 in total); then each `BUY_BUY` click is followed within 15 ms by a drop: 175.935 -> **-7800**, 180.137 -> **-3400**, 182.581 -> **-3600**. This is strong validation of `Profile + 0x2a8` as the cash `i32`.
* 245.075 s: -100 on an `INV_SLOT` click in the city shipworks; 288.44 s: -1303 on `FUEL_BUY_SLIDER` in the second shop.
* The bought items cannot be named from the amounts.

## Location [game]
`CURRENT_LOCATION` is the pointer at `0x143a11940`; it is null on every map screen.

| Time | Pointer | `+0x25c` | `+0x258` | Strings found by the scan |
|---|---|---|---|---|
| 170.794 s | `0x214692f0` | 1 | 1 | `+0x8` "Location" (class name), `+0xc8` "UR" (city name), `+0x130` "SARGAS", `+0x210` "MARK_INIT", `+0x288` "City_generated.seria" |
| 198.324 s | `0x214b11a0` | 5 | 1 | `+0xc8` "ZEMARAIM", `+0x130` "VEGA", same `+0x210` and `+0x288` |

`+0x274` (float) was 0.00 on the first visit and 552106.88 at 230.093 s on the second (the station's fuel stock, [systems.md](../systems.md) Refueling [game]). `+0x25c` agrees with the city types in QoL's shop list (1 UR, 2 repair, 3 merchant, 4 fuel, 5 intel, 6 mercenary, 7 HQ) [file]. `+0x130` is probably a faction or region name [guess].

## Fleet [game]
`PLAYER_ESCADRA` `0x143a13eb0` -> `0x1ffc71f0`. Fields (Escadra): `+0x150/+0x154` position, `+0x158` speed, `+0x15c` heading (rad), `+0x498` fuel and `+0x4a0` capacity (doubles).
* Start: position (0.00, 11000.00), fuel 5.4e6 of 10,880,000 at 156 s, 5.0e6 at 157 s.
* Moving at speed 30.484, heading 0.747 (189-190 s): fuel fell about 277,000 per probe second (5.0e6, 4.72e6, 4.44e6) and the position moved about (84.2, -91.7) per second.
* At 299-302 s, speed 0 at (579.06, 10374.09): fuel **rose** 3,804,664 -> 4,165,864 -> 4,578,435 -> 4,845,847 (+361k, +413k, +267k per second). That is refuelling at a station with **the refuel mod disabled** (`qol.json` `refuel.enabled = false` at run time), so this is the **vanilla baseline** for the refuel feature (first measurement). The user has not yet A/B-tested refuel x10 or the speed curve.
* With speed disabled the editor showed TWR 2.9 and 246 km/h; vanilla gives 50 * sqrt(1.9) * 3.6 = 248 [game, vanilla].

## Level loads [game+code]
v2.0 printed the **wrong argument**: the first is the object being loaded into (shown as `<not text: 0x...>`); the path is the **second**. Two literals arrived there: `0x14035c0c8` = `Libraries/parts.seria` and `0x14035c0a8` = `Libraries/constructor.seria` [code, read from the dump]. The heap values are the path data of other files and were not decoded (v2.1 prints them). 133 loads; callers: `+0x1b08db` 81, `+0x240e59` 15 (at 198.3, 217.2, 230.1, 250.1 and 289.4 s: map and landing transitions), `+0x233b78` 14, `+0x2343ee` 6, `+0x233fd8` 6, `+0x23470b` 4, `+0x225c67` 3, `+0xd09f5` 2, `+0x2337c7` 1, `+0x13d87a` 1.

## Unknowns
* The **map and battle label seams**. Use the `TEXT` callers on the map screen (`RADAR_MAP_LABLE`, `FUEL_MAP_LABLE`) and in combat (`HONOR_LABLE`, `RETREAT_LABLE`, `TADS_*`): find the functions that contain those caller offsets, then the bind, pass, flush bracket inside the renderers `0x14030a6b0` and `0x1403050a0` (as at `0x140303faf` / `fb4` / `fc2` in the editor).
* What Location `+0x130` is (`+0x274` is the station fuel stock, [systems.md](../systems.md)); the meaning of the 4-byte value at `gui+0xa80`; whether Escadra positions are map units.
* The decoded paths of the 133 level loads (v2.1).
* A run that launches a fleet to a chosen destination and fights on the map.
* The meaning of the sound "kind" argument and of `bd4`.

## Live-test recipe
1. Install v2.1 (commit `f094dec`, DLL sha256 `582e5f67...`; fixes `LOAD` and prints the distortion name as `fx`) and repeat the session: title, editor, map, landing, shop (buy one item), city shipworks, combat.
2. Refuel A/B: enable `refuel` x10 in `qol.json`, dock at the same kind of station, read the `FLEET` fuel slope; then disable it and read the baseline again. The vanilla slope above was +267k to +413k per probe second.
3. Launch a fleet across the map and watch `FLEET` (position, speed, heading, fuel) and `LOCATION` (null on the map).
4. Use the `TEXT` callers above to find the map and battle label functions.
