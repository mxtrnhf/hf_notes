# Config.ini reference

Source: pasted by the project owner from a community document (author/URL not recorded; treat as unverified until checked
against the game). Keys of `Config.ini` in the game folder. Write them as `KEY=value` **without spaces**, e.g. `GFX_BRIGHTNESS=1.01775`.

## Nightfall event
| Key | Meaning |
|---|---|
| `GAME COUNTDOWN` | days until nightfall (INT32) |

## Fly-mode background colors
All values are UINT32 ARGB. The digit is the time of day: **0 night, 1 morning, 2 noon, 3 evening**.

| Key pattern | Meaning |
|---|---|
| `GFX_SHADING_UP0..3` | upper color |
| `GFX_SHADING_ML0..3` | middle color |
| `GFX_SHADING_DN0..3` | lower color |
| `GFX_SHADING_SN0..3` | sun color |
| `GFX_SHADING_GL0..3` | glow color |
| `GFX_SHADING_L0..3` | sky color while landing |

## HUD glow intensity
Each is a float from 0 to 1 (a too bright HUD at night is uncomfortable). `GFX_SHADING_HUD0` night, `HUD1` morning, `HUD2` noon, `HUD3` evening.

## Take-off timings
| Key (default shown) | Meaning |
|---|---|
| `GAME_TAKEOFF_TIME_AIR=120` | time to take off during air raids |
| `GAME_TAKEOFF_TIME_BOMB=50` | normal combat, the player has bombs |
| `GAME_TAKEOFF_TIME_COMBAT=30` | normal combat, the player has no bombs |
| `GAME_TAKEOFF_TIME_UNDEF=10` | other cases |

## Dialog tags
Tags in the dialog files are written in angle brackets, e.g. `<BLUR=0>`.
`<RENDER_LAMP_ON>` / `<RENDER_LAMP_OFF>` turn the lamp effect in dialogs on and off.
(The tag census from the game's own English dialog file is in `../docs/content.md`.)

## Keys actually present in a stock `Config.ini` (Steam 1.163, observed)
`CORE_INIT_LEVEL`, `CORE_PROLOGUE_PASSED`, `CORE_LANGUAGE` (1 on the Russian install), `CORE_AIMING_MODE`, `CORE_LAST_LOADED_VERSION`,
`GFX_DITHERING_ON`, `binding=<action>|<key code>` (also `bindingMapmode=`, `bindingOther=`), `InputTask::vecPlayerDevices[n]`.
The keys in the tables above are optional and absent by default; whether each is honoured has not been tested here.

## Key bindings format [file, observed 2026-10-14]
Lines `binding=<action>|<VK>` (also `bindingMapmode=` and `bindingOther=`); `<VK>` is the Windows virtual-key code (mouse buttons 1, 2, 4 too).

| Action | Key | Action | Key |
|---|---|---|---|
| 4096 | 87 W | 4105 | 1 LMB |
| 4097 | 83 S | 4112 | 2 RMB |
| 4098 | 65 A | 4113 | 4 MMB |
| 4099 | 68 D | 4114 | 32 Space |
| 4100 | 81 Q | 4115 | 67 C |
| 4101 | 69 E | 4116 | 88 X |
| 4102 | 16 Shift | 4117 | 70 F |
| 4103 | 71 G | 4118 | 66 B |
| 4104 | 84 T | 4119 | 82 R |

`bindingMapmode` 4096..4099 = W S A D, `bindingOther` 4096..4099 = W S A D, `InputTask::vecPlayerDevices[1..3]=-1`. **U (85), P (80) and Backslash (220) are unused**, so the QoL elevation keys do not clash.

## Verbose game log [guess, untested]
`InitializeAppProperties` (`0x14023e000` region) registers APP properties; the name string at `0x140371d90` is `DBG_LOG_DEPTH`, bound to `dbgLogMode` (`0x1403c0e4c`, value 1 in the dump). The game prints a log line when `level <= dbgLogMode`; the per-frame phase lines are level 3. `Config.ini` stores APP properties as `NAME=value` lines inside the `{ m_classname=APP ... }` block, so `DBG_LOG_DEPTH=3` may give a verbose `client.log` with no mod. Back the file up first; expect a large, slow log. Next to it is `DBG_DOGMODE` (`0x140371da0`): effect unknown, do not touch.

