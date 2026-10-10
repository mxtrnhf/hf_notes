# The engine: HGE (Haaf's Game Engine)

The game is built on **HGE 1.8** (open source; stock copy in `~/Development/hge_src`, GitHub masonm12/HGE, with core source, helpers, and the tools). The game's build is **modified** (64-bit, extra log lines,
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

## Stock HGE formats used by the game [game files]
* `.res` scripts (`formats.md`): `Include/Texture/Animation/Sound/Font/Particle/...`, parsed by `RScriptParser` (source `src/helpers/parser.cpp`, `resources.cpp`).
* **Particles `Media/Prt/*.psi`: 144 files, every one exactly 128 bytes** = HGE's `hgeParticleSystemInfo`; editable with HGE's `particleed` (`tools/particleed`, source `src/particleed`).
* **Fonts `Media/Fnt/*.fnt`:** text `[HGEFONT]`, `Bitmap=...png`, `Char="x",x,y,w,h,pre,post` lines; HGE `fonted`/`fontconv`. 59 files.
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
