# Source-file names leaked in the exe

The exe contains the developers' source paths. Searching the v1.163 program for `HYBRID FLEET` finds 15 strings of the form `D:\!ESSENTIALS\PROJECTS\HYBRID FLEET 2013EX\<file>`.

## Where such strings come from
C and C++ compilers have a built-in `__FILE__` that expands to the full path of the file being compiled. Assert and error-log macros print it (with `__LINE__`), so the path ends up as a string in the exe. It costs nothing to read and gives a free map of the source layout and of which subsystems exist.

## The 15 strings (v1.163) [observed]
| String address | File |
|---|---|
| `0x1403525f8` | AircraftLogic.cpp |
| `0x140352cf0` | Body.h |
| `0x140353d08` | Body.cpp |
| `0x140355078` | Creature.cpp |
| `0x140356860` | D3DEngine\D3DEngine.cpp |
| `0x14035ba20` | Editor.cpp |
| `0x14035f528` | Escadra.cpp |
| `0x140360b50` | FX.cpp |
| `0x140363628` | Gui.cpp |
| `0x140368910` | InputTask.cpp |
| `0x140368cb0` | Joint.cpp |
| `0x14036b9c0` | main.cpp |
| `0x140374930` | Profile.cpp |
| `0x140376090` | Level.cpp |
| `0x1403771f0` | VideoTask.cpp |

## What it tells us
- Frame work is organised as tasks (`InputTask`, `VideoTask`); VideoTask.cpp's string anchors the scene dispatcher, see [render-pipeline.md](render-pipeline.md).
- Subsystems: `Gui`, `Editor`, `Level`, `FX`, `Body`/`Creature`/`Joint` (physics objects), `AircraftLogic`, `D3DEngine` (a subfolder), `Escadra` = fleet, `Profile` = save/profile.
- Only files that contain an assert or log call show up, so this is not the full file list.

## Cross-reference: functions that reference each `__FILE__` string (v1.163) [observed]
Read with a read-only Ghidra script. Entry addresses are listed; the current Ghidra name is given only where one is known, and Ghidra names here are often misleading `rep_...` labels, so treat them as guesses. "Undefined code" means the reference sits in bytes that are not part of any defined function.

| File (string address) | Refs | Functions (entry) |
|---|---|---|
| AircraftLogic.cpp (`0x1403525f8`) | 4 | `0x140007de0`, `0x14000ae90`, `0x14000b370` (renderAircraftWeaponOutOfScreen?), `0x14000fbc0` |
| Body.h (`0x140352cf0`) | 1 | `0x140048080` |
| Body.cpp (`0x140353d08`) | 41 | `0x14001b5d0`, `0x14001baf0`, `0x14002bb50`, `0x14004b010` (Reflect), `0x14004b330`, `0x14004b530`, `0x14004edd0` (CreateShell?), `0x140051760`, `0x140051850`, `0x140051c40`, `0x140051e20`, `0x1400520b0`, `0x1400521f0`, `0x140054040`; plus 16 refs from undefined code (`0x140019ca5`, `0x14001b3fc`..`0x14001ba08`, `0x14001c034`, `0x14004a94d`..`0x14004abc2`) |
| Creature.cpp (`0x140355078`) | 4 | `0x14006ef10` (CreateSpriteCreature), `0x14006f010` (CreateSprite), `0x140078b40` |
| D3DEngine\D3DEngine.cpp (`0x140356860`) | 5 | `0x140082f30`, `0x1400830f0`, `0x140083b50` (checkD3DEngineStatus?, the flush call used by the seam work), `0x140083ed0` (InitD3DEngine?) |
| Editor.cpp (`0x14035ba20`) | 9 | `0x1400bbbf0` (memcmp_editor), `0x1400d2a10` (EDITORCPP), `0x1400da8b0` |
| Escadra.cpp (`0x14035f528`) | 19 | `0x1400e6aa0`, `0x1400eab10`, `0x1400eb460`, `0x1400f1940`, `0x1400f3700`, `0x1400f3860`, `0x1400f3c10` (validateMissileFloats?), `0x1400f4070`, `0x1400f48c0`, `0x1400f4a20`, `0x1400f9460`, `0x140111ff0` (the fleet update that docks/refuels, see [mods/refuel.md](../mods/refuel.md)); plus 2 refs from undefined code (`0x140117d9b`, `0x140117dee`) |
| FX.cpp (`0x140360b50`) | 1 | `0x140122e10` (cosf_specialFX?) |
| Gui.cpp (`0x140363628`) | 3 | `0x14012f120` (ClickFunc), `0x140166420` |
| InputTask.cpp (`0x140368910`) | 4 | `0x14018b530`, `0x14018c540` |
| Joint.cpp (`0x140368cb0`) | 2 | `0x140193a10` (renderJoints?) |
| main.cpp (`0x14036b9c0`) | 40 | `0x1401a6ea0`, `0x1401a94d0`, `0x1401b7da0` (changeAircraftState?), `0x14020f9a0` (validateFloatArray?), `0x14021cf40`, `0x14021f3d0` (maincpp), `0x14022c250`, `0x14023a460`, `0x14023c820`, `0x140244de0`, `0x14024c110`, `0x14024d960`, `0x140269690`, `0x14027d3a0`; plus 4 from undefined code (`0x1402101b8`..`0x14021040e`) |
| Profile.cpp (`0x140374930`) | 2 | `0x14028bb70`, `0x14028c760` |
| Level.cpp (`0x140376090`) | 2 | `0x1402c8b80`, `0x1402c9230` |
| VideoTask.cpp (`0x1403771f0`) | 12 | `0x1402ed2f0`, `0x1402f6b00`, `0x140300c20` (scene dispatcher), `0x140300db0` (editor renderer), `0x1403050a0` (battle/city renderer), `0x14030a6b0` (map renderer), `0x14030f250` (menu/other renderer), `0x140316230` |

Interpretation:
- [observed] All four screen renderers and the scene dispatcher reference VideoTask.cpp, so the rendering code of [render-pipeline.md](render-pipeline.md) lives in VideoTask.cpp.
- [observed] The flush `0x140083b50` is in D3DEngine.cpp. Ghidra names it `checkD3DEngineStatus?`; it is the engine-status check the assert strings belong to, so "flush" is our working name [guess].
- [observed] The refuel code `0x140111ff0` is in Escadra.cpp (fleet).
- [observed] ClickFunc `0x14012f120` is in Gui.cpp.

## Earlier attempt (superseded)
An earlier query said the VideoTask.cpp xrefs were not usable (only DATA references from `rep_...` regions, `0x1402ed7ad`-`0x140316722`, and nothing for the other 14 strings). That was incomplete: the table above, read with a script, resolves them to the functions listed. [guess] The `rep_...` regions are probably parts of those same functions (the address ranges overlap), not checked.
