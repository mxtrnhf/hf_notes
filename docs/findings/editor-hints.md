# Editor hints: can the elevation mod draw inside the game? (1.163, partial)

Status: **partial. A game-thread per-frame hook site is found; a callable "draw text at x,y" function is NOT. Nothing run in game.** Ghidra stayed read-only (decompile, xrefs, instruction search only). Tags as in `../../README.md`: **[game]** · **[code]** · **[guide]** · **[guess]**.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: the elevation mod shows its hint in a separate GDI window (`mods/elevation.md`); the question is whether a native in-game hint is feasible and where the seam is.

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
* **No directly callable "draw this string at x,y" function was identified.**

## Editor UI [code]
* `FUN_1400beea0(bool inMenu, char, bool constructor)` is the enter-editor routine: sets `IN_MENU_` and `LOAD_CONSTRUCTOR_OR_EDITOR`, calls `DefineEditorParts`, calls `FUN_1400c7400` in the menu case, ends with `IsInEditor = 1`, and shows the `EDITORMODE` group via `0x1402326b0` (labelled `displayTextOnCreature?`; **the name is a guess**).
* `FUN_1400c7400` (`0x1400c7400`-`0x1400d0990`, about 38 KB) builds the editor GUI tree with `GUI_2` constructors (`0x14012a910`, object size `0xe70`). It references `HLP_EDITOR_01` (`0x14035be60`), `EDITOR_TOTAL_REPAIR_TIME` / `_COST` (`0x14035be20` / `0x14035be40`) and the `EDITOR_LIBRARY_*` names.
* The game has native help strings `HLP_EDITOR_01` / `_02` and a `_HINT` suffix string (`0x14036e1c8`, used in `setPlayerControls` and `FUN_1401dac00`) [guess: a hover-hint naming convention].

## Input [guess until checked]
* HGE slots from 17 on are +8 in 1.163 (`engine-hge.md`), so `KeyDown` (1.151 slot 81) would be `+0x290` and `GetKeyState` `+0x2a0`.
* Instruction search for `call qword ptr [reg+0x290]` over the whole program: **one hit**, `FUN_140019310` at `0x14001934a`, and it is a call through a **Body** vtable (`param_1`), not the HGE interface.
* `call qword ptr [reg+0x2a0]`: `FUN_14011c880` at `0x14011c94e` and `FUN_14021b240` at `0x14021b3a0`; **not inspected yet**.
* So no obvious direct HGE `KeyDown` use was found, and the slot arithmetic is unverified. The elevation mod itself polls the global `GetAsyncKeyState` on its own thread (`mods/elevation.md`).

## Options
| | Idea | For | Against |
|---|---|---|---|
| A | Keep the GDI overlay, port it to Rust (`windows-sys`) | Works; the user confirmed it is visible under Proton (C++ version) [game] | Separate window, may not show in exclusive fullscreen, own thread |
| B | Native: per-frame hook in `InputTask`/`VideoTask` plus a reused or new GUI text element in the `EDITORMODE` group | Looks native, one thread, fullscreen-safe | Needs more RE: GUI text setter, a free label, how keys are read |
| C | Hybrid: game-thread hook for input and `m_floor` writes, overlay for display | Removes the polling-thread race; no new RE for drawing | Still an overlay window |

Recommendation: ship A or C in the first PR; treat B as follow-up research.

## Unknowns
* Which function sets the text of a GUI label, and which existing editor label is free to reuse.
* How the editor reads keys (`FUN_14011c880` / `FUN_14021b240` not inspected; the `+0x290`/`+0x2a0` slot mapping unconfirmed).
* What `0x1402326b0` really does, and whether `_HINT` is a hover-hint mechanism.
* Whether `SomethingInputTask` runs on every frame in the editor (frame-skip applies to video, not confirmed for input).

## Live-test recipe
1. Log-only detour on `SomethingInputTask` entry (`0x14018dbf0`): count calls per second while the editor is open; confirms a per-frame game-thread site.
2. Log-only detour on `FindGuiElement` (`0x1401a9170`): list the element names requested while the editor is open, to find a reusable label.
3. Read-only Ghidra: inspect `FUN_14011c880` and `FUN_14021b240`, then xref the GUI text setter from a known label such as `EDITOR_TOTAL_REPAIR_TIME`.

## Update 2026-10-14: the game's own text-draw function is found [code]
Followed the string `EDITOR_TOTAL_REPAIR_TIME` (`0x14035be20`, use at `0x1400d4c86`) in the big editor function (Ghidra body `FUN_1400c7400`, `0x1400c7400`..`0x1400d0990`; the label `rep_1400cf430_...memmove` at `0x1400cf430` sits inside it; `FUN_1400d6f70` is a second, separate editor draw function called from it). The code around the string is:
`LEA RDX,[string]` -> `CALL 0x1401ae090` (key to text) -> `CALL 0x14016f290(font, x, y, align, fmt, ...)`.

| Address | Role (our names; Ghidra names in brackets) | Notes |
|---|---|---|
| `0x1401ae090` | **localised string lookup**: `(std::string* out, const char* key)` [`displayOnUI?`] | FNV-1a 64-bit hash (`0xcbf29ce484222325`, prime `0x100000001b3`) of the key into the hash table at `DAT_143a1c3b8`/`DAT_143a1c3a8`/mask `DAT_143a1c3d0`; empty string when missing |
| `0x14016f290` | **printf-style label draw**: `(font*, float x, float y, uint align, const char* fmt, ...)` [`rep_1401637a0_..._vsprintf`] | `__stdio_common_vsprintf` into the global 0x3ff-byte buffer `0x1439e8240`, then calls `displayLableRotation_` with angle 0. Callable with just a font, coordinates and a format string. |
| `0x14016eb40` | **bitmap-font text renderer** `(font*, float x, float y, uint align, const char* text, float* out_width, float* out_height, ?, float angle)` [`displayLableRotation_`] | `align & 3`: 0 left, 1 right, 2 centre. `\n` and `@` start a new line. Glyph sprite pointers at `font + 8 + ch*8` (missing glyph falls back to `?`); advances at `font + 0x808 + ch*4` and `font + 0xc08 + ch*4`; scale fields at `font + 0x1008`, `0x100c`, `0x1010`, `0x101c`, spacing `0x1018`, base rotation `0x1014`. Draws each glyph immediately (`FUN_140172aa0`, sprite render), so it only produces output while the scene is being rendered. |
| `0x14016f120` | sets a field at `+0x1020` of the font and every glyph sprite (`setSpriteFields`) [`setfield_0x1020SideEffects?`] | called around the labels; probably colour/alpha, unverified |

Callers of `0x14016f290` include the editor (`0x1400d4380` region, `FUN_1400d6f70`) and HUD code: `displayAmountOfHPDMG?`, `displayCityOnMap`, `displayShortage`, `checkJammed?`, `renderEmpAmount?`, `FUN_14010a980`, `FUN_14014f370`, `FUN_1402fde80`. It is the game's general label call, so a mod can draw text natively by calling it from a hook that runs inside the render pass.

GUI classes seen (Ghidra namespaces `GUI`, `Panel`, `ObjectList`): base constructor `GUI::GUI_2` `0x14012a910` (0xe70 bytes), `Panel::Constructor` `0x14012b230`, `ObjectList::ObjectList` `0x14012b0d0`, a `List` constructor `0x14012b000`, `GUI::Load` `0x140163110`, `GUI::Relink` `0x140165f70`, `GUI::HandleClick` `0x14012d050`. Do not trust Ghidra's 3640-byte `GUI` struct: it is the 1.151 `Body` layout reused as a placeholder. `FindGuiElement` `0x1401a9170` is a plain string compare.

### What this changes
Option B is now realistic: **draw the hint with `0x14016f290` from a detour inside the render pass**, no overlay window. Still missing for it:
* **Which `font*` the editor passes.** The call at `0x1400d4cc4` takes it in `R14`; the assignments to `R14` in that function (`MOV R14,RAX` / `MOV R14,RDI` pairs, `LEA R14,[0x140353628]`) do not resolve it statically. Candidates are the font objects `Init_HGE` copies from the media array into `DAT_143a13958`..`DAT_143a13a58` after `LoadNameIntoMedia("myriad_15"/"myriad_10")`.
* **Which function to hook** so the call lands after the editor scene is drawn but before it ends, and what screen coordinate system `x`/`y` use (the editor passes values derived from `DAT_143a158fc` and `0x14035483c`/`0x140354854`).
* **Calling convention for the varargs:** Windows x64, so up to 4 register args, then stack; a plain `extern "C" fn(font, f32, f32, u32, *const c_char, ...)` from Rust needs the correct signature (floats in `xmm1`/`xmm2`, which is why the decompiler shows `edx`/`r8d` for the bit patterns).

### Live-test recipe (replaces step 2 above)
1. Log-only detour on `0x14016f290` (14-byte prologue check first): for each call while the editor is open, log `rcx` (font), `xmm1`, `xmm2`, `r9d` (align) and the format string. This resolves the font pointer and the coordinates in one run.
2. Then call `0x14016f290` once per frame from a hook on `SomethingVideoTask` exit (`0x140316e20`) with that font and a fixed position and check that the text appears in the editor and nowhere else.
