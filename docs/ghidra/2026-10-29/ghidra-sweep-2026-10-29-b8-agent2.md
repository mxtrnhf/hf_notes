# Ghidra sweep 2026-10-29 — batch 8, agent 2 (`.rdata` creation B)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every qword in `.rdata` `0x140352000–0x14036A000` that points into
`0x140100000–0x1401AFFFF` and has **no function object**. The four HGE RNG slots
`0x140174350 / 0x140174320 / 0x1401742d0 / 0x140174310` are agent 9's and were
**not touched** (agent 9 created and named them while this pass ran).

Start: **124 targets** with no function object (excluding the four agent-9 slots).
End: **120 targets** — the list was live-derived from `.rdata`, and the b7-agent8
note's slice matched it exactly.

**120 created**, **0 failed**, **89 named**, **31 created + plated but left
`FUN_*`**, **0 skipped**.

Every target was checked first: all 120 already had a valid decoded instruction at
the exact target address (prologue, getter, tail-jump or this-thunk), so none is a
non-prologue artefact. Bulk creation request posted on the batch-8 blackboard
(`@agent2 -> creation`, count 120) before creating.

## Renames (89)

### HGE_Impl vtable `0x1403672f0` — system / state (10)

| addr | slot | new name |
|---|---|---|
| 0x14017d5a0 | +0x08 | `HGE_System_Initiate` |
| 0x14017d3d0 | +0x20 | `HGE_GetErrorMessage` |
| 0x14017d3e0 | +0x60 | `HGE_GetStateBool` |
| 0x14017d460 | +0x68 | `HGE_GetStatePtr` |
| 0x14017d4b0 | +0x70 | `HGE_GetStateHandle` |
| 0x14017d4d0 | +0x78 | `HGE_GetStateInt` |
| 0x14017d560 | +0x80 | `HGE_GetStateString` |
| 0x14017dd00 | +0x40 | `HGE_SetStatePtr` |
| 0x14017dd70 | +0x48 | `HGE_SetStateHandle` |
| 0x14017dd90 | +0x50 | `HGE_SetStateInt` |

### HGE_Impl — resource / ini (8)

| addr | slot | new name |
|---|---|---|
| 0x140174380 | +0x88 | `HGE_LoadFileRaw` |
| 0x140174c20 | +0xa8 | `Resource_FreeCachedFile` |
| 0x140174b00 | +0xb8 | `Resource_BuildFullPath` |
| 0x140173720 | +0xd0 | `Ini_SetInt` |
| 0x140173590 | +0xd8 | `Ini_GetInt` |
| 0x1401736a0 | +0xe0 | `Ini_SetFloat` |
| 0x1401734f0 | +0xe8 | `Ini_GetFloat` |
| 0x1401737a0 | +0xf0 | `Ini_SetString` |

### HGE_Impl — timer / sound / input / gfx (32)

| addr | slot | new name |
|---|---|---|
| 0x14017ef00 | +0x120 | `Timer_GetTime` |
| 0x14017eee0 | +0x128 | `Timer_GetDelta` |
| 0x14017eef0 | +0x130 | `Timer_GetFPS` |
| 0x14017c680 | +0x150 | `Sound_PlaySample` |
| 0x14017cb60 | +0x1d0 | `Sound_ChannelRestart` |
| 0x14017c1f0 | +0x1d8 | `Sound_ChannelSetVolume` |
| 0x14017c2c0 | +0x1e0 | `Sound_ChannelSetPan` |
| 0x14017c170 | +0x1f0 | `Sound_ChannelPause` |
| 0x14017c1b0 | +0x1f8 | `Sound_ChannelPlay` |
| 0x14017c3d0 | +0x200 | `Sound_ChannelStop` |
| 0x14017c190 | +0x208 | `Sound_PauseAll` |
| 0x14017c1d0 | +0x210 | `Sound_StartAll` |
| 0x14017c110 | +0x220 | `Sound_ChannelIsPlaying` |
| 0x14017c040 | +0x258 | `Sound_ChannelRemoveFX` |
| 0x14017c790 | +0x260 | `Sound_FXSetParameters` |
| 0x140173870 | +0x270 | `Input_GetMousePos` |
| 0x1401738d0 | +0x278 | `Input_SetCursorPos` |
| 0x140173890 | +0x280 | `Input_GetMouseWheel` |
| 0x1401738a0 | +0x288 | `Input_GetMouseButton` |
| 0x1401738b0 | +0x290 | `Input_GetKeyDown` |
| 0x1401738c0 | +0x298 | `Input_GetKeyToggled` |
| 0x140173850 | +0x2a0 | `Input_GetKeyState` |
| 0x140173840 | +0x2a8 | `Input_GetKeyName` |
| 0x140173830 | +0x2b0 | `Input_GetMouseDeltaX` |
| 0x1401737d0 | +0x2b8 | `Input_GetMouseDeltaY` |
| 0x14016cbe0 | +0x2c8 | `RenderQuadColored` |
| 0x14016cd00 | +0x2d0 | `RenderQuadBlend110` |
| 0x14016ccf0 | +0x2d8 | `RenderQuadBlend20` |
| 0x14016cbc0 | +0x2f0 | `HGE_GetWindowHandle` |
| 0x14016cbd0 | +0x2f8 | `HGE_GetWindowStyle` |
| 0x14016cbb0 | +0x300 | `HGE_CreateRenderTarget` |
| 0x14016cba0 | +0x308 | `HGE_CreateResourceObject` |

(That is 32 rows.)

### Node / Frame / Creature (3)

| addr | vtable / slot | new name |
|---|---|---|
| 0x1401049c0 | 0x14035ecb8 +0x80 | `Node_SetRelinkTarget` |
| 0x14011bd90 | 0x140360670 +0x140 | `Thunk_DisableCreatureBody` |
| 0x14011ca30 | 0x140360670 +0x150 | `Thunk_ChildCall150Slot` |

### GUI element classes (14)

| addr | vtable / slot | new name |
|---|---|---|
| 0x14012ca20 | 0x140361238 +0 | `Gui_ScalarDeletingDtor238` |
| 0x14012ca60 | 0x140360ed8 +0 | `Gui_ScalarDeletingDtorED8` |
| 0x14012d4e0 | 0x140369b50 +0x138 | `Gui_HandleCardDrop` |
| 0x14012d660 | 0x140369b50 +0x130 | `Gui_HandleCardPickUp` |
| 0x14012d830 | 0x140362b00 +0x308 | `Gui_HandleTextInputKey` |
| 0x14012d920 | 0x140362b00 +0x310 | `Gui_HandleTextInputCommit` |
| 0x14012da20 | 0x140369b00 +0x310 | `Gui_ClearInputCapture` |
| 0x14012db90 | 0x140362e60 +0x348 | `Gui_UpdateKeyBindingLabel` |
| 0x1401636b0 | 0x140369b50 +0x30 | `Gui_LoadAndInitElements` |
| 0x140165b80 | 0x140362098 +0x38 | `Replica_AddProperties` |
| 0x1401660c0 | 0x140362420 +0x80 | `Replica_Relink` |
| 0x1401680f0 | 0x140369b50 +0x2d0 | `Gui_DrawFlashOverlay` |
| 0x140168c00 | 0x1403615c8 +0x2c8 | `Body_DrawTextGrids` |
| 0x140167610 | 0x140362420 +0x238 | `Body_UpdateShellTrajectory` |
| 0x14016a130 | 0x140361238 +0x358 | `Shell_Constructor` |

(15 rows.)

### HGE media / resource descriptors (8)

| addr | vtable / slot | new name |
|---|---|---|
| 0x140178a00 | 0x140366d00 +0x10 | `ResDesc_DeleteCachedObject` |
| 0x140178d50 | 0x140366ca8 +0x08 | `URAnimation_CreateObject` |
| 0x140178ed0 | 0x140366d00 +0x08 | `TextGrid_CreateObject` |
| 0x140179030 | 0x140366cc0 +0x08 | `URFont_CreateObject` |
| 0x1401700f0 | 0x140366710 +0 | `ResDesc_ScalarDeletingDtorCopy8` |
| 0x140170b60 | 0x140366628 +0x18 | `ResDesc_IsSameResource` |
| 0x140192e40 | 0x140368ba8 +0 | `Joint_ScalarDeletingDtorAlt` |
| 0x1401950f0 | 0x140368e18 +0x40 | `SLink_ReleaseChild` |

### Property / serialisation vtables, misc dtors (11)

| addr | vtable / slot | new name |
|---|---|---|
| 0x1401952a8 | 0x140369000 +0 | `Thunk_FreeAdjustedThis` |
| 0x1401a83c0 | 0x140369448 +0 | `ISerializable_ScalarDeletingDtor448` |
| 0x1401a8400 | 0x140369790 +0 | `PositionScale_ScalarDeletingDtor` |
| 0x1401a8440 | 0x1403694b8 +0 | `NPC_ScalarDeletingDestructor` |
| 0x14018fed0 | 0x140354a98 +0x10 | `bProperty_ParseBoolText` |
| 0x14018ffe0 | 0x140354b38 +0x10 | `liProperty_ParseInt64Text` |
| 0x140190150 | 0x140369248 +0x10 | `miiProperty_FreeValues` |
| 0x140190cf0 | 0x140354b38 +0x08 | `listVectorsProperty_SerializePairs` |
| 0x140190db0 | 0x140369248 +0x08 | `miiProperty_SerializePairs` |
| 0x140191130 | 0x140354ae8 +0x08 | `sProperty_SerializeString` |
| 0x140191370 | 0x14035df78 +0x08 | `vectorVectorsProperty_SerializePairs` |
| 0x140191430 | 0x140354b88 +0x08 | `viProperty_SerializeInts` |
| 0x140191ef0 | 0x14035df78 +0x18 | `ListProperty_ResetValues` |

(13 rows. Totals by section: 10+8+32+3+15+8+13 = 89.)

## Created + plated, left unnamed (31)

Each has a plate that records the vtable/slot, parameters and behaviour. Names were
withheld because the owning class or the semantic label is not provable:

| addr | why unnamed |
|---|---|
| 0x140104a80 | Escadra remove hook; the linked-object field and the player-background side effect do not name the hook |
| 0x14011bda0 | stage propagation + enable; class field names unknown |
| 0x14011caa0 | predicate on a `+0x178` sub-object with class code 2 - type unknown |
| 0x14012cf20 | GUI map-sky layout/link step; only flags and callees are known |
| 0x14012d210 | GUI child-group activation; role overlaps `Gui_IsElementActive`/radio |
| 0x14012da30 | map click/refresh handler; behaviour straddles several slots |
| 0x14012dd90 | slider-list refresh (sprites `slider_std`/`slider_green`, `list_add`/`list_remove`) |
| 0x14012e1e0 | inventory grid layout |
| 0x14012e7e0 | `lootBoxCoins()` wrapper |
| 0x14012e7f0 | slider drag with min/max clamp |
| 0x14012e8d0 | hover-driven slider (ship-zoom style) |
| 0x14012ece0 | GUI child-group deactivation |
| 0x14015de50 | HUD marker registration/draw (map cell pool `0x143faa680`) |
| 0x14015e930 | HUD marker registration/draw, second table |
| 0x14015f0d0 | body stats/label draw with ZOOM_LEVEL-1 shadow fix-up |
| 0x14015f8d0 | trivial getter of `+0xa80` (value/alpha) |
| 0x14015f8e0 | element accessor into the `0x18`-stride vector at `+0xe88` |
| 0x14015f930 | returns `&+0xa60` std::string |
| 0x14015f950 | element accessor into the `0x20`-stride vector at `+0xe70` |
| 0x14015f990 | trampoline to slot +0x368 |
| 0x140165860 | property parse callback for names `time` / `emo` |
| 0x14016bd10 | thunk `ADD RCX,0xe88; JMP 0x140150490`; target has no function object |
| 0x14016bdf0 | clamp `[0,1]` setter of `+0xa80` |
| 0x14016be10 | large GUI element initialiser |
| 0x14016bea0 | string setter that also stores `atof` into `+0xa80` |
| 0x14016bf00 | large GUI layout/refresh method |
| 0x14016c6d0 | typing/echo handler (plays `type_01`) |
| 0x140170b80 | constant getter `0x45800000` (4096.0f) |
| 0x14017c780 | forwards through the runtime-resolved pointer `DAT_1439e89b0` |
| 0x14017c800 | returns `-1` unconditionally |
| 0x140190c10 | property WriteField via `Node::WriteParameter_`; subclass unknown |

## Structure facts for `docs/structures.md` (agent 10)

* **`HGE_Impl` vtable `0x1403672f0` is now slot-mapped** (0x328 bytes, 101 slots):
  `+0x00` Release, `+0x08` System_Initiate, `+0x18` System_Shutdown/Start family,
  `+0x28` System_Log, `+0x20` GetErrorMessage, `+0x38/+0x40/+0x48/+0x50/+0x58`
  SetState{Bool,Ptr,Handle,Int,String}, `+0x60/+0x68/+0x70/+0x78/+0x80`
  GetState{Bool,Ptr,Handle,Int,String}, `+0x88` raw file load,
  `+0x90/+0x98` Resource_LoadFileData, `+0xa0/+0xa8` free file/cached file,
  `+0xa8` FreeCachedFile, `+0xb0` RemoveAllPacks, `+0xb8` BuildFullPath,
  `+0xc0/+0xc8/+0xd0` EnumFiles/EnumFolders, `+0xd0..+0xf0` Ini_Set/Get Int/Float/String,
  `+0xf8` Ini_GetString, `+0x100..+0x118` HGE RNG (agent 9), `+0x120/+0x128/+0x130`
  Timer_GetTime/Delta/FPS, `+0x138/+0x148` Sound_Load/Free, `+0x150` Sound_PlaySample,
  `+0x158` Stream_Play, `+0x160..+0x190` music, `+0x198..+0x218` channel state,
  `+0x1c0/+0x1c8` Stream_Load/Free, `+0x1d0..+0x220` channel restart/volume/pan/
  pause/play/stop and pause/start-all, `+0x228` Channel_GetLength, `+0x258`
  ChannelRemoveFX, `+0x260` FXSetParameters, `+0x268` dynamic FX pointer,
  `+0x270..+0x2b8` input getters, `+0x2c0` Input_GetEvent, `+0x2c8` quad with colour,
  `+0x2d0/+0x2d8` quad with blend +0x110 / +0x20, `+0x2e0` Gfx_RenderQuad,
  `+0x2f0/+0x2f8` window handle/style, `+0x300` render-target factory,
  `+0x308` resource-object factory, `+0x310` Texture_Load.
* **HGE state ids** (from the Set/GetState switches): bool 1..7 read bytes
  `+0x754/+0x755/+0x756/+0x95f/+0x975/+0x974/+0x980`; ptr 8..0xd are
  `+0x610/+0x618/+0x620/+0x628/+0x630/+0x638`; handles 0xf = `+0x300` (HWND),
  0x10 = `+0x978`; ints 0x11 width `+0x748`, 0x12 height `+0x74c`, 0x13..0x19
  `+0x750/+0x960/+0x964/+0x968/+0x96c/+0x970/+0x984`; strings 0x1a icon `+0x640`,
  0x1b title `+0x648`, 0x1c ini path `+0x757`, 0x1d `+0x85b`.
* **HGE+I/O fields**: `+0x300` main HWND, `+0x309` error-message buffer,
  `+0x409` base directory, `+0x648` application name, `+0x757` ini file,
  `+0xb10` current full path, `+0xc18` cached-file list head,
  `+0xd68` accumulated time (float), `+0xd6c` frame delta, `+0xd74` FPS,
  `+0xd70` frame period, `+0xd78/+0xd7c` timeGetTime snapshots.
  Mouse: `+0x9f0/+0x9f4` deltas, `+0x9f8` wheel, `+0x9fc/+0xa00` position,
  `+0xa04` mouse-button byte, `+0xa06[]` per-key state bytes (bit0 down,
  bit1 toggled).
* **Key-name table** at `0x1403be0f0` (pointers to strings such as
  `"Left Mouse Button"`), indexed by key code.
* **Resource descriptors**: `ResDesc` base vtable `0x140366c38`; per-type tables
  `0x140366ca8` (URAnimation), `0x140366cc0` (URFont), `0x140366d00` (TextGrid).
  Each caches its HGE object at descriptor `+0x90`; the create methods read the
  descriptor fields `+0x88` (type), `+0xa0` (name to load), `+0x120..+0x160`
  (per-type parameters).
* **Legacy property vtables**: `0x140354a68` / `0x14035df20` / `0x140369248` are
  the older property class tables; their `WriteField`/`ReadField` slots write
  `<name>=<value>` lines, the map (mii) variant uses `<key>|<value>`.
* **Stream separators** `0x140352a14` and `0x140352a18` are used by the property
  serialisers (likely `"="` / `","`).

## Cross-references for other agents

* `0x14016bd10` thunk targets `0x140150490`, which **still has no function object**
  (and no `.rdata` qword points at it) — worth adding to a future creation list.
* The four agent-9 slots now resolve as `HGE_RandSeed`, `HGE_RandInt`,
  `HGE_RandFloat`, `HGE_RandGetState`; this pass did not touch them.
* `0x14017c780` depends on a runtime-resolved pointer `DAT_1439e89b0` (BASS FX
  entry loaded by the sound init); do not treat it as a plain BASS import.
