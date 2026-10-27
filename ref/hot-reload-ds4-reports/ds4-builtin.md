# Part C — built-in dev, debug and reload facilities (Highfleet 1.163)

Program: `Highfleet.exe.unpacked.exe v1.163` in Ghidra project `HighfleetServer`, image base `0x140000000`.
Read-only static analysis, no game run. Tags: `[code]` = read here at the cited address with the quoted
instruction/decompile line; `[notes]` = repo note, not re-checked; `[guess]` = inference plus what would confirm it.
Build shape: x86-64, MSVC, C++ with a small reflection/serialisation framework (`ISerializable`, typed `Property`
objects) and a per-frame task list (`PreTask`/`PhysicTask`/`InputTask`/`VideoTask`/`SoundTask`/`AITask`).

---

## 0. Answers first

The question behind this part: *what does the game itself already offer for development, debugging and — above all —
reloading data while it runs?*

| Item | What exists | Verdict for hot-reload |
|---|---|---|
| Level / scenario reload from disk | **yes**: `SetLevelSeriaToLoad_` 0x14025afd0 → `SomethingPreTask` 0x140286e40 → `reload_sg` 0x140240b90 → `LoadSeriaFile` → `Level::Load` | **feasible** (the engine's own scene-change path, 57 call sites; see §6.2/§6.3) |
| Localisation text reload | **yes**: `LoadDialogue` 0x1402253a0 clears the string table and re-reads `Data/Dialogs/*.seria_enc`; the options language button calls it live | **feasible** |
| Ship designs (`Ships/*.seria`, `Objects/Designs/*.seria`) | **yes, partly**: `get_filenames` 0x140212850 re-scans the folders every time the shipworks screen is built; editor entry re-reads `Libraries/parts.seria` | **feasible with caveats** |
| `Libraries/parts.seria` / editor libraries | **yes**: `loadSeriaForLibraries_` 0x1400d09a0 on editor entry; `PreLoadLibraries_` 0x140233710 loads everything but has one caller (`initGame`) | **feasible with caveats** |
| `Libraries/OL.seria` (object library) | read once in `PrepareMainLoop` 0x1401ad9c8; written by exit_game | **not feasible safely** without reference fix-up |
| `Config.ini` | read exactly once (`Main` 0x14027e976), written at init and exit; values are *live globals*, so individual settings can be poked at runtime | **feasible per key**, not as a file re-read |
| Mod DLL reload | nothing: no plugin interface, no runtime `LoadLibrary`, `FreeLibrary` only in `System_Shutdown` | **not feasible in-process** with today's loader |
| Mod JSON re-read | the exe has **no JSON at all** (0 strings matching `json`, no parser) — it neither helps nor hinders | mod-side, feasible |
| Console / cheat codes / `-dev` switches | none found | not available |
| Verbose logging | **yes**: `error.log` + `client.log`, level-gated by the live global `dbgLogMode`, Config key `DBG_LOG_DEPTH`, plus `DBG_SOUND`, plus a dead `DBG_DOGMODE` | usable today |
| File watching / auto-reload | none: no `ReadDirectoryChangesW` import; data is only read when a function is called | must be mod-driven |

The one-sentence version: *the game has no hot-reload feature, but it has three real reload primitives — the scene
loader, the dialogue loader and the shipworks/design re-scan — and all of them work by "clear, then read the file
again", which is exactly the shape a mod-side reload needs.*

---

## 1. Method and limits

* Every address below was read in this session in the v1.163 program. Where a claim rests only on a repo note it is
  tagged `[notes]`; where it rests on an inference it is tagged `[guess]` with the test that would settle it.
* The v1.151 program was not used for addresses.
* Function names in this program are partly machine-propagated from 1.151 and several are wrong
  (see §2.4, §7.1). Each named function used as evidence was opened and read.
* Big functions (`ClickFunc` 0x14012f120, `creatureLogic`, `SomethingWithLevelSerias` 0x1402ac970) were not
  decompiled whole; only individual call sites and small address windows were disassembled, as the rules require.

---

## 2. What the exe does *not* have (negative evidence, with the searches)

Negative results are only useful with the search list, so here it is.

### 2.1 No developer console, no cheat codes, no command line

* `search_strings` for `console`, `cheat`, `^dev`, `^debug$`, `god`, `dev_?mode`, `test_?mode`: **0 matches** each
  (case-insensitive, min length 3–4). The only `editor`/`EDITORMODE` hits are the ship editor (§5).
* The full import table (287 entries, paged through `list_imports`) contains **no `GetCommandLineA/W`,
  `CommandLineToArgvW`, `GetEnvironmentVariable`**. The only command-line-related symbol is the CRT's internal
  `_get_narrow_winmain_command_line` string. So there are no command-line switches to inspect. `[code]`
* No `printf`-style stdin loop, no `AllocConsole` in the exe (the black console window comes from the modloader,
  `[notes]` setup.md §Modloader).

### 2.2 No JSON

`search_strings "json"` (min length 4, case-insensitive): **0**; `nlohmann|rapidjson|jsoncpp|picojson`: **0**.
All game data is the custom text format `.seria` (plus `.seria_enc` for dialogs, plus `Config.ini`). `[code]`
Consequence: "re-read mod JSON while running" is purely a mod-side problem; the game has no loader to reuse, and
nothing in the exe will ever re-read a JSON file on its own.

### 2.3 No file watching

`ReadDirectoryChangesW`, `FindFirstChangeNotification`: **not imported**. Directory contents are read with
`FindFirstFileA`/`FindNextFileA` only when a function asks for them (see §6.6). So nothing in the game notices a
changed file by itself; every reload must be triggered by a call. `[code]`

### 2.4 No plugin/DLL lifecycle in the exe

* `FreeLibrary` is imported; the only analysed caller is `System_Shutdown` at 0x14017e021. `[code]`
* `LoadLibraryA`/`GetProcAddress` are imported, but Ghidra finds no named thunk and no call site for them
  (`search_functions "LoadLibrary"` → none; xrefs to the IAT entry `EXTERNAL:003bac44` → none). `[code]` for the
  absence of call sites, `[guess]` for the reason (they are probably used only by CRT/third-party init paths).
* The modloader itself (bass.dll proxy) does the loading; its README says mods are loaded from
  `Modloader/mods/*.dll` in directory order and the shared notes say the libraries are never unloaded
  (`mem::forget`) `[notes]` setup.md. The shipped loader binary does import `FreeLibrary`, `LoadLibraryA` and
  `LoadLibraryExW` (`objdump -p bass.dll`), so the loader *could* unload, but per the notes it does not. `[code]`
  for the imports, `[notes]` for the behaviour.
* Nothing in the game keeps a list of loaded modules, so there is no game-side hook a "swap the DLL" operation
  could hold on to.

---

## 3. Built-in logging (`error.log`, `client.log`) — the observability a reload feature needs

### 3.1 The two sinks

`InitializeLogs` 0x1401957d0 opens two ofstreams and says so:

```
  lVar2 = OpenFile_(&Error_logStream);   ...  "error.log"
  lVar2 = OpenFile_(&Client_logStream);  ...  "client.log"
  WriteToClientLog(0,1,"Errorlog initiated successful.\n");
  WriteToClientLog(0,2,"Clientlog initiated successful.\n");
```

`[code]` 0x1401957d0; file names from the string table: `error.log` @0x140368f90, `client.log` @0x140368fa0,
also `hge.log` @0x14036ae90. Which stream is which follows from the two init lines (mask 1 → "Errorlog
initiated", mask 2 → "Clientlog initiated"), so oStream1 = `error.log`, oStream2 = `client.log`. `@` on its own is
a separator marker: the writer sees `*param_3 == '@'` and emits a bare newline plus `flush` on the selected sinks.
`[code]` 0x140195c10.

### 3.2 `WriteToClientLog(level, sinks, fmt, ...)` 0x140195c10

Signature as recovered: `void WriteToClientLog(int level, ulonglong sinkMask, char *fmt, ...)`.
Behaviour read in the decompile and confirmed in disassembly:

```
  if (param_1 <= dbgLogMode) {
     if (*param_3 == '@') { newline+flush on the sinks selected by param_2 }
     else {
        __stdio_common_vsprintf(...)                       // format
        timestamp = HH:MM:SS.hh from _Xtime_get_ticks()    // floorf-based, 3 divisions
        if (param_2 & 1) write to oStream1 (error.log) + "\n" + flush
        if (param_2 & 2) write to oStream2 (client.log) + "\n" + flush
     }
  }
```

Branch polarity, straight from the disassembly at 0x140195c35:

```
140195c35: CMP ECX, dword ptr [0x1403c0e4c]     ; ECX = level argument
140195c3b: MOV RSI, R8
140195c3e: MOV EDI, EDX
140195c40: JG  0x140195f0a                      ; if level > dbgLogMode -> skip everything
```

So: **log if `level <= dbgLogMode`**, else print nothing. Two outcome sides stated: with `dbgLogMode = 1` all
`level 0` and `level 1` calls print (most `(1,2)` INFO lines and all `(0,3)` errors), and `level >= 2` calls are
silently dropped. `[code]`

### 3.3 `dbgLogMode` is a live Config.ini key: `DBG_LOG_DEPTH`

`InitializeAppProperties` (0x14023e000…) builds typed property objects that point **directly at globals**; for the
debug ones the code is literally:

```
14023e046: LEA RDX, [0x140371d90]      ; "DBG_LOG_DEPTH" (13 chars)
14023e04d: CALL 0x1400056e0            ; copy key name into the Property
14023e052: MOV EAX, dword ptr [0x1403c0e4c]
14023e058: MOV dword ptr [RDI + 0x38], EAX     ; current value
14023e05b: LEA RAX, [0x1403c0e4c]
14023e062: MOV qword ptr [RDI + 0x30], RAX     ; the Property points at the global
```

`[code]` 0x14023e04d–0x14023e062. `dbgLogMode` = 0x1403c0e4c, default value read from the image = **1**
(`01 00 00 00` at 0x1403c0e4c). Because the property points at the global, the *only* way to change it is to write
that global (or edit Config.ini and restart, see §4). `[code]`

### 3.4 The other two debug keys

Same mechanism, next two properties:

```
14023e0ac: LEA RDX, [0x140371da0]      ; "DBG_DOGMODE" (11 chars)
14023e0b8: MOVZX EAX, byte ptr [0x143a1193f]
...
14023e10c: LEA RDX, [0x140371db0]      ; "DBG_SOUND" (9 chars)
14023e118: MOVZX EAX, byte ptr [0x1403c0e22]
```

* `DBG_DOGMODE` → 0x143a1193f. The *only* code references to that byte are the two instructions above (binding and
  value read); `search_instructions` over the whole program for the operand returns 2 hits, both inside
  `InitializeAppProperties`. So the key is **dead** in 1.163: it is read from Config.ini and never used. `[code]`
* `DBG_SOUND` → 0x1403c0e22, default **1** (image byte). Its only consumer is the sound player
  `playSFXSound?` 0x1402e30e0:

```
1402e312b: CMP byte ptr [0x1403c0e22], 0x0
1402e3132: JZ  0x1402e3327          ; == 0 -> jump
...
1402e3327: MOVSS XMM0, dword ptr [0x1403524ec]   ; = -1.0f (0xbf800000)
1402e332f..1402e336d: restore registers, RET
```

  Both sides: `DBG_SOUND == 0` → the function returns `-1.0f` immediately, so **all SFX are skipped**;
  `DBG_SOUND != 0` → the normal mixing path runs. `[code]` This is a genuine built-in "mute everything for
  testing" switch, reachable only through Config.ini + restart or by writing the byte.

### 3.5 The CHECK/assert macro is still compiled in

`sprintf(local_b8,"CHECK ERROR: %s, %d", "D:\\!ESSENTIALS\\PROJECTS\\HYBRID FLEET 2013EX\\main.cpp", 0x9239)`
followed by `writeTimeToLog_(local_b8)` and `WriteToClientLog(0,3,...)` — read at 0x14024da1b inside
`FUN_14024d960`. `[code]` Sixteen source paths of the original project are in the binary (AircraftLogic.cpp,
Body.h, Body.cpp, Creature.cpp, D3DEngine.cpp, Editor.cpp, Escadra.cpp, FX.cpp, Gui.cpp, InputTask.cpp, Joint.cpp,
main.cpp, Profile.cpp, Level.cpp, VideoTask.cpp) and `writeTimeToLog_` 0x1400a0b10 prepends `"%H:%M:%S "` and
appends the line to a global linked list at 0x1403ef328. `[code]` That list is read by a small function at
0x14034bd00 (`MOV RBX, qword ptr [0x1403ef328]` at 0x14034bd0f) `[code]`; I did not find a UI that renders it, so
whether it is ever displayed is **not determined**.
Useful side effect for us: a failing CHECK writes original file + line into the game log, which makes hook debugging
much cheaper than blind patching.

### 3.6 What the logging is *not*

It is not a console: there is no input side, no command evaluation, and log lines cannot be typed. `[code]` (no
stdin/read loop in the writer, no console import). So no "dev console hotkey" exists to extend.

---

## 4. `Config.ini` — a property table, not a config file with a watcher

### 4.1 Read exactly once

`FUN_140224c60` is the reader:

```
  lVar3 = OpenFile_(&local_118,"Config.ini",1,0x40);
  ...
  (**(code **)(*globalAstruct + 0x18))(globalAstruct,local_128);   // Deserialize(stream)
  FUN_14018d3d0();
```

`[code]` 0x140224c60. It has exactly one caller: `Main` at 0x14027e976 (`get_function_xrefs`). `[code]`
So editing Config.ini while the game runs does nothing until the next start.

### 4.2 Written at init and at exit

The writer `FUN_14024d520` opens `Config.ini` for output and calls the object's `Serialize`
(`(**(code **)(*plVar1 + 0x10))(plVar1,&local_128)`); it is called from `initGame` (0x1401a94d0, near the end),
from `exit_game` 0x140211e10, and from the failure branch of `reload_sg`. `[code]`
Practical note for testing: the game rewrites `Config.ini` at start and exit, so a key you add by hand can be
normalised away — set it while the game is closed and read the file back after a run. `[code]` for the write paths,
`[guess]` for "normalised away" (the writer serialises its whole property list, so unknown keys are almost certainly
dropped; test: add `X=1`, run, exit, look at the file).

### 4.3 The schema (what a mod may poke live)

`InitializeAppProperties` binds each key to a global with a type-specific `Property` vtable
(`FPropertyVFTABLE` = float, `BPropertyVFTABLE` = byte/bool, `IPropertyVFTABLE` = int, `SPropertyVFTABLE` =
string). Keys read from the string table (0x140371b98…0x1403720f8) plus the bindings seen in the code:

`CORE_INIT_LEVEL` (string, default `Title.seria` — the embedded template at 0x1403719f0 says
`CORE_INIT_LEVEL=Title.seria`), `CORE_FRAMERATE` (float, 60.0), `CORE_USE_SLEEP`, `CORE_TIMEWRAP`,
`CORE_INIT_RI`, `CORE_SHOW_AUX`, `CORE_PROLOGUE_PASSED`, `CORE_LANGUAGE` (int; 1 = russian, 2 = english),
`CORE_SUBTEXT_TIMEOUT`, `CORE_MOUSE_OVERALL/WHEEL/MOUSE0..4/…_SPEED0..4/CORE_MOUSE_LAST`, `CORE_AIMING_MODE`,
`CORE_LAST_LOADED_VERSION`, `CORE_U2M`, `GFX_SCREENBPP`, `GFX_DSCREEN_WIDTH/HEIGHT`, `GFX_SCREEN_WIDTH/HEIGHT`,
`GFX_FRAME_WIDTH/HEIGHT`, `GFX_SCREEN_MODE`, `GFX_STRETCH_ON`, `GFX_DITHERING_ON`, `GFX_GLITCH_LEVEL`,
`GFX_QUALITY`, `GFX_BRIGHTNESS`, `GFX_FLASHES`, `GFX_SHADING_*` (16 entries), `PRESELECT_*`, `DBG_LOG_DEPTH`,
`DBG_DOGMODE`, `DBG_SOUND`. `[code]` for the names and for three bindings read in disassembly
(0x14023e052, 0x14023e0b8, 0x14023e118); the rest is `[code]` on the string table plus the one-key-one-property loop
shape of that function, but I did not individually verify every target address.

Two of these are directly useful for a reload study:
* `CORE_INIT_LEVEL` is the scenario loaded at start — proof that *the first level and every later level go through the
  same "load by name" mechanism* (§6.2, §6.3).
* `CORE_LAST_LOADED_VERSION` is compared against `GetGameVersionString()` inside `PreLoadLibraries_` to decide
  whether to migrate ship files (§6.7).

Because the property objects hold **pointers to the globals**, writing e.g. `*(float*)0x… = 30.0f` takes effect
immediately for any code that reads that global per frame; the file is irrelevant at that point. `[code]` for the
pointer binding, `[guess]` for "per frame" per key (must be checked per key; e.g. `GFX_SCREEN_MODE` is obviously
applied only when the device is recreated).

---

## 5. The ship editor / "shipworks" is the built-in developer mode

This is the closest thing the game has to a dev mode, and it is reachable at runtime from UI code and from level
scripts.

### 5.1 Entering: `FUN_1400beea0(inMenu, moveCamera, constructorMode)`

```
  IN_MENU_ = param_1;
  LOAD_CONSTRUCTOR_OR_EDITOR = param_3;
  if (!param_3) { if (param_1) { compData(); loadSeriaForLibraries_(); DefineEditorParts(); somethingShipworks_(); ... }
                  else { ... DefinePart(ALL_PARTS,"ITEM_HULL",...) 30+ times ...; DefineEditorParts(); DrawShopShipworksScreen_(); } }
  loadSeriaForLibraries_();
  DefineEditorParts();
  DrawShipworksScreen();
  ...
  if (DAT_147fc6fb6 != '\0') { DAT_147fc6fb6 = 0;  "<" Objects/Designs/Test/ + DAT_1403bd548 + ".seria" ... LoadSeriaFile(...) }
  ...
  IsInEditor = 1;
```

`[code]` 0x1400beea0 (`IsInEditor = 1` written at 0x1400c0173 via `MOV byte ptr [0x1403ef368],0x1`).
Note the third mode: a **test-design loader** that reads `Objects/Designs/Test/<name>.seria` when the flag
`DAT_147fc6fb6` is set — a leftover dev facility for iterating on one design. `[code]` for the path construction;
`[guess]` that it is only used by the editor's "test" entry (flag has no other writer found in a quick pass).

Callers (`get_function_xrefs`): `FUN_1402109d0` at 0x140210b90 and three sites inside the level-script interpreter
`SomethingWithLevelSerias` (0x1402b373e, 0x1402b381f, 0x1402b3911). `[code]`
→ a `*.seria` level file can put the game into the editor; so can our mods by calling 0x1400beea0 directly.

### 5.2 Leaving: `loadShipworks_` 0x1400d2260 — and it *writes* `parts.seria`

```
  if (PARTS_CONSTRUCTOR_SERIA != 0) {
    if (LOAD_CONSTRUCTOR_OR_EDITOR == 0) ISerializable_SerializeToFile(PARTS_CONSTRUCTOR_SERIA,"Libraries/parts.seria");
    (**(code **)(*PARTS_CONSTRUCTOR_SERIA + 0x48))();
  }
  ... free all editor libraries ...
  MakeGlobal_("EDITORMODE"); LocalFileReadAndUpdate("EDITORMODE");
  ...
  IsInEditor = 0;
```

`[code]` 0x1400d2260 (`IsInEditor = 0` at 0x1400d25bc, `MOV byte ptr [0x1403ef368],0x0`).
**This is the single most dangerous function for a "live part library edit" feature**: leaving the editor serialises
the in-memory library over `Libraries/parts.seria`. Any mod that injects parts into the library and then triggers an
editor round-trip will persist its injected parts to disk (or, worse, persist a broken library). It is also how the
game itself "saves" editor changes.

Callers: `ClickFunc` (0x140138060, 0x140138929), `FUN_140211220` (0x14021124b), `SomethingWithLevelSerias`
(0x1402b372b, 0x1402b38ef), and **`reload_sg` itself** (0x140240d3d, guarded by `if (IsInEditor != '\0')`). `[code]`

### 5.3 `loadSeriaForLibraries_` 0x1400d09a0 — a *runtime* re-read of `parts.seria`

```
  SetLink((Link *)&DAT_1403ef4f0, node);
  pcVar3 = "Libraries/parts.seria";
  if (LOAD_CONSTRUCTOR_OR_EDITOR != '\0') pcVar3 = "Libraries/constructor.seria";
  bVar1 = LoadSeriaFile(PARTS_CONSTRUCTOR_SERIA, pcVar3);
  if (bVar1) { copy class name "EDITOR_LIBRARY"/"CONSTRUCTOR_LIBRARY"; AssignRandomId(...,1); ... set part ids to 999 ... }
```

`[code]` 0x1400d09a0. Called from `FUN_1400beea0` at 0x1400beff5 and 0x1400bf2ea — i.e. **every time the editor is
entered, the library is re-read from disk**, replacing the previous `PARTS_CONSTRUCTOR_SERIA` object. So a
"reload parts.seria" operation already exists, with the caveat that it swaps a global out from under anything that
still points into the old library.

---

## 6. The reload primitives, one by one

### 6.1 The core: `LoadSeriaFile` always hits the disk

```
bool __fastcall LoadSeriaFile(ISerializable *container, char *pathToSeria)
{
  ... std::istream on GlobalStreamBuf ...
  lVar3 = OpenFile_(&local_118,pathToSeria,1,0x40);
  if (file != (FILE *)0x0) {
    cVar1 = (*(code *)container->vfTable->Desearialzie)(container,local_128);
    if (cVar1 != '\0') { ... bVar4 = true; goto ...; }
    ...
  }
  return bVar4;      // false if open or deserialize failed
}
```

`[code]` 0x140225930. There is **no cache, no name→object map, no mtime check**: every call opens the path and
deserialises into the container. Consequence: any "reload" is only a matter of calling the right loader with the
right container; nothing remembers the old file content. (The decompiler shows a stray `fwrite` in the read path —
that is a stream-buffer artefact of the inlined `std::istream` teardown, not a write; the open flags are read-mode
`1`.) `[code]` for the open call and the Deserialize call, `[guess]` for the `fwrite` artefact reading.

### 6.2 `reload_sg` 0x140240b90 — full level reload (teardown + disk read + rebuild)

Signature as recovered: `char reload_sg(char *levelName)` (returns non-zero on success; see §9.3).
Sequence, quoted from the decompile:

```
  WriteToClientLog(1,2,"APP::reload_sg initiated with %s.",param_1);
  loopVarLessThan15000 = 0;                       // clear the active-body table count
  free(someKindOfFileIO_ list); FUN_1401bc280();
  _TARGET_SCREEN_X_ = 0; ZOOM_LEVEL = 3; MIN_ZOOM_LEVEL = 0; MAX_ZOOM_LEVEL = 4;
  _FAST_SHAKE_X = 0; SLOW_SHAKE_X = 0;  ... a dozen scalar globals reset ...
  clear two intrusive lists (someKindOfFileIO_, DAT_143a15a50)
  mouseTrackSelected_ = 1; ...
  if (IsInEditor != '\0') { loadShipworks_(); }
  ... if current seria is Map.seria/Title.seria -> somethingAddMapMark_(profile) ...
  local_60.ptr = (char *)0x76654c2f61746144;   // "Data/Lev"
  local_60._8_4_ = 0x2f736c65;                 // "els/"      => "Data/Levels/"
  <append levelName>
  bVar2 = LoadSeriaFile(LevelSingleton,(char *)uVar7);
  if (bVar2) {
     WriteToClientLog(1,2,"LEVEL reload successful with %s.",uVar7);
     Level::Load();                                    // 0x1402d4270
     displayTextOnCreature_(...);
     DAT_143a11963 = 1;
     CopyString(&DAT_1403c13b0,param_1,...);            // remember "current level name"
     if (name == "Map.seria") { purge profile entries with duration > 0.0 }
     (**(code **)(*HGE + 0x100))(HGE, ms_since_start);  // timer/clock reset
     ...
     WriteToClientLog(1,2,"APP::reload_sg finished successfull with %s.",param_1);
  }
  else {
     WriteToClientLog(0,3,"ERR: reload_sg failed, for %s",uVar7);
     CopyString(&SeriaToLoad,"",0);
     WriteToClientLog(1,2,"APP::exit_game initiated.");
     ISerializable_SerializeToFile(ObjectsLibrarySingleton,"Libraries/OL.seria");
     FUN_14024d520();                                   // write Config.ini
     DAT_143a11901 = 1;                                 // quit flag
     WriteToClientLog(1,2,"APP::exit_game finished successful.");
  }
```

`[code]` 0x140240b90 (body 0x140240b90–0x1402410a8). Two things matter enormously for us:

1. **The level file is re-read from `Data/Levels/<name>` on every call.** A mod that wants "reload the game's level
   data" does not need to reimplement anything: it asks for the current level name again and the engine rebuilds the
   scene from the file on disk. `[guess]` (from the 57 call sites in §6.3) this is also what the game does on a
   city→map or map→battle transition, so *mods already have to survive this*: any mod state that cannot survive a
   scene transition is already broken today. Test: log `SeriaToLoad` at each `reload_sg` entry during normal play.
2. **On failure the game quits**: it writes `Libraries/OL.seria` and `Config.ini`, sets the quit flag, and the frame
   loop ends. So a hotkey that asks for a non-existent level name is a "quit the game and rewrite two libraries"
   button. Any mod-side reload must validate the name (or read `DAT_1403c13b0`, §6.3) before calling.

`Level::Load` 0x1402d4270 is small and worth quoting in full, because it shows what "the level is loaded" means:

```
bool Level::Load(void)
{
  if ((GlobalNode_ != 0) && ((**(code **)(*GlobalNode_ + 0x88))() == 0)) return false;
  if ((GlobalNodeElectricBoogaloo != 0) && ((**(code **)(*GlobalNodeElectricBoogaloo + 0x88))() == 0)) return false;
  _lvlHighX = _lvlHighXHighY; ... (level bounds reset to the sentinel)
  DAT_147fc6f98 = loadMediaByName_(Media_res, levelNameString);
  WriteToClientLog(1,2,"LEVEL::load finished successful.");
  return true;
}
```

`[code]` 0x1402d4270. i.e. the deserialised scene graph is asked to `Load()` itself, and the background media for the
level is (re)loaded by name.

### 6.3 `SetLevelSeriaToLoad_` 0x14025afd0 and the global `SeriaToLoad` — the request API

```
  CopyString((longlong **)&SeriaToLoad,param_1,plVar7);
  DAT_143a11903 = param_2;
  DAT_143a11908 = param_3;
  ... if (IS_IN_CAMPAIGN_ || BOOL_147fc6fd2) { DAT_143a1190c = ZOOM_LEVEL; MakeGlobal_(DAT_1439e9388,1); }
  ... if (name is "Map.seria" or "City_generated.seria") build the loading screen GUI ...
  DAT_147fc6fb3 = 0; loadAircraftMaps_ = 1;
  FUN_1402db350(name); FUN_14000e430(); FUN_1402e4b50();
```

`[code]` 0x14025afd0. `SeriaToLoad` is a `std::string` at 0x1403c1390 (size at +0x10 = 0x1403c13a0, capacity at
+0x18 = 0x1403c13a8; verified against the `CopyString` helper's layout and the `0xf` capacity comparisons).
`DAT_143a11903`/`DAT_143a11908` are the two flag bytes the caller supplies; they are cleared after the load.
There are **57 code call sites** (the xref query returned 58 references in total, one of them a data label, with a
limit of 60, so the list is complete), among them 11 inside `ClickFunc`, 10 at named sites inside
`SomethingWithLevelSerias`, 3 in `UpdateStrategicFleet`, and calls from `creatureLogic`, `LoadCity?`,
`mainDialogWithChoices`, `precombatOk`, `creditsScreen?`, `UpdateMapAircraftGroup`. `[code]` for the xref list.
This is *the* generic "go to this scene" entry point.

### 6.4 `SomethingPreTask` 0x140286e40 — the per-frame consumer

```
  if (DAT_1403c2b11 != '\0') {
    WriteToClientLog(2,2,9,"PreTask");
    if (DAT_1403c13a0 != 0) {                       // std::string::size(SeriaToLoad) != 0
      if (size == 4 && *(int*)SeriaToLoad == 'exit') { clear; exit_game(); return; }
      ...
      cVar5 = FUN_140240b90(SeriaToLoad.data());    // = reload_sg
      if (cVar5 == '\0') { exit_game(); }            // 0x140211e10
      CopyString(&SeriaToLoad,"",0);
      DAT_143a11903 = 0; DAT_143a11908 = 0;
    }
    ... then the normal per-frame work (BreakUpFrame for dead bodies, CollectDeadNodes,
        Creature_RecalcStatsPass, ...)
```

`[code]` 0x140286e40, call at 0x140286f2a; the "exit" test is `size == 4 && *(int*)ptr == 0x74697865`
("exit" little-endian). Called from `!FrameFunc` 0x1401a8eb8. `[code]`
`DAT_1403c2b11` is the gate byte at 0x1403c2b11: **1 in the image and never written** (`get_xrefs_to` on
0x1403c2b11 → one READ at 0x140286e44; `search_instructions` for `1403c2b1` shows writers for 0x1403c2b10 only, at
0x140269cc5 `=1` and 0x14023270f `=0`). So the block runs every time `SomethingPreTask` is called. `[code]`

Two consequences:
* the trigger is simply "`SeriaToLoad` is non-empty at the start of the frame" — a mod can write the string itself or
  call `SetLevelSeriaToLoad_`;
* it runs at the *start* of the frame, before the world update, which is the safe point: the previous frame's scene
  is finished but nothing of the new frame is built yet.

`initGame` 0x1401a94d0 uses exactly this: `CopyString(&SeriaToLoad, CORE_INIT_LEVEL); PreLoadLibraries_(); ...`
`[code]` (first statements of `initGame`), so the starting scenario and a later reload are literally the same
pipeline.

### 6.5 `PreLoadLibraries_` 0x140233710 — "reload all libraries + all objects + all ships" in one call

What it loads, in order `[code]`:

1. `Libraries/parts.seria` into `ALL_PARTS`, class name `LIB_EDITOR`; on failure
   `LogFatalError("ERR: Preload_libraries was unable to load LIB_EDITOR.")` and an early, unclean return.
2. `Objects/Town/*` into `LIB_TOWN` (0x143a13a08) — the folder name is built by concatenating `"Objects/Town"`
   (0x14036be08, referenced at 0x1402338a6/0x140233942) with each enumerated name, then `LoadSeriaFile`.
3. `Objects/Land/*` (→ `LIB_GROUND` 0x143a13a28), `Objects/Rock/*` (→ `LIB_ROCK` 0x143a13a40),
   `Objects/Docs/*` (→ `LIB_DOCS` 0x143a13a50) — same pattern, four folder/library pairs in all.
4. `LIB_SHIPS` (global `newNode_`), then a loop that loads each enumerated name via 0x1401b08a0; the code mentions
   both `Objects/Designs` and `Ships` around this loop (the decompiler renders the two folder lists as `memcmp`
   artefacts, so which list feeds which global is `[guess]`: the folder scan in §6.6 reads exactly these two).
5. Version check: compare `GetGameVersionString()` with the saved `CORE_LAST_LOADED_VERSION`; if different
   → `loadShipBackups_()` and `DAT_143a11920 = 1`.

`get_function_xrefs` → **one caller only**, `initGame` at 0x1401a9538. `[code]`

Verdict: this is the closest thing to a "reload all game data" button, and it leaks (it overwrites the six global
library pointers with new nodes and never frees the old ones) and it gives no guarantee about objects that already
hold `Part*`/`Body*` pointers into the old libraries. Calling it mid-battle would be reckless; calling it at a scene
boundary (right after `reload_sg` emptied the body table) is plausible but untested. That is a `[guess]` with a clear
test: call it from a hook immediately after `Level::Load` and see whether the next scene builds.

### 6.6 `get_filenames` 0x140212850 — the folder re-scan behind the shipworks screen

```
  GetCurrentDirectoryA(0x104, saved);
  if (SetCurrentDirectoryA("Objects/Designs")) {
      h = FindFirstFileA("*", &fd); FindNextFileA(h,&fd);          // skip "."
      if (FindNextFileA(h,&fd)) { do { copy fd.cFileName } while (FindNextFileA(h,&fd)); }  // skip ".."
      FindClose(h); SetCurrentDirectoryA(saved);
  } else WriteToClientLog(0,3,"ERR: get_filenames failed with %s.","Objects/Designs");
  ... same block for "Ships" ...
  ... keep only names ending in ".seria" (memcmp against ".seria"), strip the extension,
      insert into a std::set-like tree (DAT_143a1c220) and append new names to the caller's vector via CopyEscadraName ...
```

`[code]` 0x140212850. Callers: `DrawShipworksScreen` 0x1400c3f70 (0x1400c5345), `somethingShipworks?` 0x1400c7400
(0x1400d05c2), `ClickFunc` (three sites), `FUN_14024d960` (0x14024e2d2). `[code]`
So **the design list is rebuilt from the folder every time the screen is drawn** — dropping a new `.seria` into
`Ships/` shows up without a restart as soon as the shipworks/design screen is opened again. That is a working
hot-reload for ship designs today, with no mod at all (only the *design list*; the individual designs are loaded
when used). Caveats: it `SetCurrentDirectoryA`s the process (global state, and a race with any other file I/O
thread); it also only logs a line when a folder is missing.

### 6.7 Version-based ship migration: `loadShipBackups_` 0x14023cd00

Referenced from `PreLoadLibraries_` (0x140234903) and by the string `Ships_backup/` (0x140370c30). `[code]` for both.
`[guess]`: it is the "the game version changed, restore/migrate the player's `Ships/*.seria` from
`Ships_backup/`" helper. This is the game's own precedent for *automatically re-reading and rewriting* player data
at a version boundary — relevant if a mod ever needs to migrate its own data files.

### 6.8 Localisation: `LoadDialogue` 0x1402253a0 — a real, safe, in-place reload

```
  rep_140184060_API_MS_WIN_CRT_HEAP_L1_1_0_DLL__free(&DAT_143a1c3a0);       // frees/replaces the previous table object
  local_68.ptr = (char *)0x6169442f61746144;   // "Data/Dia"
  local_68._8_4_ = 0x73676f6c;                 // "logs"     => "Data/Dialogs/"
  if (coreLanguage == 1)      pcVar14 = "russian.seria_enc";
  else if (coreLanguage == 2) pcVar14 = "english.seria_enc";
  else                        goto LAB_14022546c;   // "any other val is error"
  ... open, seekg/tellg, read the whole file into a buffer ...
  ... parse lines into the table ...
```

`[code]` 0x1402253a0. Callers: `PrepareMainLoop` 0x1401ad95b (startup) and `ClickFunc` 0x140131b11 (the language
option) — **two, nothing else**. `[code]`
The language handler is worth quoting because it is the whole hot-reload in five instructions:

```
140131af8: MOV EAX, dword ptr [0x1403c0e1c]    ; coreLanguage
140131afe: INC EAX
140131b00: MOV EDI, 1
140131b05: CMP EAX, 2
140131b08: CMOVG EAX, EDI                      ; wrap: >2 -> 1
140131b0b: MOV dword ptr [0x1403c0e1c], EAX
140131b11: CALL 0x1402253a0                    ; LoadDialogue -> re-read the file from disk, rebuild the table
```

`[code]` 0x140131af8–0x140131b11. So clicking "language" in the options **re-reads the localisation file at runtime**
and swaps the table. This is the cleanest existing proof that "clear container → read file → rebuild" is safe in this
engine, and the template a mod-side reload should copy.
Two details: the dialog files are `*.seria_enc` (encoded, not plain text), and `russian` = 1 / `english` = 2 with the
default `CORE_LANGUAGE=2` (Config template at 0x140371a10). `[code]`

### 6.9 What is *not* reloadable (and what that costs)

* `Libraries/OL.seria` — the object library. Read once:
  `1401ad9c8: LEA RDX,[0x14036ae10] ("Libraries/OL.seria"); MOV RCX,[0x143a1c428]; CALL 0x140225930` inside
  `PrepareMainLoop`. `[code]` It is *written* by `exit_game` (`ISerializable_SerializeToFile(ObjectsLibrarySingleton,"Libraries/OL.seria")`,
  `[code]` 0x140211e10) and by `reload_sg`'s failure branch. Re-reading it into the same singleton would replace the
  class definitions every live object was built from, with no fix-up pass anywhere in the program (no function
  iterates live objects to remap definitions). → **not feasible** without a purpose-built fix-up. `[guess]` for the
  absence of a remap pass (searched for callers of the OL load outside `PrepareMainLoop`/exit paths: none).
* Media/textures (`loadMediaByName_`) — per-name loads happen at level load (`Level::Load` reloads the level's
  background media by name), but I did not map the media cache; a texture reload is **not determined**.
* Fonts/GUI — not investigated (out of scope for reload of mods).
* `Config.ini` — see §4: single read.

---

## 7. Traps found (names/claims that would mislead the next reader)

### 7.1 Names that are wrong

* `LocalFileReadAndUpdate` 0x140269b60 — despite the name it is *not* a file watcher. It manipulates the
  `someKindOfFileIO_` list (removes one entry), sets `fileRead_ = 1`, `QWORD_1403bd00c = 1`, `doRecoil_global = 0`,
  then calls `FUN_140006d70(path)`. `[code]` Do not build a reload design on this name.
* `SomethingPreTask`/`SomethingPhysicTask`/… are unnamed original classes (`*Task` singletons created by
  `CreatePreTaskSingleton` etc.). The names carry no semantics; use the addresses.
* `rep_1401f68c0_KERNEL32.DLL::FindNextFileA` at 0x140212850 is really `get_filenames` (the doc-folder scanner), not
  a thin import wrapper. `[code]`
* `Level::Load` exists as a symbol in the decompiler but `search_functions "Level::"` finds nothing; the real entry is
  the plain `Load` at 0x1402d4270. `[code]`

### 7.2 Structural traps

* **`reload_sg` failure = quit + disk writes.** Covered in §6.2. A "reload" hotkey must never pass a name it has not
  seen loaded.
* **`loadShipworks_` writes `Libraries/parts.seria`.** Covered in §5.2. Triggering an editor round-trip to "reload
  parts" also *saves* whatever is in memory.
* **`get_filenames` changes the process CWD** and restores it; it is not thread-safe against other file I/O.
* **`PreLoadLibraries_` overwrites globals without freeing** (leak) and has one caller (init).
* `SomethingPreTask`'s gate byte 0x1403c2b11 is a constant 1 with no writer; do not treat it as a runtime toggle.
  `[code]`

---

## 8. Verdicts per hot-reload idea, with risks

### 8.1 (a) Hot-swap a mod DLL — **not feasible in-process**

Facts: the exe has no module list, no plugin loader, no runtime `LoadLibrary` (only `FreeLibrary` in
`System_Shutdown`); the loader loads mods once from `Modloader/mods` and, per the notes, never unloads them;
our mods' hooks live *inside* the mod DLL (14-byte entry detours whose trampolines are allocated and written by the
mod, `[notes]` hooks.md). A `FreeLibrary` on a mod that owns even one installed detour would leave the game jumping
into freed pages within one frame.
Verdict: with today's loader, "swap the DLL while the game runs" is a crash generator. The workable shapes are:
(i) restart-only (what exists), (ii) move the code that game code jumps to into a **non-unloadable shim DLL** that
owns all trampolines and calls into a reloadable payload with function pointers — a real but substantial design
change, and it needs every mod's patch sites to go through the shim (this is part A/B territory).
What the game contributes: nothing (no unload callback, no module registry). The only useful game-side fact is that
it unloads nothing at runtime, so a "never unload anything" design is consistent with the host.

### 8.2 (b) Re-read mod JSON configs — **feasible** (mod-side, cheap)

The game has no JSON and no config watcher, so nothing can be reused and nothing gets in the way. The engine's own
precedent (§6.8) shows the safe pattern: clear the container, read the file, rebuild the derived state, swap the
pointer at a frame boundary. For a mod, the extra work is not the parsing but the **re-application of values that
were baked into code**: immediates patched by `patchy` (`[notes]` hooks.md table), operand repoints to private
floats, etc. Those need either (i) a "poked float" cell the patched instruction reads (operand repoint to a mod-owned
float — already the technique used by the refuel mod), so a config change is just a store, or (ii) a re-patch pass.
Recommendation: make every tunable a float/int in the mod's data section and repoint the instruction once; then a
JSON re-read is a store loop and cannot fail mid-frame.
Risks: a torn read (file being written while read) — read into a temp buffer, parse, then swap; and features that
allocate/register something at patch time (e.g. GUI elements) need their own teardown, which the game does not
provide.

### 8.3 (c) Re-read the game's own data files — **feasible for three of them, with caveats**

| Data | How | Caveat |
|---|---|---|
| `Data/Levels/<level>.seria` | `SetLevelSeriaToLoad_(name)` (or write `SeriaToLoad`) → rebuild at next frame | full scene restart; failure quits & rewrites libraries; mods must re-init their per-scene state (they must already, for city/battle transitions) |
| `Data/Dialogs/<lang>.seria_enc` | `LoadDialogue()` | encoded file format; table swapped in place; safest of all |
| `Ships/*.seria`, `Objects/Designs/*.seria` | open the shipworks/design screen (rescan), or call `get_filenames` 0x140212850 | list only; CWD churn |
| `Libraries/parts.seria` | editor round-trip (`loadSeriaForLibraries_`) | `loadShipworks_` **writes back** on exit; live ships may hold old part pointers |
| all libraries at once | `PreLoadLibraries_` | init-only by design; leaks; no reference fix-up |
| `Libraries/OL.seria` | no safe path | live objects reference the old definitions |
| `Config.ini` | not re-read; write the bound global instead | only per key; device-level keys need a recreate |

Practical recommendation for the user's goal (c): ship a mod-side "reload current scene" hotkey that (1) reads the
last loaded level name from the global `DAT_1403c13b0` (written by `reload_sg` after a successful load), (2) validates
the corresponding `Data/Levels/<name>` exists, and (3) calls `SetLevelSeriaToLoad_` with it at a frame boundary.
That gives "re-read the game's level data" with no reverse engineering of the scene graph at all.

---

## 9. Operation ledger (conditions, so polarity cannot drift)

### 9.1 Log gate

`if (level <= dbgLogMode)` → print, else nothing.
Disasm 0x140195c35 `CMP ECX,[0x1403c0e4c]` / 0x140195c40 `JG 0x140195f0a` (skip). `[code]`
`dbgLogMode` default = 1, Config key `DBG_LOG_DEPTH`.

### 9.2 Reload trigger

`SomethingPreTask`: `if (byte 0x1403c2b11 != 0)` (constant 1) and `if (*(size_t*)0x1403c13a0 != 0)` → reload.
Name `"exit"` (length 4, dword `0x74697865`) → exit_game instead. `[code]`

### 9.3 `reload_sg` return value

`XOR BL,BL` at 0x140240edf (failure path) and `MOV BL,0x1` at 0x140241034 (success path), returned via
`MOVZX EAX,BL` at 0x140241074. The branch at 0x140240e54–0x140240e5f:

```
140240e54: CALL 0x140225930        ; LoadSeriaFile(LevelSingleton, "Data/Levels/<name>")
140240e59: LEA  R9, [RBP + -0x1]
140240e5d: TEST AL, AL
140240e5f: JNZ  0x140240ee6        ; AL != 0 -> success block (log "LEVEL reload successful", CALL Level::Load)
                                   ; AL == 0 -> fall through to "ERR: reload_sg failed" + exit_game
```

Note the physical layout is failure-first, success-second: `0x140240e65–0x140240ee1` is the failure block
(`SerializeToFile OL.seria` at 0x140240eba, `Config.ini` write at 0x140240ebf, quit flag `[0x143a11901]=1` at
0x140240ec4), and `0x140240ee6` onward is the success block (`CALL 0x1402d4270` = `Level::Load` at 0x140240f04).
Caller: `if (ret == 0) exit_game()`. `[code]`

### 9.4 Sound gate

`if (byte[0x1403c0e22] == 0) → return -1.0f` (skip), else play. `[code]` 0x1402e312b / 0x1402e3132.

### 9.5 `IsInEditor`

Set 1 at the end of `FUN_1400beea0` (0x1400c0173); set 0 in `loadShipworks_` (0x1400d25bc). Tested in `reload_sg`:

```
140240d34: CMP byte ptr [0x1403ef368], R13B     ; R13B = 0 here
140240d3b: JZ  0x140240d42                      ; IsInEditor == 0 -> skip
140240d3d: CALL 0x1400d2260                     ; loadShipworks_()
```

i.e. leaving the editor is a *precondition* of a level reload, and the game does it for you. `[code]` for the writes,
the test and the call; 112 read sites from `list_globals` (`xrefs=112`).

### 9.6 Language cycle

`coreLanguage = (coreLanguage + 1 > 2) ? 1 : coreLanguage + 1`; 1 = russian, 2 = english; anything else is an error
branch in `LoadDialogue`. `[code]` 0x140131af8–0x140131b08 and 0x1402253a0.

### 9.7 Library version migration

`if (GetGameVersionString() == CORE_LAST_LOADED_VERSION) bVar3 = false; else bVar3 = true;` then
`if (bVar3) { loadShipBackups_(); DAT_143a11920 = 1; }` inside `PreLoadLibraries_`. `[code]` ~0x1402348c0–0x140234940.

---

## 10. Proposed minimal experiments (for the user to run later; not run here)

Ordered by information per unit of risk. Every one is reversible; none requires rebuilding a mod for step 1–2.

**E1 — confirm the log gate and get verbose logs (5 min, zero risk).**
With the game closed, set `DBG_LOG_DEPTH=3` in `Config.ini`, start, play one city transition, quit. Compare
`client.log` line count/contents with a run at the default 1; then read `Config.ini` back to see whether the key
survived. Confirms §3.3/§4.2 and gives a much more verbose log for everything else. (If the key is dropped by the
writer, that also confirms §4.2's normalisation.)

**E2 — prove the scene reload path from a mod (30 min, low risk).**
A log-only mod with a hotkey: log the string at 0x1403c13b0 (the current level name; written by `reload_sg` on
success at 0x140240f38 and cleared by `FUN_14034d320` at 0x14034d377), then call `SetLevelSeriaToLoad_(name, 0, 0)`
with that exact name. Expect `APP::reload_sg initiated with Map.seria.` / `LEVEL reload successful with Map.seria.` /
`APP::reload_sg finished successfull` in `client.log` and the loading screen. Do it while standing on the strategic
map, not mid-battle. Cancels the experiment if the name is empty (never loaded through `reload_sg` in that session).

**E3 — prove a data file is re-read from disk (15 min, no code).**
Copy `Ships/<adesign>.seria` to a new name (e.g. `ZZ_TEST.seria`) inside the game folder, open the design/shipworks
screen, check whether `ZZ_TEST` appears in the list without a restart. This tests `get_filenames` (§6.6) and therefore
whether any "new content file" hot-reload is possible at all. Then delete the file and re-open.

**E4 — prove the in-place reload pattern is safe to repeat (30 min, low risk).**
Hook `LoadDialogue` 0x1402253a0 (5 bytes to protect; `hf_probe` already hooks neighbours) and call it twice in a row
from your hook after a normal language switch, logging before/after. If the string table survives two rebuilds and
the UI still renders text, the "clear container → re-read → rebuild" pattern (§6.8) is confirmed as the model for
mod-side JSON reloads. Watch the log for `ERR: load_dialog failed to open file` — that is the failure side.

**E5 — only if E2 works: measure the cost/risk envelope of `PreLoadLibraries_` (1 h, medium risk).**
Call it once from a hook immediately after a successful `Level::Load` (i.e. at a scene boundary), in a disposable
save, and check (i) whether the next scene builds, (ii) whether memory grows, (iii) whether loaded ships still fly.
Do not call it mid-battle. This decides whether "reload all libraries" is a usable feature or only a crash.

**Explicitly not proposed:** calling `FreeLibrary` on a mod, or re-reading `Libraries/OL.seria` — both have no safe
path in this program (see §8.1, §6.9).

---

## 11. Not determined

* Whether `DAT_147fc6fb6` (the `Objects/Designs/Test/<name>.seria` loader flag) can be set from a data file — the
  writers of that byte were not enumerated.
* Whether the in-memory log list at 0x1403ef328 is ever rendered on screen (the small reader at 0x14034bd00 was not
  followed to a UI).
* Exact media/texture cache behaviour of `loadMediaByName_` (out of scope; `Level::Load` reloads one media by name
  per level).
* The precise meaning of the two flag arguments of `SetLevelSeriaToLoad_` (`DAT_143a11903`, `DAT_143a11908`): both are
  stored and cleared, both are read only in `SomethingPreTask`, and the byte `DAT_143a11908` gates a `free` of
  `DAT_1403c13b0` — the full consequence was not traced.
* `loadShipBackups_`'s actual file operations (only inferred from the `Ships_backup/` string and the version test).
* Whether the `Ships`/`Objects/Designs` scans are also used to *load* at startup (the load calls exist in
  `PreLoadLibraries_`, but which of the two folder lists feeds which global was not fully traced through the
  decompiler's inlined vector loops).
* 1.151 equivalents were not compared (addresses here are 1.163 only).

---

## 12. Checked twice

Re-opened the claims that the whole report leans on, re-reading each cited site a second time and comparing
against the rule checklist (missing sqrt/abs/clamp, condition polarity, right base object, invented constant):

1. **`LoadSeriaFile` has no cache and always opens the path** — re-read 0x140225930 a second time: the only I/O is
   `OpenFile_(&local_118, pathToSeria, 1, 0x40)` followed by `container->vfTable->Desearialzie(container, …)`; no
   static map, no name comparison, no early return before the open. **Held.** (The stray `fwrite` in the decompile
   was re-examined: it is part of the inlined `std::istream`/streambuf teardown after the deserialize, on the same
   `local_98` handle; there is no write to `pathToSeria`.)

2. **The reload trigger is "non-empty `SeriaToLoad`", not the flag byte** — re-read `SomethingPreTask` 0x140286e40 and
   the disassembly at 0x140286e44/0x140286f2a: `CMP byte ptr [0x1403c2b11],0` (image value 1, no writer) then
   `if (DAT_1403c13a0 != 0)` where 0x1403c13a8 is compared against `0xf` elsewhere ⇒ 0x1403c13a0 is the std::string
   *size* of the string whose buffer starts at 0x1403c1390. Polarity checked both sides: non-empty → reload_sg, then
   the string is cleared; empty → no reload. **Held**, and the "exit" special case (length 4, dword 0x74697865) was
   re-read in the same window.

3. **`PreLoadLibraries_` has exactly one caller (`initGame`)** — re-ran `get_function_xrefs` on 0x140233710: data refs
   at 0x14808431c/0x148084324 plus one code call from `initGame` at 0x1401a9538; nothing from `reload_sg`,
   `SetLevelSeriaToLoad_` or the frame loop. **Held.** This is what makes the in-game library reload a *new* action
   rather than a supported one, and the report's verdict for `parts.seria`/`OL.seria` rests on it.

4. **`reload_sg` success/failure branch polarity** — disassembled 0x140240e40–0x140240f30 a second time: the
   `LoadSeriaFile` call is at 0x140240e54, `TEST AL,AL` at 0x140240e5d, `JNZ 0x140240ee6` at 0x140240e5f. Both sides
   read: `AL != 0` → 0x140240ee6 (log "LEVEL reload successful" at 0x140240ef0, `CALL 0x1402d4270` = `Level::Load`
   at 0x140240f04); `AL == 0` → fall through to 0x140240e65 ("ERR: reload_sg failed"), `SerializeToFile OL.seria`
   0x140240eba, `Config.ini` write 0x140240ebf, quit flag 0x140240ec4, `XOR BL,BL` 0x140240edf. The decompiler's
   if/else is right; note that the *physical* layout is failure-first, so reading the block order as control flow
   would invert the meaning — the conditional jump is what settles it. **Held** (written that way in §6.2 and §9.3).

One correction made during the check: an earlier draft said "the exe imports only 100 functions, therefore no
`FindFirstFile`". `list_imports` was paged only once; the full table has 287 entries and does contain
`FindFirstFileA`/`FindNextFileA` (and no `ReadDirectoryChangesW`). §2.3 and §6.6 use the corrected version.

A second correction, found while re-reading `PreLoadLibraries_` against the string table: an earlier draft of §6.5
listed `Objects/Joint` as a folder loaded into `LIB_TOWN`. `search_strings` for `Objects/` returns only
`Objects/Designs/Test/`, `Objects/Designs/`, `Objects/Designs`, `Objects/Town`, `Objects/Land`, `Objects/Rock`,
`Objects/Docs` — there is **no** `Objects/Joint` string in 1.163. The four editor folder/library pairs are
`Objects/Town`→`LIB_TOWN`, `Objects/Land`→`LIB_GROUND`, `Objects/Rock`→`LIB_ROCK`, `Objects/Docs`→`LIB_DOCS`
(xrefs of the folder strings 0x14036be08/0x14036be28/0x14036be48/0x14036be68 all land inside `PreLoadLibraries_`).
§6.5 now reads that way. Everything else in the report was re-checked and held as written.
