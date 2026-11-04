# Ghidra sweep 2026-10-29 — agent 4 (GUI / screens / input / app / precombat)

Range: `0x140120000–0x1401FFFFF`. Program `Highfleet.exe.unpacked.exe` v1.163
(`HighfleetServer`). Every name below was applied to a `FUN_*` / `rep_*` function
and given a plate comment in doc-comment style.

## Renames

| addr | new name | description |
|---|---|---|
| 0x140188ce0 | `Input_InitRawInputDevices` | loads `user32.dll` raw-input entry points, enumerates devices, registers mouse/keyboard usage; returns 0 when raw input is unavailable. |
| 0x140184f90 | `InputTask_Constructor` | `InputTask` constructor: `ISerializable` base, class name, `createVideoTaskThread_("InputTask")`, keyboard record, SDL joystick enumeration, starts raw input or falls back to doubled mouse speed. |
| 0x140185ca0 | `InputTask_Destructor` | deleting destructor: closes every SDL joystick, releases the capture object, unclips the cursor, frees the object. |
| 0x140189fa0 | `Editor_HandleEscapeKey` | editor/shipworks key handler for ESC: closes the part held in the editor, or opens the `EDITOR_EXIT` confirm dialog (`Gui_CreateConfirmDialog` with `OK_BUTTON`/`CANCEL_BUTTON`) when no save frame is up; also clears the key flags at `+0xde..+0xe1`. |
| 0x140189ab0 | `Dialog_HandleAnswerKey` | key handler for the dialog screen: finds the `DIALOG_ANS` element whose `+0xc08` equals the pressed number, splits its caption on `\|`, builds the answer list and dispatches it; ESC (0x1b) runs the quit/back chain (`LOADGAME_*`, `SAVEGAME_*`, `QUIT_CANCEL`, `RETRY_YES`, `LANDMODE_EXIT`). |
| 0x14018f8a0 | `Property_Destructor` | `Property` destructor body: resets the vtable, frees the name string and empties it. |
| 0x14018f9c0 | `Property_ScalarDeletingDestructor` | scalar deleting destructor of `Property` (destructor body + optional `free`). |
| 0x14018fa00 | `ui64Property_ScalarDeletingDestructor` | scalar deleting destructor of the `ui64` property variant (sets `ui64PropertyVFTABLE`). |
| 0x1401c0dc0 | `Preselect_BuildShipCardScreen` | builds the preselect (skirmish/PvP) ship-select screen: one `PRESELECT_CARD` per selectable ship via `displayShipCards`, `PRESELECT_DONE`/`PRESELECT_BACK`/`PRESELECT_BORDER_ROLES`, scroll area and card links. |
| 0x1401dac00 | `Title_BuildControlsPanel` | builds the title-screen controls/hotseat panel: `TITLE`, `TITLE_SQUARE`, `title_empty_menue`, `TITLE_HOTSEAT_DEVICE(_TYPE)`, the `Player` hint and `TITLE_CONTROLS_BACK`/`title_back`. |
| 0x1401dbdc0 | `Landing_BuildPrelandingPanel` | builds the pre-landing (docking) panel: `PRELANDING_TXT(_HINT)`, `PRELANDING_MINIFIG` with `sign_landing`/`sign_indocks`, the stat lines `LANDING_STAT_DAMAGE/EXPENDABLES/USVH/RADIATION`. |
| 0x1401ebe50 | `Victory_BuildBadgePanel` | builds the victory badge/promotion panel: `VIC_BADGE_PROMOTION` (`badge_promotion`, `badge_stamp_01`), `VIC_BADGE_MINIFIG`, `VIC_BADGE_BOW` with the two victor bands and the `medal_*` slots. |
| 0x1401c4ee0 | `Map_BuildMissileMarkers` | (re)builds the `MISSILE_MARK` / `MISSILE_TARGET` GUI markers around the player escadra and its missile targets, with the `sign_bomb` / `sign_fighter_mini` icons and `cursor_craft`. |
| 0x14016ade0 | `Inventory_BuildPanel` | builds the inventory/warehouse panel: `INV_SLOT` grid, `INV_SLIDER` with `slider_std`/`slider_green` and the `_BACK` button. |
| 0x14016a5c0 | `List_BuildScrollList` | builds the generic scrollable list widget: `GL_LIST_MINI`, `GL_LIST_SLIDER`, `GL_LIST_BUTTON` per row (`list_add`), using the std/green slider sprites. |
| 0x1401b3590 | `Dialog_BuildDirectionFinder` | builds the radio-direction-finder readout of the dialog screen: `TERMINAL_FIND1/2` plus the eight `DIR_N/NE/E/SE/S/SW/W/NW/FAR` labels placed around the player position. |
| 0x1401e8d80 | `Precombat_BuildLayoutDispatch` | chooses the pre-combat layout: `Precombat_BuildMapLayout` when the high-zoom flag `DAT_147fc6fe0` is set, otherwise `Precombat_BuildCardLayout`. |
| 0x1401e8da0 | `Precombat_BuildMapLayout` | high-zoom pre-combat layout: `PRECOMBAT_BACK` (`precombat_capital`), `PRECOMBAT_MAP`, one `PRECOMBAT_SPAWN` + `PRECOMBAT_SPAWN_NUM` per enemy spawn (rotated `enemy_spawn` icon and its number), the ship cards `PRECOMBAT_NEW_A`/`PRECOMBAT_NEW_B`, `PRECOMBAT_OK`, then `ammoSelectButtonPress_`. |
| 0x1401ea500 | `Precombat_BuildCardLayout` | plain pre-combat layout: `PRECOMBAT_BACK` (`precombat_back`/`precombat_front`), the `PRECOMBAT_LEVEL` caption, ship cards `PRECOMBAT_A`/`PRECOMBAT_B` with `FATIGUE_MORALE` and the player/enemy columns, `PRECOMBAT_OK`. |
| 0x140183150 | `Zip_ReadInt32BE` | reads a 4-byte big-endian integer through the reader callbacks at `+8`/`+0x30`, 0 on success, -1 on read failure. |
| 0x140183280 | `Zip_ReadUInt16BE` | reads a 2-byte big-endian integer the same way. |
| 0x140182b40 | `Zip_ReadLocalFileHeader` | parses a ZIP local file header (`PK\x03\x04` = 0x04034b50): version, flags, method, time/date, CRC, sizes and name/extra lengths, cross-checks them against the archive and returns offsets. |
| 0x14017ef10 | `Zlib_Adler32` | Adler-32 checksum (block 0x15b0, mod 0xfff1), returns `(b << 16) \| a`. |
| 0x140187100 | `Input_HandleKeyDown` | key-down event handler: maps the key code and calls `Input_KeyDown`, also latches the menu/quit shortcut flags (`0x1439e92c8..cd`, ESC, space, F-keys). |
| 0x140187260 | `Input_HandleMouseMove` | mouse-move handler: moves the dragged/edited body inside the screen bounds (`±DAT_14801fd10/14`), rebuilds the editor link previews and forwards the delta to the active scene. |
| 0x140187910 | `RbTree_InsertRebalance` | `std::_Tree` insert fix-up: recolours and rotates from the new node to the root. |
| 0x140184bb0 | `Input_Joystick_Constructor` | joystick record constructor: copies the device and SDL names, classifies the pad (`PS5 Controller`, `Xbox Series X Controller`, any other `PS…`) into `+0xe8`, stores the player index. |
| 0x140188300 | `Input_SwapJoystickPlayerIndex` | finds the device record owning the active player index (`dialog+0xe70`) and moves that index to the requested device, swapping with the previous owner; logs `Incorrect player index` for >= 4. |
| 0x14018ac30 | `Input_HandleJoystickEvent` | SDL joystick event handler: axis values into the axis slots `+0xac..+0xc0`, buttons/hats, with `joy: %d, %d, %d` range logging. |
| 0x14017c050 | `Sound_ChannelSetFX` | `BASS_ChannelSetFX` wrapper, logs `bass error: %d` and returns 0 on failure. |
| 0x14017c280 | `Sound_ChannelSeekSeconds` | seeks a BASS channel to a time in seconds (`BASS_ChannelSeconds2Bytes` + `BASS_ChannelSetPosition`). |
| 0x14016ce10 | `hgeAnimation_Constructor` | `hgeAnimation` constructor: sprite, frame count, FPS (stores `1/fps` as the frame time), starts on frame 0. |
| 0x14016cf50 | `hgeAnimation_Restart` | restarts the animation at the first (or last, for a ping-pong/reverse mode) frame. |
| 0x14016d490 | `hgeAnimation_Update` | advances the animation by `dt`, handles the loop/ping-pong/stop modes and returns whether it is still playing. |
| 0x14016eaf0 | `Font_GetCharWidth` | advance width of one glyph: `pre[c] + glyph+0x188 + post[c]`, with `?` as the fallback glyph, 0 for a missing sprite. |
| 0x1401a8670 | `Gui_WorldToScreenPoint` | converts a world point to the GUI frame: subtract the screen centre, optionally scale/divide by `ZOOM_LEVEL`, add the fast/slow shake and the target offset. |
| 0x1401a7cd0 | `Random_MT19937_Generate` | Mersenne-Twister (624-word) generator: twist step and tempering, returns the next 32-bit value. |
| 0x1401be370 | `Battle_EnterArcadeMode` | enters the arcade battle mode once: links the first ten profile creatures into `DAT_143a1c260`, sets the 60.0 timer and `IS_IN_ARCADE_BATTLE`. |
| 0x1401c0890 | `Creature_CountSubtree` | counts a creature plus every child in its `+0x100` child lists, recursively. |
| 0x14016b750 | `Gui_BindShipReplica` | binds a body to a GUI element as its `REPLICA` 3D preview: centres the body, calls `SetShipZoom`, links it at `+0xe70`, sets the name and the display flags. |

## Answers to the open questions in `rendering/precombat-screen.md`

`precombat-screen.md` listed `FUN_1401e8da0` / `FUN_1401ea500` ("what they lay
out") as open. They are now named and plated:

* `Precombat_BuildLayoutDispatch` (0x1401e8d80) is the 32-byte branch that
  `buildSquadPrecombatScreen` reaches through `FUN_1401e8d80`: high-zoom flag
  `DAT_147fc6fe0` set -> `Precombat_BuildMapLayout`, clear ->
  `Precombat_BuildCardLayout`. `DAT_147fc6fe0` is also the flag read by
  `IsHighZoomActive` (0x1402213e0), so the map layout is the **zoomed-in**
  variant of the screen.
* `Precombat_BuildMapLayout` (0x1401e8da0) creates `PRECOMBAT_BACK` /
  `PRECOMBAT_MAP`, one rotated `enemy_spawn` + `PRECOMBAT_SPAWN_NUM` per enemy
  spawn (after the first three list entries), `PRECOMBAT_NEW_A`/`PRECOMBAT_NEW_B`
  cards and `PRECOMBAT_OK`, then calls `ammoSelectButtonPress_`.
* `Precombat_BuildCardLayout` (0x1401ea500) is the plain two-column layout:
  `PRECOMBAT_LEVEL` caption, `PRECOMBAT_A`/`PRECOMBAT_B` cards with
  `FATIGUE_MORALE`, `PRECOMBAT_OK`.

Also useful for the GUI notes: `Gui_WorldToScreenPoint` (0x1401a8670) is the
small world->GUI-frame transform (`-screen centre`, `/ZOOM_LEVEL`, `+shake`,
`+target`) used by the pre-combat layout code, as opposed to
`Creature_WorldToScreen` (0x1400250a0).

## Skipped / open

Not renamed because a name would be a guess. Address, size and what was seen:

| addr | size | what it does / why skipped |
|---|---|---|
| 0x140181000 | 0x170 | reads a zlib-style `(strm, windowBits, version, stream_size)` and rejects `version[0] != '1'` / `stream_size != 0x58` — that is `inflateInit2_`, but the module has no zlib strings and uses its own `-0x66`/`-0x67` error codes; needs the caller read. |
| 0x140181b60 | 0x50 | stream wrapper returning `-0x9a`/`-0x9c`, calls 0x140182d50 with nine arguments (zip/seria decode step). |
| 0x140182d50 | 0x400 | the decode step itself (9 parameters, output buffer + lengths). |
| 0x1401893e0 | 0x240 | layout index -> game virtual key (`0x1004..0x1017`) press mapping plus the ESC back chain; the binding table was not read. |
| 0x140189620 | 0x120 | the release counterpart of the above. |
| 0x14012d1a0..0x14012dd00 | up to 0xee0 | settings/keyboard-layout GUI handlers of one class (vtable slots): `KEYBOARD_LAYOUT_` red-black tree, "PS"/"XBOX" strings, key rebinding. The class vtable was not read. |
| 0x14013edd0 / 0x14013ffe0 | 0x720 / 0x4d0 | GUI element hover/click effect keyed on the element name (`PRECOMBAT_A`, `PRECOMBAT_PLAYER_n`, `ED_SHIPWORKS_MINIFIG`), plays `precombat_up_01` / `precombat_slide` and animates the size fields; reached through a function pointer, no direct caller. |
| 0x1401574b0 | 0x1a10 | huge slider/panel factory referencing `MAPMODE_THRUST_SLIDER`, `BUY_*`, `FUEL_BUY_*`, `TITLE_GAMMA/VOLUME/SOUNDS/MUSIC/MOUSE_SENS`; probably the settings screen, but the call sites were not read. |
| 0x1401a7120 | 0x920 | 3x3 UV/cell setup helper (alloca-heavy), called from 0x1401c2ba0 with grid coordinates 0x19/0x32/0x4b/0x50. |
| 0x1401c2ba0 | 0x2e0 | nine-way switch into 0x1401a7120 (grid cell 1..8, one extra case). |
| 0x1401c7270 | 0x25d0 | particle/debris spawner (`Media/Prt/sparcles.psi`, `debris.psi`, `sparcles`, `strides_*`), called from `World_ThermalPass` — identity depends on that caller. |
| 0x140124280 / 0x140124990 / 0x140125bb0 / 0x140125e60 / 0x140126560 | 0x710..0xb30 | per-frame zoom/LOD scaling of ship bodies via `SetShipZoom`, called from `SomethingVideoTask` and the scene ticks; the family is clear but the individual entry points are not distinguishable without reading the scene ticks. |
| 0x14019xxxx cluster | — | `std::vector` / red-black tree internals for the ship-works data (`0x140196320`, `0x140196810`, `0x1401969d0`, `0x140196e80`, `0x1401aea50`, ...). Compiler output, not game logic. |
| 0x1401a2xxx..0x1401a4xxx cluster | — | more container internals (relocate/copy/destroy ranges of 0x28/0x38/0x110-byte elements). |
| 0x1401ae780..0x1401ae980 | 0x20..0x40 | range destructors for 0x38/0x48/0x110/0x188/0x28-byte element types. |
| 0x14019c6d0..0x1401a2xxx | — | the `rep_*_compData` / `rep_*_GetStats` duplicated bodies (ICF copies of already named functions). |

Known duplicate: `rep_14018b530_InputTask` (0x14018b530) is a second, identical
copy of `InputTask_Constructor` (0x140184f90) — it was left with its `rep_`
name so the two can still be told apart.

Discovered while working, for whoever reads the input code next:

* The input stack lives at 0x140181b60..0x14018ac30: `InputTask_Constructor`,
  `Input_InitRawInputDevices`, `Input_Joystick_Constructor`,
  `Input_HandleJoystickEvent`, `Input_HandleKeyDown`, `Input_HandleMouseMove`,
  `Input_SwapJoystickPlayerIndex`, `InputTask_Destructor`.
* 0x140182b40/0x140183150/0x140183280 are the ZIP local-file-header reader and
  its big-endian readers; `Zlib_Adler32` (0x14017ef10) is next to them, so the
  `.seria` data really is read out of a ZIP container, not a raw file.
