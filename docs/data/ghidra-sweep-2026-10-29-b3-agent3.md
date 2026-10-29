# Ghidra sweep 2026-10-29 — batch 3, agent 3 (0x140120000–0x14016FFFF, GUI / screens)

Program `Highfleet.exe.unpacked.exe` v1.163 (`HighfleetServer`). Every name
below was applied to a `FUN_*` function in the range and given a plate comment
in the doc-comment style (summary / Algorithm / Parameters / Returns).

Focus: the trail / world-sprite render family, the pre-combat card shuffle, the
joystick settings class, the big slider handler, the text-grid helpers, and the
Stats getters whose offsets are already documented in `structures.md`.

## Renames (46)

| addr | new name | description |
|---|---|---|
| 0x140122890 | `Trail_AddSprite` | appends a media sprite to a trail: phase 1 -> short-sprite vector +0x90, phase 2 -> long-sprite vector +0xa8; called from `World_ThermalPass` with `trail_black_short_01..03` / `trail_black_long_01/02`. |
| 0x140122900 | `Trail_CreateForBody` | allocates a 0xc8 trail, links it to a body (`Link` at +0x10), stores world/screen position at +0x78, layer from body+0x8e8, and pushes it on the global trail list `DAT_1439e5fc8`. |
| 0x140122b40 | `Trail_DestroyNode` | frees one trail node: the 8-byte pointer vector at +0x60, the allocation, then unlinks and frees the list node. |
| 0x140122c40 | `Trail_ClearAll` | destroys every trail in `DAT_1439e5fc8`: writes -1.0 to the linked alpha, frees both sprite vectors (+0x90/+0xa8), the Link and the node. |
| 0x140123e10 | `WorldSprite_IsInactive` | true when `(float)(int)+0x188 * optional float at +0xd0` is 0 and the segment count +0x268 is 0 (used as a per-frame skip test). |
| 0x140123e50 | `WorldSprite_IsEmpty` | true when both pointers at +0x18 and +0x8 are null. |
| 0x140124280 | `Trail_UpdateAll` | per-frame update of every world sprite (`DAT_1439e5fd8`) and trail (`DAT_1439e5fc8`): refreshes transforms/alpha, frees finished ones, rebuilds the per-layer buckets (layer clamped to 0x46). |
| 0x140124990 | `Trail_UpdateLayerTransforms` | re-applies zoom/shadow/SetShipZoom to every trail of one layer, temporarily overriding the linked body's shadow fields. |
| 0x140124eb0 | `Trail_DrawLayer` | draws one layer bucket through `Trail_Render`, filtered by mode (0 all, 1 with +0x3c, 2 without). |
| 0x140125510 | `Trail_Render` | draws one trail: short/long sprite cross-fade by distance plus the extra segment sprites, colours from the fade factor. |
| 0x140125bb0 | `Trail_UpdateLayerZoomFade` | updates the layer's trails whose body zoom value is <= the passed threshold. |
| 0x140125e60 | `Trail_UpdateLayerTimeFade` | updates every trail of a layer and stamps the fade time +0x170. |
| 0x1401260d0 | `Trail_DrawAndUpdateLayer` | draws the sprite bucket, then updates the trail bucket of the same layer index. |
| 0x140126560 | `Trail_UpdateGeometry` | advances one trail by dt: samples the linked body position, adds distance to the fade budget, moves the history ring and recomputes width/alpha. |
| 0x14012c860 | `Precombat_ApplyCardOrder` | after a card drag: renumbers ships (+0x3ec) and moves the escadra list nodes so the squad order matches the on-screen card order (escadra vtable +0x60/+0x50). |
| 0x14012d1c0 | `Settings_ToggleJoystickType` | toggles device type +0xe8 (0/1) for the player index at +0xe70. |
| 0x14012d410 | `Editor_HandleMeshSlotClick` | editor click on `ED_MESH_PIN` (opens the mesh picker) / `ED_SLOT_PIN` (background swap), then refreshes the element. |
| 0x14012d720 | `Inventory_HandleSlotDrop` | accepts a `NOTE_MIN_PL` drop onto an `INV_SLOT` (via slot vtable +0x380) and clears the drag Link. |
| 0x14012d970 | `Settings_ApplyKeyRebind` | looks the key up in the `KEYBOARD_LAYOUT_` tree and pushes it to every listener in the vector at +0xe70. |
| 0x14012db60 | `Gui_IsElementActive` | returns the element's vtable +0x78 active predicate. |
| 0x14012dc60 | `Settings_UpdateJoystickLabel` | writes the device name (or `...` while detecting) into caption +0xca8. |
| 0x14012dd00 | `Settings_UpdateJoystickTypeLabel` | writes `PS` / `XBOX` into caption +0xca8 from the device type. |
| 0x14012ee40 | `Radio_HandlePanelClick` | radio/IRST panel click: requires active + flag +0xa3b, resets the frame counter and calls `variousRadioIRSTPanels_`. |
| 0x1401274a0 | `GameTask_ScalarDeletingDestructor` | scalar deleting destructor of the `Singleton<GameTask>` object. |
| 0x1401274f0 | `GameTask_Destructor` | deleting destructor of `GameTask`: frees the particle vector `DAT_1439e6038..6040`, then the object. |
| 0x14013edd0 | `Precombat_DragCard` | the pre-combat card **drag**: swaps a dragged `PRECOMBAT_A` / `PRECOMBAT_NEW_A` / `ED_SHIPWORKS_MINIFIG` with its neighbour, renumbers `MINIFIG_NUMBER` and updates +0x600. |
| 0x14013ffe0 | `Precombat_PickUpCard` | the card **pickup**: plays `precombat_up_01` + `precombat_slide`, sets the drag flags +0x5e4/+0x600.. and lifts the linked body. |
| 0x1401574b0 | `Gui_HandleSliderChange` | one change handler for every slider, dispatching on the element name: `MAPMODE_THRUST_SLIDER`, `MAPMODE_MISSION_SLIDER`, `FUEL_BUY_SLIDER`, `BUY_SLIDER`, `AUTO_REPAIR_SLIDER`, `TITLE_GAMMA/FLASHES/VOLUME/SOUNDS/MUSIC/MOUSE_SENS/WHEEL_SENS/AIMING/QUALITY`, `RADIO_SCAN/BEARING/BAND`, `TUTORIAL_RADIO*`. |
| 0x14015f540 | `Gui_HitTestPoint` | returns the element when the point is inside its active hit rect (transform via `Creature_WorldToScreen`, state-mask and flag gates). |
| 0x14015f720 | `ShipStats_GetBurnHeat` | Stats +0xc0 (burn heat per second; engines 10). |
| 0x14015f750 | `ShipStats_GetIgniteTemperature` | Stats +0xbc (ignition temperature; engines 400). |
| 0x14015f810 | `ShipStats_GetArmor` | Stats +0xc4. |
| 0x14015f9a0 | `ShipStats_GetCaliber` | Stats +0x144. |
| 0x14015f9d0 | `ShipStats_GetLoadAmount` | Stats +0x148 (magazine size). |
| 0x14015fa00 | `ShipStats_GetLoadTime` | Stats +0x14c. |
| 0x14015fa30 | `ShipStats_GetWeaponPriority` | Stats +0x140. |
| 0x140168410 | `TextGrid_LayoutProjected` | lays out a 4x4 grid in screen space from the element size, applying GUI or world (zoom/shake/shadow) transforms, writes the colour and submits it. |
| 0x1401687f0 | `TextGrid_LayoutLocal` | lays out the 4x4 grid(s) at +0xb78 / +0xe90 in element-local coordinates (8 px insets, second grid clamped to 50 px). |
| 0x14016b9c0 | `GUI_InitElementStrings` | GUI element initializer: name, class, sprite, effect defaults (`flash_large_shadow`), the `CreateShell_` geometry call and the two float params. |
| 0x14016c940 | `RelishLogo_ReleaseObject` | releases the Relish Games logo object (vtable slot 0). |
| 0x14016c960 | `RelishLogo_UpdateFade` | advances the logo fade (0..0.25 in, hold, 1.0..1.25 out), writes the four overlay tint globals, returns 1 when done. |
| 0x14016da50 | `TextGrid_DrawCells` | builds and submits the quad pieces of a text grid from the 0x58-byte cells. |
| 0x14016de00 | `TextGrid_SetCellColour` | writes the packed ARGB colour of one cell (offset +0x18). |
| 0x14016def0 | `TextGrid_SetTextureHandle` | stores the grid's texture handle at +0x198. |
| 0x14016df00 | `TextGrid_SetCellUVs` | computes per-cell UVs from a source rectangle and the texture size. |
| 0x14016f640 | `Rect_AccumulatePoint` | min/max accumulator for a float rect with a first-use flag. |

## Answers / corrections for the existing notes

* **`0x1401574b0` is not a "slider factory"** (batch 2 agent 4's skip list).
  It is `Gui_HandleSliderChange`, the single change callback of every slider in
  the game (settings screen, shop, fuel, auto-repair, radio, tutorial). The
  slider names listed there are the ones it dispatches on. Useful for
  `click-func.md`: the slider *value* logic (buy/fuel maths) lives here, not in
  `ClickFunc`; `ClickFunc` only routes the click.
* **`0x14013edd0` / `0x14013ffe0` are the pre-combat card drag pair**, not a
  hover effect: `Precombat_PickUpCard` starts the drag (sound + lift),
  `Precombat_DragCard` performs the swap and renumbering described in
  `rendering/precombat-screen.md` ("Shuffling the cards"), and
  `Precombat_ApplyCardOrder` (0x14012c860) then aligns the escadra list with
  the card order. The `precombat_up_01` / `precombat_slide` sounds named in
  the old skip note are played here.
* **New family: trails / world sprites (0x140122890–0x140126560).** This is
  the missile/body smoke-trail system that batch 2 saw only as "ship-zoom LOD":
  `World_ThermalPass` spawns a `Trail_CreateForBody` and adds
  `trail_black_short_01..03` / `trail_black_long_01/02` when a burning body is
  zoomed in (`ZOOM_LEVEL > 2`). The per-frame pipeline is
  `Trail_UpdateAll` -> per-layer `Trail_DrawAndUpdateLayer` / `Trail_DrawLayer`
  -> `Trail_Render`. `FUN_140124280/4990/4eb0/5510/5bb0/5e60/60d0/6560` in the
  batch-2 skip list are all this family.
* **Joystick settings class** (`0x14012d1a0..0x14012dd00`): the pair
  `Settings_UpdateJoystickLabel` / `Settings_UpdateJoystickTypeLabel` fills the
  caption +0xca8 shown next to the device list; `Settings_ToggleJoystickType`
  flips PS/XBOX; `Settings_ApplyKeyRebind` writes a pressed key into the
  `KEYBOARD_LAYOUT_` tree listeners. `FUN_140188940` (input range) is the
  device-by-player-index lookup these use.

## Skipped / open

| addr | size | why skipped |
|---|---|---|
| 0x14012d1a0 / 0x14012d370 / 0x14012d600 | 0x10 / 0x2a0 / 0x120 | vtable-slot callbacks of the GUI element base (each appears in ~12 element vtables). 0x14012d1a0 sets `DAT_143a13e00` via SetLink, 0x14012d370 branches on button 1/2 into `MakeGlobal_` helpers, 0x14012d600 runs `makeSoundsForMapInstruments` and clears +0x8d8..; the exact event (hover / press / release) was not provable. |
| 0x140123530 | 0x400 | `std::vector<bool>` insert/copy (bit packing) — compiler container code. |
| 0x140121560 / 0x140121580 / 0x140121870 / 0x1401261c0 | 0x20..0x140 | `std::vector` range destroy / construct / resize helpers for 0x18-byte elements. |
| 0x140122a70 | 0x70 | vector element accessor (out_of_range) for 0x18-byte elements. |
| 0x140128c70 … 0x14012cb40 | — | `std::vector<Captain>` (0x58-byte, `Captain_Constructor`), RbTree lower_bound/insert and introsort(0x114 key) internals. |
| 0x14015c180 … 0x14015cf80 | 0x40..0x440 | container/array methods of the class used by the map screen (+0xe70 vector of group pointers, +0xe88 Link array): range destroy/copy of 0x58-byte elements, push_back, clear, rotate, erase. Left unnamed because the owning class is not identified. |
| 0x14015f6f0 / 0x14016c2a0 | 0x20 | pair that halves / restores a float at +0x8f8 and sets flag +0xc7c; called from `setupPropsSecondaryMapModes` for map objects. Field meaning unknown. |
| 0x14015f7b0 / 0x14015f7e0 / 0x14015f840 / 0x14015f8a0 | 0x30 | Stats getters for +0xe8, +0xf0, +0xdc, +0x108. The offsets are not in `structures.md`; naming them would be a guess. |
| 0x140161ac0 | 0x20 | returns `BOOL_147fc6f80 \|\| DAT_147fc6f81` — one of the global mode flags; which mode is unknown. |
| 0x140162fe0 | 0x30 | true when `[obj+0x88]+0x28 == 7`, used by the map-mode prop setup. Object type 7 not identified. |
| 0x140165990 / 0x14016a040 / 0x14016fed0 / 0x14016a100 / 0x14016c130 / 0x14012c9a0 | small | container push/reset/destroy, a forwarder to `FUN_140052070` and a 0xc-stride count. |
| 0x14016cd10 / 0x14016cd30 / 0x14016cf30 | 0x20 | tiny vtable adapters (call a virtual +0x10 / +0x8 and truncate to int) and a forwarder through `newValidHGE`; no semantic name possible. |
| 0x14016dde0 / 0x14016ddf0 | 0x10 | write +0x1a4 / +0x1a0 of a text grid; call sites pass a value the decompiler could not recover. |
| 0x14016f010 / 0x14016f230 | 0x220 / 0x110 | loop over the 256 font-glyph pointers setting +0x16c / calling the sprite draw helper; the field and the purpose of the bulk pass are unclear. |
| 0x14016e… | — | remaining `rep_*` in the range are ICF duplicates of already-named functions (`loadMediaByName_`, `CopyString`, `SetBackground_`, `CreateHGE`, `WriteToClientLog`, `Property::Property`, `miscLabelsIntelBadges`, `setupPropsSecondaryMapModes`, CRT alloc/free/mem*) — not renamed by rule. |

## Remaining work in the range

60 `FUN_*` are left, and essentially all of them fall into the groups above
(container internals, four unnamed Stats getters, the map-mode half/double
pair, and the two text-grid/font bulk loops). No further GUI *builder* is
unnamed in `0x140120000–0x14016FFFF`; the screen builders all live in the
agent-4 range (`0x14017xxxx+`).
