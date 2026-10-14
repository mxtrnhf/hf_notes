# The engine: HGE (Haaf's Game Engine)

The game is built on **HGE 1.8** (open source; stock copy in `~/Development_Highfleet/hge_src`, GitHub masonm12/HGE, with core source, helpers, and the tools). The game's build is **modified** (64-bit, extra log lines,
64-bit minizip) but keeps HGE's structure, which explains much of what we found by hand (`.res` scripts, `hge.log`, `.fnt`, `.psi`, BASS audio).

## Evidence [code, Ghidra on the dump]
| Finding | Where |
|---|---|
| HGE log strings (`HGE Started..`, `HGE version: %X.%X`, `Application: %s`, `Memory: ...`, `Can't load resource: %s`) | `System_Initiate` = `0x14017d5a0`; the game adds video-memory lines (`Texture memory`, `Local video memory`) |
| The HGE interface object is the global **`DAT_143a119e0`**, created in `Init_HGE` `FUN_1401ad080` with `FUN_14017ecc0(0x180)` (= `hgeCreate`); the game calls it through the vtable (e.g. `+0x110` = `Random_Float`) | `Init_HGE` |
| State numbers are stock: `HGE_ICON` 0x1a = `hf_project.ico`, `HGE_TITLE` 0x1b = "HIGHFLEET v.<ver>", `HGE_LOGFILE` 0x1d = `hge.log`; width/height/bpp = 0x11/0x12/0x13 | `Init_HGE` |
| Resource manager: `FUN_14016fd30(this, "Media/media.res")` (global `DAT_143a119e8`), then `Precache(3)` `FUN_140170a20`, fonts fetched by name (`myriad_15`, `myriad_10`) | `Init_HGE` |
| `Resource_Load` = **`0x140174850`**: upper-cases the path, `/` -> `\`, searches attached **zip packs** first (minizip64 is compiled in), else the file loader `0x140174380` (`MakePath`, `CreateFileA`, `malloc`, `ReadFile`) | decompiled |

## Interface table (`HGE_Impl` vtable at `0x1403672f0`, slot n at +8n) [code]
Same order as the stock header, except one System_ method is missing between slots 2-7 (Launch or Snapshot) and slot 17 holds an added "load file" method before `Resource_Load`.
| Slot | Address | Stock method | | Slot | Address | Stock method |
|---|---|---|---|---|---|---|
| 0 | `0x14017d360` | Release | | 19 | `0x140174840` | Resource_Free |
| 1 | `0x14017d5a0` | System_Initiate (log header) | | 20 | `0x1401744e0` | **Resource_AttachPack** |
| 2 / 3 | `0x14017dfd0` / `0x14017e080` | Shutdown / Start | | 21 / 22 | `0x140174c20` / `0x140174bd0` | RemovePack / RemoveAllPacks |
| 4 / 5 | `0x14017d3d0` / `0x14017dbd0` | GetErrorMessage / Log | | 23 | `0x140174b00` | Resource_MakePath |
| 7-11 | `0x14017dc60`...`0x14017de60` | SetStateBool/Func/Hwnd/Int/String (confirmed by `Init_HGE` calls) | | 24 / 25 | `0x1401745f0` / `0x1401746e0` | EnumFiles / EnumFolders |
| 12-16 | `0x14017d3e0`...`0x14017d560` | GetState... | | 26-31 | `0x140173720`... | Ini_Set/GetInt, Float, String |
| 17 | `0x140174380` | (added) file loader | | 32-34 | `0x140174350`, `0x140174320`, `0x1401742d0` | Random_Seed / Int / Float |
| 18 | **`0x140174850`** | **Resource_Load** | | 35.. | `0x140174310`... | Timer_*, Effect_*, Music_*, Stream_*, Channel_*, Input_*, Gfx_*, Target_*, Texture_* (order of `include/hge.h`) |

## Stock HGE formats used by the game [game]
* `.res` scripts (`formats.md`): `Include/Texture/Animation/Sound/Font/Particle/...`, parsed by `RScriptParser` (source `src/helpers/parser.cpp`, `resources.cpp`).
* **Particles `Media/Prt/*.psi`: 144 files, every one exactly 128 bytes** = HGE's `hgeParticleSystemInfo`; editable with HGE's `particleed` (`tools/particleed`, source `src/particleed`).
* **Fonts `Media/Fnt/*.fnt`:** text `[HGEFONT]`, `Bitmap=...png`, `Char="x",x,y,w,h,pre,post` lines; HGE `fonted`/`fontconv`. 59 `.fnt` files, 58 declared in `Media/Fnt/fonts.res` (`Font <name>` / `{ filename=Media\\Fnt\\<name>.fnt }`); all are ASCII `0x20`-`0x7E` only except three digit-only fonts; glyph bitmaps live in the texture atlases (`Media/Tex/Fnt1.res`, `Fnt2.res`). Full list and metrics: [rendering/fonts.md](rendering/fonts.md).
* Atlases are produced by `texasm` (`src/texasm`). Audio goes through BASS (the modloader proxies `bass.dll`).

## What does NOT go through HGE
* **Dialogue packs:** `load_dialog` (`FUN_1402253a0`) opens `Data/Dialogs/<lang>.seria_enc` with a C++ `ifstream` (open `FUN_1401a3be0`), logs `ERR: load_dialog failed to open file %s.` on failure, then decrypts with the LCG
  (seed `0x269ec3` = 2531011, step `0x343fd` = 214013, `b ^= (v >> 15) ^ v`), splits at `#` and drops `\n`: exactly what `hfcrypt.py` does.
* `.seria` libraries/saves are read by the game's own serializer (not traced; saved on exit by `FUN_14024e3e0`).

## Why it matters for mods (ideas, untested)
1. **Override media without touching game files:** `Resource_AttachPack` (slot 20) lets a DLL attach a zip whose files are found *before* the disk copies (names compared upper-cased, `/` = `\`), including `media.res` itself and every
   `.res` it includes. The attach must happen before `Init_HGE` parses `media.res`: hook `Resource_Load` and attach on its first call.
2. **First step before any hook:** a log-only detour on `Resource_Load` (`0x140174850`, the proven approach) listing every requested file at startup. That shows which assets really use the engine loader (textures, sounds, particles, fonts).
3. **Dialogue text:** needs a different seam (the `ifstream` open, or `CreateFileA/W`), since it bypasses HGE.
4. Authoring: the HGE tools (`particleed`, `fonted`, `texasm`) produce the formats the game reads.
5. The engine interface pointer `DAT_143a119e0` gives a mod direct access to `Gfx_*`, `Input_*`, `Timer_*` and the logger (`System_Log` writes to `hge.log`).

## The interface table in 1.151 (names from logdot's annotated program) [code]
1.151 has a named `HGEVFTABLE` struct (800 bytes = 100 slots, plus `HGE_Impl` 3,464 bytes and the `hge.h` / `hge.pdb` header types). 1.163 has none. Compared with the table above:

* **The 1.163 table is the 1.151 table plus one slot.** In 1.151 `Resource_Load` is slot 17 (`+0x88`) and `Resource_Free` slot 18; in 1.163 they are slots 18 and 19 with an extra "load file" method at 17
  (already noted above). So **the added file-loader slot is new in 1.163**; every slot at or after 17 is `+8` in 1.163, which is why `Random_Float` is `+0x108` in 1.151 and `+0x110` in 1.163,
  and the same `+8` applies to the Body vtable damage slot (`+0x208` -> `+0x210`) seen in map-air-groups.md (that one is a different vtable, but the same kind of change).
* **1.151 slot names** (stock HGE order, with the game's differences): 0 Release, 1 `System_Initiate`, 2 `System_Shutdown`, 3 `System_Start`, 4 *(unnamed: GetErrorMessage)*, 5 `System_Log`, 6 *(unnamed: one of
  Launch/Snapshot)*, 7-11 `System_SetStateBool/Func/(Hwnd)/Int/String`, 12-16 `GetState*`, 17 `Resource_Load`, 18 `Resource_Free`, 19 `AttachPack`, 20 `RemovePack`, 21 `RemoveAllPacks`, 22 `Resource_MakePath`,
  23 `EnumFiles`, 24 `EnumFolders`, 25-30 `SetInt/GetInt/SetFloat/GetFloat/SetString/GetString` (`Ini_*`), 31 `Random_Seed`, 32 `Random_Int`, 33 `Random_Float`, 34 `GetSeed`, 35 `GetTime`, 36 `GetDelta`,
  37 `GetFps`, 38 `EffectLoad`, 39 `EffectFree`, 40 `EffectPlay`, 41 `PlayEx`, 42 `StreamPlay`, 43 `MusicLoad`, 44 `MusicFree`, 55 `StreamLoad`, 56 `StreamFree`, 57-60 `ChannelUnknown`, 61-72 `Channel*` (`Pause`, `Resume`, `Stop`, `PauseAll`, `ResumeAll`, `StopAll`, `IsPlaying`, `GetLength`, `SetPos`, slot 70 unnamed, `SlideTo`, `IsSliding`), 77-87 input (`GetMousePos`,
  `SetMousePos`, `GetMoseWheel` [sic], `IsMouseOver`, `KeyDown`, `KeyUp`, `GetKeyState`, `GetKeyName`, `GetKey`, `GetChar`, `GetEvent`), 97 `showPoweredByHGE?`, 98/99 `GetSpriteWidth?`/`GetSpriteHeight?`
  (names with a question mark are logdot's guesses). The slots 45-54, 73-76 and 88-96 are unnamed in 1.151 (the stock header puts Gfx_/Target_/Texture_ there).
* **It narrows the open question** about which stock System_ method is missing: the table has **one** slot (6) between `System_Log` and `SetStateBool` where the stock header has two
  (`System_Launch`, `System_Snapshot`). Which one is still unnamed.
* All named slots match the HGE 1.8 header order, consistent with the notes' claim that the game uses a lightly modified stock HGE.
* Extra useful hook: `Resource_AttachPack` is slot 19 in 1.151 and **slot 20** in 1.163 (consistent with the table above).

## HGE helpers compiled into the exe [code]
The helper classes of stock HGE are in the game, found by matching offsets and logic against `hge_src/src/helpers` (details and offsets: [rendering/render-pipeline.md](rendering/render-pipeline.md)):

| Address | Stock counterpart |
|---|---|
| `0x14016eb40` | `hgeFont::Render` (modified: `@` line break, rotation argument, width/height outputs) |
| `0x14016f290` | `hgeFont::printf` |
| `0x14016f120` / `0x14016f0c0` | `hgeFont::SetColor` / `hgeFont::SetBlendMode` |
| `0x1401703e0` | `hgeResourceManager::GetFont` (`RES_FONT` = 9) |
| `0x140172aa0` / `0x1401725c0` | `hgeSprite::RenderEx` / `Render` [likely] |

The game added a renderer-like object at HGE slot `+0x2e8` (stored as `ArrayLoadedByMedia_res`, called by `Init_HGE`); [guess] it is the D3D11 renderer. The `.fnt` format described above stays valid: the font objects are plain `hgeFont` instances loaded from `Media/Fnt`.

## HGE_Impl input layout and slots 78-89 [code, bytes decoded by hand]
The tiny input functions are **not defined as functions in Ghidra** (the tool says "no function found"); the bytes were read from memory and decoded. `HGE` is the global `0x143a119e0`, the vtable is `HGEVFTABLE` `0x1403672f0`. Slots are +8 against 1.151 from slot 17 on.

| Slot | Address | Stock method | What it does |
|---|---|---|---|
| 78 | `0x140173870` | `Input_GetMousePos` | copies the floats at `HGE+0x9fc` (x) and `HGE+0xa00` (y) to the out pointers |
| 79 | `0x1401738d0` | `Input_SetMousePos` | floats to int, uses the `HWND` at `HGE+0x300` |
| 80 | `0x140173890` | `Input_GetMouseWheel` | int at `HGE+0x9f8` |
| 81 | `0x1401738a0` | `Input_IsMouseOver` | byte at `HGE+0xa04` |
| 82 | `0x1401738b0` | `Input_KeyDown(key)` | `byte[HGE+0xa06+key] & 1` |
| 83 | `0x1401738c0` | `Input_KeyUp(key)` | `(byte[HGE+0xa06+key] >> 1) & 1` |
| 84 | `0x140173850` | key state | calls a Win32 key-state API, returns bit 15 |
| 85 | `0x140173840` | `Input_GetKeyName` | pointer-table lookup |
| 86 | `0x140173830` | `Input_GetChar` | int at `HGE+0x9f0` |
| 87 / 88 | `0x1401737d0` / `0x1401737e0` | (not decoded) | |
| 89 | `0x14016cbe0` | (not decoded) | |

`GetClientCursorPos` `0x140173c40(HGE_Impl*)` is `GetCursorPos` + `ScreenToClient(HWND at +0x300)`, stores the floats at `+0x9fc/+0xa00` and clears `0x100` bytes at `+0xa06` (the key-state array). A search for `call [reg+0x290]` found one hit, a **Body** vtable call, so the game may read input through direct calls rather than the vtable [unknown]. The probe run saw the OS cursor pinned at client `(960,540)` ([runs/probe-run-1.md](runs/probe-run-1.md)): `HGE+0x9fc/0xa00` is what the HGE layer sees, the game's own virtual cursor is somewhere else [unknown].

## Resource getters [code]
`GetAnimation` `0x140170230`, `GetFont` `0x1401703e0`, `GetEffect` `0x1401702b0`, `GetTexture` `0x140170420`, `GetDistort?` `0x140170270`; all go through `CopyNameIntoMedia_` `0x140178950` with the stock resource-type enum. Images are `Animation` resources, details in [rendering/images-and-sprites.md](rendering/images-and-sprites.md).

## Input observations from probe run 2 [game] (2026-10-14)
* **Mouse wheel:** `HGE+0x9f8` (`Input_GetMouseWheel`) reads `-1` or `+1` per notch (53 events during editor palette scrolling) [game].
* **Mouse floats:** `HGE+0x9fc` / `+0xa00` showed only `-1`, `0`, `1` in the first run, but the probe rounded them to integers; whether they are relative deltas or something else is unknown until exact values are printed (probe v1.2) [guess].
* **SDL is only for joysticks:** the imports found are `SDL_Init`, `SDL_NumJoysticks`, `SDL_JoystickOpen`, `SDL_JoystickName`, `SDL_JoystickClose`, `SDL_PollEvent`, `SDL_Quit`. `InputTask` `0x14018dbf0` calls `SDL_PollEvent`, but there is no SDL mouse or keyboard path in this build [code]. The input-device manager destructor `FUN_140185ca0` (device table `DAT_1439e9388`, stride `0xf0`, SDL joysticks) is the only caller of the `ClipCursor` wrapper `0x14024c650`, which releases the clip at shutdown [code]; no `SetCursorPos` import was found by name.
* The Windows cursor stays at client `(960,540)` in a 2560x1440 client; the code that recentres it, and the game's virtual cursor, are not found yet [game+code]. `InputTask` callees: `FUN_1400bc5e0` (editor wheel), `140187100`, `140187260` (reads the held part), `140188300`, `140188570`, `140189ab0`, `140189fa0`, `14018a530`, `14018ac30`, `14018af40`, `14018b310`, `UpdateZoom` `0x14026af80` [code]. See [runs/probe-run-1.md](runs/probe-run-1.md).
