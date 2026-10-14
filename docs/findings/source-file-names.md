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

## Not done
The "xref functions" column (which function uses each string) was **not** added. A Ghidra xref query on these addresses (checked on `0x1403771f0`) returned only DATA references from inside oddly labelled replicated/thunk-like regions (`rep_...` names, `0x1402ed7ad`-`0x140316722`), not usable function names; the other 14 strings returned nothing in a bulk query. Not verified further.
