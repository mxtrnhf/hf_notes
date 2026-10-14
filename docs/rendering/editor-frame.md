# Editor frame, input and the label-pass calls (1.163)

What the editor's per-frame code looks like and which calls draw its labels. This is the reference behind the native elevation hint; how a mod draws text: [render-pipeline.md](render-pipeline.md), [fonts.md](fonts.md), [../mods/elevation.md](../mods/elevation.md). Tags: legend in `../../README.md`. Addresses are 1.163 (image base `0x140000000`, the unpacked exe).

## What is established [code]
| Finding | Where |
|---|---|
| `Init_HGE` registers only `HGE_FRAMEFUNC` (8) = `_FrameFunc`, plus `FOCUSLOST` (10), `FOCUSGAIN` (11) and states `0xc`, `0xd`. **No `HGE_RENDERFUNC` (9)**: the game renders inside the frame function | `Init_HGE` `0x1401ad080` |
| HGE vtable offsets used there: `SetStateBool` `+0x38`, `SetStateFunc` `+0x40`, `SetStateInt` `+0x50`, `SetStateString` `+0x58`; the HGE global is `HGE`, created by `CreateHGE(0x180)` | `Init_HGE` |
| `_FrameFunc` (labelled `!FrameFunc`) calls, in order: `SomethingPreTask` `0x140286e40`, `SomethingPhysicTask` `0x140286380`, `SomethingInputTask` `0x14018dbf0`, `SomethingAITask` `0x140011180`, `SomethingGameTask` `0x140127590`, `SomethingSoundTask` `0x1402dd890`, `SomethingVideoTask` `0x140316e20`. The video task runs with a "render this frame" bool chosen by a frame-skip heuristic from recent frame times | `0x1401a8970` |
| `SomethingInputTask` reads the editor held-part global `0x1403c0d88` (xref `0x14018e46d`) and the string `EDITORMODE`: a **game-thread, per-frame site** that already knows the held part | `0x14018dbf0` |
| `SomethingVideoTask` is the render pass: a custom D3D pipeline over the media/GUI object `ArrayLoadedByMedia_res` and GUI element tables, with `FindGuiElement` lookups (`0x1401a9170`, a string-compare lookup). It does **not** use stock `hgeFont` calls | `0x140316e20` |

## Text path [code]
* The game's text is markup-driven. Strings: `{font=myriad_15}{align=2}{color=4294967295}%s` at `0x140365470` (only xref: `FUN_14012f120`, `0x1401398e3`) and `@{font=myriad_10}` at `0x140355b40` (in `shipCardsMainStatsDisp?`, `0x14007c5ca`).
* Fonts `myriad_15` and `myriad_10` are loaded by name in `Init_HGE` through `LoadNameIntoMedia`.
* The callable "draw this string at x,y" function is `0x14016f290`, see "The label pass and its calls" below.

## Editor UI [code]
* `FUN_1400beea0(bool inMenu, char, bool constructor)` is the enter-editor routine: sets `IN_MENU_` and `LOAD_CONSTRUCTOR_OR_EDITOR`, calls `DefineEditorParts`, calls `FUN_1400c7400` in the menu case, ends with `IsInEditor = 1`, and shows the `EDITORMODE` group via `0x1402326b0` (labelled `displayTextOnCreature?`; **the name is a guess**).
* `FUN_1400c7400` (`0x1400c7400`-`0x1400d0990`, about 38 KB) builds the editor GUI tree with `GUI_2` constructors (`0x14012a910`, object size `0xe70`). It references `HLP_EDITOR_01` (`0x14035be60`), `EDITOR_TOTAL_REPAIR_TIME` / `_COST` (`0x14035be20` / `0x14035be40`) and the `EDITOR_LIBRARY_*` names.
* The game has native help strings `HLP_EDITOR_01` / `_02` and a `_HINT` suffix string (`0x14036e1c8`, used in `setPlayerControls` and `FUN_1401dac00`) [guess: a hover-hint naming convention].

## Input [guess until checked]
* HGE slots from 17 on are +8 in 1.163 (`engine-hge.md`), so `KeyDown` (1.151 slot 81) would be `+0x290` and `GetKeyState` `+0x2a0`.
* Instruction search for `call qword ptr [reg+0x290]` over the whole program: **one hit**, `FUN_140019310` at `0x14001934a`, and it is a call through a **Body** vtable (`param_1`), not the HGE interface.
* `call qword ptr [reg+0x2a0]`: `FUN_14011c880` at `0x14011c94e` and `FUN_14021b240` at `0x14021b3a0`; **not inspected yet**.
* So no obvious direct HGE `KeyDown` use was found, and the slot arithmetic is unverified. The elevation mod itself polls the global `GetAsyncKeyState` on its own thread (`mods/elevation.md`).

## The label pass and its calls [code]
The string `EDITOR_TOTAL_REPAIR_TIME` (`0x14035be20`, used at `0x1400d4c86`) is in the label pass `0x1400d4380` (body `0x1400d4380`-`0x1400d6f63`, Ghidra `rep_1400cf430_VCRUNTIME140.DLL::memmove`; the number in a `rep_` name is the 1.151 address), not in the 38 KB `FUN_1400c7400`, which is the editor GUI builder that runs once on entry and draws nothing. `FUN_1400d6f70` is a second label function called from the pass. See [render-pipeline.md](render-pipeline.md). The code around the string is:
`LEA RDX,[string]` -> `CALL 0x1401ae090` (key to text) -> `CALL 0x14016f290(font, x, y, align, fmt, ...)`.

| Address | Role (our names; Ghidra names in brackets) | Notes |
|---|---|---|
| `0x1401ae090` | **localised string lookup**: `(std::string* out, const char* key)` [`displayOnUI?`] | FNV-1a 64-bit hash (`0xcbf29ce484222325`, prime `0x100000001b3`) of the key into the hash table at `DAT_143a1c3b8`/`DAT_143a1c3a8`/mask `DAT_143a1c3d0`; empty string when missing |
| `0x14016f290` | **printf-style label draw**: `(font*, float x, float y, uint align, const char* fmt, ...)` [`rep_1401637a0_..._vsprintf`] | `__stdio_common_vsprintf` into the global 0x3ff-byte buffer `0x1439e8240`, then calls `displayLableRotation_` with angle 0. Callable with just a font, coordinates and a format string. |
| `0x14016eb40` | **bitmap-font text renderer** `(font*, float x, float y, uint align, const char* text, float* out_width, float* out_height, ?, float angle)` [`displayLableRotation_`] | `align & 3`: 0 left, 1 right, 2 centre. `\n` and `@` start a new line. Glyph sprite pointers at `font + 8 + ch*8` (missing glyph falls back to `?`); advances at `font + 0x808 + ch*4` and `font + 0xc08 + ch*4`; scale fields at `font + 0x1008`, `0x100c`, `0x1010`, `0x101c`, tracking `0x1018` (`fTracking`), spacing `0x101c` (`fSpacing`), base rotation `0x1014`. Draws each glyph immediately (`FUN_140172aa0`, sprite render), so it only produces output while the scene is being rendered. |
| `0x14016f120` | sets a field at `+0x1020` of the font and every glyph sprite (`setSpriteFields`) [`setfield_0x1020SideEffects?`] | called around the labels; probably colour/alpha, unverified |

Callers of `0x14016f290` include the editor (`0x1400d4380` region, `FUN_1400d6f70`) and HUD code: `displayAmountOfHPDMG?`, `displayCityOnMap`, `displayShortage`, `checkJammed?`, `renderEmpAmount?`, `FUN_14010a980`, `FUN_14014f370`, `FUN_1402fde80`. It is the game's general label call, so a mod can draw text natively by calling it from a hook that runs inside the render pass.

GUI classes seen (Ghidra namespaces `GUI`, `Panel`, `ObjectList`): base constructor `GUI::GUI_2` `0x14012a910` (0xe70 bytes), `Panel::Constructor` `0x14012b230`, `ObjectList::ObjectList` `0x14012b0d0`, a `List` constructor `0x14012b000`, `GUI::Load` `0x140163110`, `GUI::Relink` `0x140165f70`, `GUI::HandleClick` `0x14012d050`. Do not trust Ghidra's 3640-byte `GUI` struct: it is the 1.151 `Body` layout reused as a placeholder. `FindGuiElement` `0x1401a9170` is a plain string compare.

The font is a stock `hgeFont` that the game restyles before every draw: the label pass gets it from `0x1401a8710("dinpro_14_bold", scale, 2, 0xff73604c)` at `0x1400d445e`; other labels use `dinpro_45_black`, `flash_large`, `vcr_21`. Coordinates are the 1920x1080 virtual frame ([render-pipeline.md](render-pipeline.md) [game]). Calling convention: Windows x64, floats in `xmm1`/`xmm2` (which is why the decompiler shows `edx`/`r8d` for the bit patterns).

## Unknowns
* How the editor reads keys (`FUN_14011c880` / `FUN_14021b240` not inspected; the `+0x290`/`+0x2a0` slot mapping unconfirmed).
* What `0x1402326b0` really does, and whether `_HINT` is a hover-hint mechanism.
* Whether `SomethingInputTask` runs on every frame in the editor (frame-skip applies to video, not confirmed for input).

## Live-test recipe
1. Log-only detour on `SomethingInputTask` entry (`0x14018dbf0`): count calls per second while the editor is open.
2. Read-only Ghidra: inspect `FUN_14011c880` and `FUN_14021b240`.

## The editor's own `"%i %i"` readout [code]
The two numbers at the top centre of every editor screenshot are printed in the label pass `0x1400d4380`: the format string `"%i %i"` is at `0x14035bdec` (xrefs `0x1400d473d`, `0x1400d4744`), the integers come from `CVTTSS2SI` of a vector filled by `0x140048b10` applied to the object at `[0x1403c0d40]`, and the whole block is gated by the byte `0x1403ef369` (and `[0x143a11964]` being nonzero). A neighbouring string `ED_OBJ` is at `0x14035bde4` (used at `0x1400d4516` and `0x1400d45e1`). What the numbers are (grid or cursor position) is a [guess]; see [probe-run-1.md](../runs/probe-run-1.md) for the cursor investigation.

