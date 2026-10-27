# Hot-reload feasibility, part A: game file I/O (Highfleet 1.163)

Status: **complete** (checked twice at the end).
Program: `Highfleet.exe.unpacked.exe` v1.163, image base `0x140000000`, read-only Ghidra.
Second source used for the loader (not the game): `Modloader.v4/bass.dll` import table and
`hge_src/` (stock HGE 1.8 source), both local files.
Tags: `[code]` = read in this session at the cited address with a quoted line;
`[guess]` = inference plus what would confirm it; `[notes]` = repo note or decompiler
comment written earlier, not re-verified here; `[game]` = behaviour somebody observed in a
game run (relayed from notes).

Scope of this part: **how the game touches files** — which primitives open/read/write them,
whether anything is cached or watched, which readers can be re-run while the game runs, and
which writers can clobber a file a mod just changed. The in-memory tables themselves (part
stats, Body prototypes, engine resources) are part D (`ds4-data`); DLL unload/repatch and mod
config application are part C (`ds4-modside`); safe points and threads are `ds4-threads`.

---

## 0. Summary of verdicts (file-I/O angle)

| User idea | Verdict | Reason in one line |
|---|---|---|
| (a) hot-swap a mod DLL | **not feasible from game side** (mod side: part C) | the game has no plugin loader of its own; the only dynamic DLLs are `bass.dll` (audio) and system DLLs; the modloader scans `Modloader/mods` once and never frees a mod (§5) |
| (b) re-read mod JSON config while running | **feasible** (in the mod, not the game) | configs are read with plain `std::fs::read_to_string` by our own DLLs, once at `init`; no lock, no cache, no format registration — re-reading is a few lines of code (§6) |
| (c1) re-read `Data/Levels/*.seria` | **feasible with caveats, vanilla already does it** | every level change reloads the file from disk through `reload_sg`; a malformed file aborts the game (`exit_game`) (§4.1) |
| (c2) re-read `Libraries/parts.seria` | **partly feasible** | vanilla re-reads it whenever the editor setup runs (3 call sites in the `SCR_*` dispatcher, exact screens `[guess]`), but only into the *editor* library; the startup copy (`ALL_PARTS`) is never re-read, and leaving the editor writes the file back over your edit (§4.2, §4.6) |
| (c3) re-read `Libraries/OL.seria` | **not feasible as a reload** | read once in `PrepareMainLoop`, written on exit; no re-read path; a hand edit made while running is overwritten at a clean exit (§4.4) |
| (c4) re-read language packs `Data/Dialogs/*.seria_enc` | **feasible, vanilla already does it** | the in-game language switch re-reads and re-decrypts the pack through `LoadDialogue`, which frees the old table first (§4.3) |
| (c5) re-read `Media/*.res` / textures | **not feasible in place** | HGE registers resources by name once and rejects a second definition of the same name; sprites keep pointers to the old parsed resource (§4.8) |
| (c6) re-read `Config.ini` | **feasible with caveats** | `LoadConfig` (`0x140224c60`) is a self-contained re-read, but vanilla calls it only from `Main`, and the game rewrites `Config.ini` at exit (§4.5) |
| (c7) re-read `Ships/*.seria` (designs) | **likely feasible per click** | two `!ClickFunc` sites build `<name>.seria` and call `LoadSeriaFile` for a fresh object (§4.7); an already-instantiated ship is not updated |
| watch a file for changes | **nothing to build on** | the game imports no directory-change notification and no file-time call; only `FindFirstFileA` for listing (§1.6) |

---

## 1. The I/O inventory

### 1.1 `LoadSeriaFile` — the one `.seria` reader

`LoadSeriaFile` `0x140225930`, signature `bool (ISerializable *container, char *path)`.

Decompiled head and the call that matters `[code]`:

```c
file = (FILE *)0x0;
local_a4 = DAT_1403ef250;
lVar3 = OpenFile_(&local_118,pathToSeria,1,0x40);
if (lVar3 == 0) { ... setstate(...,2,false); }      /* failbit */
else            { ... clear(...,0,false);   }
if (file != (FILE *)0x0) {
    cVar1 = (*(code *)container->vfTable->Desearialzie)(container,local_128);
```

Disassembly at the same spot `[code]`:

```
1402259f9: LEA R9D,[RSI + 0x40]        ; 4th arg to OpenFile_ = 0x40
1402259fd: LEA R8D,[RSI + 0x1]         ; 3rd arg = 1
140225a01: MOV RDX,RBX                 ; path
140225a04: LEA RCX,[RSP + 0x30]        ; the std::filebuf on the stack
140225a09: CALL 0x140195f30            ; OpenFile_
...
140225a46: MOV RAX,qword ptr [RDI]     ; RDI = container, [RDI] = vtable
140225a49: LEA RDX,[RSP + 0x20]        ; RDX = std::istream
140225a4e: MOV RCX,RDI
140225a51: CALL qword ptr [RAX + 0x18] ; vtable slot 3 = Deserialize(container, stream)
```

`OpenFile_` `0x140195f30` is `std::filebuf::open` inlined `[code]`:

```c
p_Var2 = std::_Fiopen(param_2,param_3,param_4);
if (p_Var2 != (_iobuf *)0x0) {
  param_1[0x7c] = ...0x1;
  ...
  *(_iobuf **)(param_1 + 0x80) = p_Var2;
```

and `std::_Fiopen` is imported from `MSVCP140.dll` (`EXTERNAL:0000007d`) `[code: import table]`,
i.e. the CRT's `fopen`. Consequences, all from this body:

* **No HGE involvement.** `.seria` files are *not* read through HGE's `Resource_Load`, so the
  zip-pack search, the HGE path helper and `media.res` do not apply. The path is used exactly as
  given (relative to the current directory, which is the game folder).
* **No cache, no mtime check, no share lock.** A fresh `std::filebuf` is built on the stack,
  a `FILE*` is opened, the whole stream is parsed, then `fclose` is called
  (`140225a80: CALL qword ptr [0x1403518a0]` = `fclose`) and the buffer destroyed. Nothing
  persists between calls; there is no static table of loaded paths in this function.
* **The object is filled by the container's own virtual `Deserialize`** (slot `+0x18`), so
  "what happens to old data" is a property of the class being loaded, not of the I/O (§3).
* **Return value:** `true` only if the open succeeded *and* `Deserialize` returned non-zero;
  otherwise `false` with no exception (`0x140225a3f..0x140225abb`).

Its call sites (13, from xrefs `[code]`): `PrepareMainLoop`, `PreLoadLibraries_` ×5, the ship
loader `rep_1401a0a70_LoadSeriaFile`, `loadShipBackups?`, `loadSeriaForLibraries_`,
`rep_140208020_LoadSeriaFile` (wrapper), `!ClickFunc` ×2, `Load`, and `reload_sg`. The ones
that matter for data files are in §2. It is hooked (log-only) by `hf_probe` today
(`hf_notes/docs/hooks.md`).

### 1.2 `ISerializable::SerializeToFile` — the one `.seria` writer

`0x14024e3e0`, `bool (ISerializable *obj, char *path)` `[code]`:

```c
lVar3 = OpenFile_(&local_120,param_2,2,0x40);      /* openmode 2 = out */
...
cVar1 = (**(code **)(*param_1 + 0x10))(param_1,&local_128);   /* vtable slot 2 = Serialize */
```

`std::_Fiopen(path, 2, 0x40)` is `fopen(path,"w")`: **truncate, then write**. There is no
temp-file-plus-rename. If the process dies mid-write, or if the object serializes fewer keys
than before, the old file is gone.

Verified callers (xrefs to `0x14024e3e0`) `[code]`:

| caller | address | what it writes |
|---|---|---|
| `Save` (Profile) | `0x1402a77ac` | `Saves/Profile_N/profile.seria` |
| `loadShipBackups?` | `0x14023d2ac` | ship backups (`Ships_backup/`) |
| `loadShipworks?` | `0x1400d230e` | **`Libraries/parts.seria`** |
| `BuildQuitMenu` | `0x1401ecba8` | `Libraries/OL.seria` (only in the "Profiles.seria" exit branch) |
| `FUN_140211e10` (`exit_game`) | `0x140211e36` | `Libraries/OL.seria` |
| `FUN_140240b90` (`reload_sg`) failure path | `0x140240eba` | `Libraries/OL.seria` |
| `rep_14022cff0_..._free` = level saver `0x14024e6d0` | `0x14024ec3d` | **`Data/Levels/<name>`** |

### 1.3 Every std::filebuf open in the game (complete, from xrefs to `OpenFile_`)

14 xrefs to `0x140195f30`, i.e. 14 code sites that open a file through the CRT `[code]`:

| site | function | file |
|---|---|---|
| `0x1401957fb`, `0x14019584d` | `InitializeLogs` | log files |
| `0x140195a3e` | (mislabeled MSVCP140 function) | one more log-ish open |
| `0x140224d40` | `FUN_140224c60` = **LoadConfig** | `Config.ini` (mode 1) |
| `0x1401a3cc3` | `rep_1401952a0_..._Init` = ifstream open helper | dialogue pack |
| `0x140225a09` | **`LoadSeriaFile`** | any `.seria` (mode 1) |
| `0x140228c63` | `CreateUserSpaceFiles` | first-run defaults |
| `0x1401a6bbb` | `InitProfileFile` | `%s/profile.seria` |
| `0x1401a3de3` | (same helper as above) | another text read |
| `0x14024d620` | `FUN_14024d520` = **SaveConfig** | `Config.ini` (write) |
| `0x14024e4b9` | **`SerializeToFile`** | any `.seria` (mode 2) |
| `0x14024ef4a` | `SaveVolume` | volume/config fragment |

So the game has exactly **two** generic data-file primitives: `LoadSeriaFile` / `SerializeToFile`
(CRT filebuf) and the dialogue reader (ifstream built through the same filebuf). Everything else
is fixed-purpose: logs, `Config.ini`, profile, volume.

### 1.4 HGE's file loader — media only

`Resource_Load` is slot 18 (`0x140174850`), `Resource_Free` slot 19, `Resource_AttachPack` slot 20
(`0x1401744e0`), `Resource_MakePath` slot 23 — addresses as in `hf_notes/docs/engine-hge.md`; in
this program those functions are **not defined as functions** (`decompile_function` →
"No function found"), so I read the raw instructions.

The added slot 17 (`0x140174380`) is the file loader `[code, disassembly]`:

```
1401743ab: CALL qword ptr [RAX + 0xb8]     ; HGE_Impl::Resource_MakePath
1401743c0: MOV dword ptr [RSP + 0x28], 0x10000080
1401743c8: MOV EDX, 0x80000000             ; GENERIC_READ
1401743d5: LEA R8D, [R9 + 0x1]             ; share mode 1 = FILE_SHARE_READ
1401743d9: CALL qword ptr [0x140351148]    ; CreateFileA
...
14017441d: CALL qword ptr [0x140351140]    ; GetFileSize
140174458: CALL qword ptr [0x140351138]    ; ReadFile
14017446e: CALL qword ptr [0x1403516d0]    ; CloseHandle  (error path)
```

`CreateFileA` has **exactly one** xref in the whole program, `0x1401743d9` `[code: xrefs to
EXTERNAL:0000005e]`. So: one function reads whole files into a `malloc` buffer and closes the
handle immediately; it does not keep an open handle and does not cache contents. Media files
are therefore re-openable at any time; what is cached is the *parsed resource*, not the bytes.

`Resource_AttachPack` has **no call sites** — the only xrefs are the vtable slot
(`0x140367390`) and a vtable copy (`0x1480801fc`) `[code]`. With no attached packs the pack
list HGE searches (`hge_src/src/core/resource.cpp`, `while(resItem) ... unzOpen`) is empty, and
every `Resource_Load` goes to the disk loader. That is good news for mods: nothing on disk is
shadowed by a zip.

### 1.5 No file watching, no timestamp checks

Complete import list of the program `[code: list_imports]` contains
`CreateFileA`, `ReadFile`, `GetFileSize`, `CloseHandle`, `DeleteFileA`, `CreateDirectoryA`,
`RemoveDirectoryA`, `SetCurrentDirectoryA`, `FindFirstFileA`, `FindNextFileA`, `FindClose`,
`fopen/fread/fwrite/fclose`, `WritePrivateProfileStringA`, `GetPrivateProfileStringA`.
It does **not** contain `ReadDirectoryChangesW`, `GetFileAttributesA/W`,
`GetFileAttributesExA/W`, `GetFileTime`, `SetFileTime`, `MoveFileA/W`, `CopyFileA/W`,
`FindFirstFileExA` (I searched the import names explicitly; result: none present).

`FindFirstFileA` is used only for enumeration: `Resource_EnumFiles` `0x140174643`,
`Resource_EnumFolders` `0x140174737`, `CreateUserSpaceFiles` `0x140228b9a`,
`InitProfileFile` `0x1401a6af2`, `DeleteAllFilesInFolderMatchingPattern?` `0x140241c29`,
`ClickFunc` `0x14013cf4d`, `FUN_140241e90` `0x1402422d6` `[code: xrefs]`. None of these
compares write times. **There is no change detection anywhere in the game**; a mod that wants
"reload when the file changed" must do its own `GetFileAttributesEx`/`FindFirstFile` poll.

### 1.6 Relative paths and the working directory

Every path in the game is relative (`Libraries/OL.seria`, `Config.ini`, `Data/Levels/`, `Saves/`,
`Media/media.res`). The directory lister `get_filenames` `0x14021a2d0` (mislabeled
`rep_1401fcf80_VCRUNTIME140_DLL__memcmp`) changes the process working directory around its
`FindFirstFileA`/`FindNextFileA` loop `[code]`:

```c
GetCurrentDirectoryA(0x104,local_158);
BVar6 = SetCurrentDirectoryA(param_1);
if (BVar6 == 0) { WriteToClientLog(0,3,"ERR: get_filenames failed with %s.",param_1); }
else { hFindFile = FindFirstFileA("*",&local_298); ... FindNextFileA ... }
/* restores local_158 at the end (SetCurrentDirectoryA(local_158)) */
```

`PreLoadLibraries_` uses it to list `Objects/Designs` and `Ships` before calling the ship loader
for each name. Consequences: (a) a reload helper must resolve paths relative to the process CWD,
not the exe path; (b) the CWD is global process state and is switched temporarily during
enumeration, so a reload that runs on another thread during `PreLoadLibraries` could read a
wrong path (another reason to do reloads on the game thread).

---

## 2. What is read when, and what can be re-read

Read of every data-file reader in this session unless marked otherwise.

| file | reader | when | re-read by vanilla? |
|---|---|---|---|
| `Data/Levels/<name>.seria` | `LoadSeriaFile` from `reload_sg` `0x140240b90` | every level/screen change | **yes, always** (§4.1) |
| `Libraries/parts.seria` | `LoadSeriaFile` in `PreLoadLibraries_` `0x140233710` | once, startup | no (fresh editor copy: §4.2) |
| `Libraries/parts.seria` | `LoadSeriaFile` in `loadSeriaForLibraries_` `0x1400d09a0` | each editor-screen setup | yes, into `PARTS_CONSTRUCTOR_SERIA` |
| `Libraries/constructor.seria` | same function, other branch | same | yes (constructor mode) |
| `Libraries/OL.seria` | `LoadSeriaFile` from `PrepareMainLoop` `0x1401ad9d6` | once, startup | **no** |
| `Objects/Town/*`, `Objects/Land/*`, `Objects/Rock/*`, `Objects/Docs/*` | `LoadSeriaFile` per file in `PreLoadLibraries_` (names from `get_filenames` `0x14021a2d0`) | once, startup | no |
| `Ships/*`, `Objects/Designs/*` | ship loader `0x1401b08a0` per name (`rep_1401a0a70_LoadSeriaFile`), called at the end of `PreLoadLibraries_` | once, startup (plus `loadShipBackups_` if the version string changed) | no |
| `<name>.seria` from a UI list | `!ClickFunc` `0x140135297`, `0x14013d875` → `LoadSeriaFile` | on click | **yes, each click reads the file again** (§4.7) |
| `Data/Dialogs/<lang>.seria_enc` | `LoadDialogue` `0x1402253a0` | startup and **on the language toggle** | **yes** (§4.3) |
| `Media/media.res` + every `.res` it includes | HGE `Resource_Load` via `Init_HGE` `FUN_1401ad080` | once, startup | no (names registered once) |
| `Media/Tex/*.png`, sounds, particles | HGE `Resource_Load` on demand | on first use, then cached by name | only after `Resource_Free` |
| `Config.ini` | `LoadConfig` `0x140224c60` | once, from `Main` `0x14027e976` | no (function re-callable, §4.5) |
| `Config.ini` | HGE `Ini_GetString` `0x140173620` → `GetPrivateProfileStringA` | on each call (Win32 profile API reads the file) | per call, but callers are vtable calls I did not enumerate |
| `Saves/Profile_N/profile.seria` | `Load` `0x140293f90` (`/profile.seria` built into a path) | when the `Profiles.seria` level is entered | functionally yes — loading a save is a level load |
| `Modloader/config/*.json` | **our DLLs**, `std::fs::read_to_string` (`hf_qol_fork/src/config.rs:219`) | once in `init` | mod's own choice (§6) |

Nothing in that table is read from a memory-mapped file, and nothing is read ahead by a worker
thread: all these readers run on the game thread (the only other threads are the modloader's
init thread and BASS audio) `[guess: thread attribution from the call graphs; ds4-threads owns
the exact frame boundaries]`.

---

## 3. Re-reading into a live object: what the game itself proves

`LoadSeriaFile` never clears the target. The container's `Deserialize` (slot `+0x18`) does
whatever it does; three vanilla call sites demonstrate that this *can* be a full reload:

1. **The level reload** passes the same `LevelSingleton` again and then calls `Level::Load()`
   (§4.1). It is the normal path for every screen change, not a debug curiosity.
2. **`LoadDialogue`** explicitly frees/clears the global dialogue table *before* parsing
   (`rep_140184060_..._free(&DAT_143a1c3a0)` is the first statement) `[code]`. So the
   "clear first" convention exists in this code base and was needed for text.
3. **`loadSeriaForLibraries_`** replaces the editor library object: it builds a fresh `Node`
   first, `SetLink(&DAT_1403ef4f0, node)`, and only then loads into `PARTS_CONSTRUCTOR_SERIA`
   `[code]`.

Whether a given class appends, replaces or leaks on a second `Deserialize` is part D's question;
from the I/O side the important part is: **the file can always be read again, cheaply, at any
time; the hard part is entirely on the object side.**

---

## 4. The individual re-read paths

### 4.1 Levels: `SetLevelSeriaToLoad_` → `SomethingPreTask` → `reload_sg`

`SetLevelSeriaToLoad_` `0x14025afd0` only stores the request `[code]`:

```c
/* This single CopyString seems to be singularly responsible for telling the
   game what to load :( */
CopyString((longlong **)&SeriaToLoad,param_1,plVar7);
DAT_143a11903 = param_2;
DAT_143a11908 = param_3;
```

`SomethingPreTask` `0x140286e40` (the pending-load consumer) reads `SeriaToLoad` and branches on
the literal `"exit"` (`0x140286ea6: CMP dword ptr [RAX], 0x74697865`); the load itself is
`[code]`:

```
140286ef1: CALL 0x14024e6d0            ; save the CURRENT level (Data/Levels/<name>)
140286f2a: CALL 0x140240b90            ; reload_sg(SeriaToLoad)
140286f31: JNZ 0x140286f38             ; success -> continue
140286f33: CALL 0x140211e10            ; failure -> exit_game()
```

The save call is gated by `byte [0x143a11908]` (`0x140286ed1`), the third argument of
`SetLevelSeriaToLoad_`: when non-zero the current level is written back to
`Data/Levels/<current>` **before** the next one is loaded (editor "save on leave") `[code]`.

`reload_sg` `0x140240b90` `[code]`:

```c
WriteToClientLog(1,2,"APP::reload_sg initiated with %s.",param_1);
... /* ~30 globals reset, lists freed, Shipworks palette re-inited if IsInEditor */
local_60.ptr = (char *)0x76654c2f61746144;   /* "Data/Lev" */
local_60._8_4_ = 0x2f736c65;                  /* "els/"      */
... /* appends param_1 */
bVar2 = LoadSeriaFile(LevelSingleton,(char *)uVar7);
if (bVar2) {
    WriteToClientLog(1,2,"LEVEL reload successful with %s.",uVar7);
    Level::Load();
    ...
    CopyString(&DAT_1403c13b0,param_1,plVar11);   /* remember current level name */
}
else {
    WriteToClientLog(0,3,"ERR: reload_sg failed, for %s",uVar7);
    CopyString((longlong **)&SeriaToLoad,"",(longlong *)0x0);
    WriteToClientLog(1,2,"APP::exit_game initiated.");
    ISerializable_SerializeToFile(ObjectsLibrarySingleton,"Libraries/OL.seria");
    FUN_14024d520();      /* SaveConfig */
    DAT_143a11901 = 1;    /* exit flag */
}
```

**Verdict for level files: feasible, with the game's own semantics.** Editing
`Data/Levels/X.seria` and re-entering X picks the change up without a restart. The costs are:
the whole scene is torn down (that is what `reload_sg` does, ~50 globals reset, `Level::Load()`
rebuilds everything), and a parse error is not recoverable — the game exits. An experiment can
therefore be run safely only with a copy of the file and a known-good edit (see §7, E1).

### 4.2 `parts.seria`: two copies, one re-read, one write-back

Startup (`PreLoadLibraries_` `0x140233710`) `[code]`:

```c
pIVar5 = (ISerializable *)Node::Node(local_80);
ALL_PARTS = pIVar5;
CopyString(...,"LIB_EDITOR",...);
bVar3 = LoadSeriaFile(ALL_PARTS,"Libraries/parts.seria");
if (!bVar3) { ...; LogFatalError("ERR: Preload_libraries was unable to load LIB_EDITOR."); ... }
(*(code *)ALL_PARTS->vfTable[2].destructor_)(ALL_PARTS,0);   /* slot +0x20 */
AssignRandomId(ALL_PARTS,1);
(*(code *)ALL_PARTS->vfTable[2].field1_0x8)();               /* slot +0x28 */
```

Editor (`loadSeriaForLibraries_` `0x1400d09a0`) `[code]`:

```c
this = (Node *)New(0x128); node = Node::Node(this);
SetLink((Link *)&DAT_1403ef4f0,node);
pcVar3 = "Libraries/parts.seria";
if (LOAD_CONSTRUCTOR_OR_EDITOR != '\0') pcVar3 = "Libraries/constructor.seria";   /* byte [0x1403ef36a] */
bVar1 = LoadSeriaFile(PARTS_CONSTRUCTOR_SERIA,pcVar3);   /* global [0x1403ef4f8] */
...
CopyString(...,"EDITOR_LIBRARY",...);           /* or "CONSTRUCTOR_LIBRARY" */
(*(code *)PARTS_CONSTRUCTOR_SERIA->vfTable[2].destructor_)(PARTS_CONSTRUCTOR_SERIA,0);
AssignRandomId(PARTS_CONSTRUCTOR_SERIA,1);
/* then: for each child: *(undefined4 *)(*plVar4 + 0x7a8) = 999; */
```

So the same file is loaded into two different trees: `ALL_PARTS`/`LIB_EDITOR` once at startup,
and `PARTS_CONSTRUCTOR_SERIA`/`EDITOR_LIBRARY` every time the editor setup runs. The second one
is the one that can be refreshed at runtime for free, and the third-party Shipworks palette
builds on it (`[notes]` `hf_notes/docs/formats.md`; not read here).

Callers of `loadSeriaForLibraries_`: `FUN_1400beea0` at `0x1400beff5` and `0x1400bf2ea`; the
`SCR_*` dispatcher `SomethingWithLevelSerias` `0x1402ac970` calls `FUN_1400beea0` at
`0x1402b373e`, `0x1402b381f`, `0x1402b3911` `[code: xrefs]`. That is *screen setup*, not a
per-frame path — so "enter the editor again" is a safe refresh point for the palette.
`[guess: the three sites are the editor / extended-editor / builder entries; confirmed by a
log or breakpoint inside `loadSeriaForLibraries_` while cycling those screens.]`

What it does **not** do: re-read into `ALL_PARTS`, i.e. the runtime object the rest of the game
sees. Nothing in the program calls `LoadSeriaFile(ALL_PARTS, ...)` a second time — I looked at
all xrefs to `0x140233710` and to the `"Libraries/parts.seria"` string `[code]`.

**Verdict:** a "parts.seria hot reload" today means "the editor palette reloads on entry". Any
effect beyond the palette requires re-running the startup pass into a new tree and re-linking
the global part registry — part D's problem, with this I/O caveat: §4.6.

### 4.3 Language packs: the vanilla hot reload that already exists

`LoadDialogue` `0x1402253a0` `[code]`:

```c
rep_140184060_..._free(&DAT_143a1c3a0);        /* clear the old table first */
local_68.ptr = (char *)0x6169442f61746144;     /* "Data/Dia" */
local_68._8_4_ = 0x73676f6c;                   /* "logs"    */
if (coreLanguage == 1)      pcVar14 = "russian.seria_enc";
else { if (coreLanguage != 2) goto LAB_14022546c; pcVar14 = "english.seria_enc"; }
rep_1401952a0_..._Init(local_198,uVar7,0x20,0x40);   /* ifstream open */
/* seekg(end), tellg, read whole file, LCG-decrypt whole buffer
   (pcVar5[i] ^= (v>>15)^v, v = 2531011 + i*214013), split at '#', CopyString each entry */
```

Callers `[code: xrefs to 0x1402253a0]`: `PrepareMainLoop 0x1401ad95b` (startup) and
`!ClickFunc 0x140131b11`. The second one is the language toggle `[code]`:

```
140131af8: MOV EAX, dword ptr [0x1403c0e1c]   ; coreLanguage
140131afe: INC EAX ; CMP EAX,0x2 ; CMOVG EAX,1 ; MOV [0x1403c0e1c],EAX
140131b11: CALL 0x1402253a0                   ; LoadDialogue  (then 0x140256f10: rebuild UI text?)
```

**Verdict: feasible and already proven in production.** A mod that calls `LoadDialogue` (no
arguments) re-reads and re-decrypts `Data/Dialogs/<current language>.seria_enc`. It also means
the *format* is a hot-reloadable one: entries are keyed by `#KEY`, the table is rebuilt from
scratch, and the only state is the global table at `0x143a1c3a0`. Caveats: `LoadFatalError` on
a missing file (the message is `"ERR: load_dialog failed to open file %s."`) and the fact that
the UI keeps already-built text strings until it re-asks for them.

### 4.4 `OL.seria`: read once, written at exit

Read `[code]`:

```
1401ad9c8: LEA RDX,[0x14036ae10]        ; "Libraries/OL.seria"
1401ad9cf: MOV RCX,qword ptr [0x143a1c428]
1401ad9d6: CALL 0x140225930             ; LoadSeriaFile
```

inside `PrepareMainLoop`. Write `[code]`:

```c
void FUN_140211e10(void) {                       /* exit_game */
  WriteToClientLog(1,2,"APP::exit_game initiated.");
  ISerializable_SerializeToFile(ObjectsLibrarySingleton,"Libraries/OL.seria");
  FUN_14024d520();                               /* SaveConfig -> Config.ini */
  DAT_143a11901 = 1;
  WriteToClientLog(1,2,"APP::exit_game finished successful.");
```

`FUN_140211e10` is called from `!ClickFunc` (two sites, 0x140130b87 / 0x140131a7d) and
`SomethingPreTask` (0x140286ecc, the "exit" path; 0x140286f33, the failed-reload path) `[code]`.
`BuildQuitMenu` has the same three lines inlined for the `"Profiles.seria"` exit branch
`0x1401ecba8` `[code, decompiled]`.

**Verdict: not a reload candidate.** No re-read path exists; calling `LoadSeriaFile` on
`[0x143a1c428]` again would be an experiment with an unknown `Deserialize` on a live singleton
(part D), and a clean exit rewrites the file from memory anyway, so a hand edit made while
running is lost. That the read and the write use the same global is confirmed by the failure
path, which writes `[0x143a1c428]` back to the same file `[code: 0x140240eb3 / 0x140240eba]`.
Practical rule: **edit `OL.seria` only with the game closed** (the repo note says the same, with
the mechanism slightly wrong — it is exit, not startup).

### 4.5 `Config.ini`: a ready-made re-read function, and a writer at exit

`LoadConfig` `FUN_140224c60` `[code]`:

```c
_DAT_1439e92b8 = 0xffffffffffffffff;
uRam00000001439e92c0 = 0xffffffffffffffff;
lVar3 = OpenFile_(&local_118,"Config.ini",1,0x40);
if (lVar3 == 0) { ...; (**(code **)*DAT_1439ef248)(DAT_1439ef248,1);
                      (**(code **)*globalAstruct)(globalAstruct,1); return 0; }
(**(code **)(*globalAstruct + 0x18))(globalAstruct,local_128);   /* Deserialize */
FUN_14018d3d0();                                                 /* apply keys */
```

* Only caller: `Main 0x14027e976` `[code: xrefs]` — vanilla reads it once.
* `FUN_14018d3d0` `[code]` is small: 26 calls of the form
  `rep_140179ee0_tooLongError(buf, &DAT_1439e93a0, 0x1000..0x1009 and 0x1010..0x1017, <keycode>)`,
  then 4 for `DAT_1439ef1c0` and 4 for `DAT_1439e9310` (action ids `0x1000..0x1003`).
  The argument pattern (action id + default key code, copied into a per-context table) looks like
  key-binding defaults `[guess: confirmation is changing a binding in Config.ini and re-running
  `FUN_140224c60`; it does not touch video mode, fonts or the window, so it is safe to re-run]`.
* Two globals are reset to `-1` before parsing (the two "not set" markers); the rest of the
  config object is overwritten by `Deserialize` only for keys present in the file, so a key
  *removed* from `Config.ini` may keep the old value `[guess: depends on the config class's
  Deserialize; confirm by deleting one key and re-running LoadConfig in a probe]`.

`SaveConfig` `FUN_14024d520` `[code]`:

```c
uVar3 = FUN_140188a00(pppuVar7);  *puVar9 = uVar3;   /* four ints into 0x1439e92b8.. */
lVar5 = OpenFile_(&local_120);                       /* args elided by the decompiler */
(**(code **)(*plVar1 + 0x10))(plVar1,&local_128);    /* Serialize; error text names Config.ini */
```

Callers: `exit_game` (via `FUN_14024d520()` right after the OL write) and the failed-`reload_sg`
path `[code]`. So `Config.ini` is **rewritten at every clean exit** from the in-memory object.

**Verdict: feasible with caveats.** Calling `FUN_140224c60` again is the cheapest real reload in
the game: it re-parses the file into the live config object and re-applies key bindings. Caveats:
(a) only "settings the code reads later from globals" become live — anything copied into the
window/renderer/level at startup will not (which is the same behaviour as changing a setting in
the options menu); (b) at exit the file is rewritten from memory, so a change that did not
parse (or that the object dropped) disappears; (c) the HGE `Ini_*` path is a *second* reader of
the same file (`GetPrivateProfileStringA`), so values could be read at different times
depending on which code asks.

### 4.6 The writers that can clobber a hot edit

`loadShipworks_` `0x1400d2260` `[code]`:

```c
if (PARTS_CONSTRUCTOR_SERIA != (longlong *)0x0) {
    if (LOAD_CONSTRUCTOR_OR_EDITOR == '\0') {                 /* byte [0x1403ef36a] == 0 */
      ISerializable_SerializeToFile(PARTS_CONSTRUCTOR_SERIA,"Libraries/parts.seria");
    }
    (**(code **)(*PARTS_CONSTRUCTOR_SERIA + 0x48))();     /* destroy the library */
}
```

Byte-level, in `loadShipworks_` `[code: disassembly]`:

```
1400d22fe: CMP byte ptr [0x1403ef36a], 0x0     ; LOAD_CONSTRUCTOR_OR_EDITOR
1400d2305: JNZ 0x1400d231a                     ; constructor mode -> no write
1400d2307: LEA RDX, [0x14035c0c8]              ; "Libraries/parts.seria"
1400d230e: CALL 0x14024e3e0                    ; SerializeToFile(PARTS_CONSTRUCTOR_SERIA, ...)
```

`loadShipworks_` is called from `SomethingWithLevelSerias` (twice), from `reload_sg` **when
leaving the editor** and from two `!ClickFunc` sites and `FUN_140211220` `[code: calls to
0x1400d2260]`. The `reload_sg` one is gated by the editor flag `[code]`:

```
140240d34: CMP byte ptr [0x1403ef368], R13B      ; IsInEditor, R13B = 0
140240d3b: JZ 0x140240d42
140240d3d: CALL 0x1400d2260                      ; loadShipworks_ -> writes parts.seria
```

So: **open the editor, change `parts.seria` on disk, leave the editor → your edit is overwritten**
by whatever the game loaded when the editor opened. This is the single most important practical
gotcha for a `parts.seria` hot reload.

Same shape elsewhere:
* `Data/Levels/<name>` is written by `0x14024e6d0` (at `0x14024ec3d`) when
  `SetLevelSeriaToLoad_` was called with the "save" flag (`byte [0x143a11908]`) — the editor's
  save-on-leave. A hand-edited level file can be overwritten by leaving that level from the
  editor.
* `Libraries/OL.seria` at exit (§4.4).
* `Config.ini` at exit (§4.5).
* `Saves/Profile_N/profile.seria` by `Save` `0x1402a73a0` (`0x1402a77ac`) — the normal
  save-game path, unaffected by data-file reloads unless a reload happens during save.

### 4.7 Ship / design files: also loaded on demand

Two `!ClickFunc` sites (`0x140135297`, `0x14013d875`) build a path at runtime and call
`LoadSeriaFile` into an object `[code]`:

```
140135272: LEA R8, [0x14035ba74]       ; ".seria"
140135283: CALL 0x140011510            ; string concat: <prefix><name> + ".seria"
14013528c: CALL 0x140023940            ; (returns the char* to load)
140135294: MOV RCX, RBX                ; destination object
140135297: CALL 0x140225930            ; LoadSeriaFile
```

So at least one UI list re-reads a `.seria` per click instead of using a cached copy.
`[guess: the ship/design list (ship-info or editor load-design) — confirmed by clicking an entry
with the `hf_probe` `LOAD` hook on and reading the logged path.]` If so, **editing a
`Ships/*.seria` file and re-opening that entry is a per-file hot reload that already works**;
what it cannot do is update a ship that is already instantiated in a battle or a campaign, since
the loaded record is a fresh object.

### 4.8 `Media/*.res` and textures: registered once, no re-definition

HGE's resource manager, from the stock source `hge_src/src/helpers/resources.cpp:324` `[code:
local source, not Ghidra]`:

```c
if(FindRes(rm, restype, np->tkn_string()))
{
    np->ScriptPostError("Resource "," of the same type already has been defined.");
    ... np->put_back(); continue;            /* definition skipped */
}
```

and a script itself is only parsed if not already known (`if(!FindRes(rm, RES_SCRIPT, sname))`
at `resources.cpp:270`). `Resource_Load` (`src/core/resource.cpp`) reads the file through the
pack list, then the disk loader, and returns a `malloc`ed copy that the caller frees — no byte
cache, but the *parsed* `RResource`/`RAnimation`/`RScript` live in the manager's list for the
process lifetime.

**Verdict: not feasible as an in-place hot reload** without (i) freeing the old resource
(`Resource_Free`, slot 19), (ii) re-parsing the `.res`, and (iii) re-pointing every game object
that holds a `hgeSprite*`/texture handle at the new one. Point (iii) is the blocker: sprites are
stored inside parts, GUI elements and creature fields, and there is no registry that would let a
mod re-link them all. A restart is the sane path; an "attach a zip before `Init_HGE`" override is
the sane *installation* path (the HGE mechanism exists, the game just never uses it — §1.4).

---

## 5. DLL loading: what the file layer shows

* The game's own imports contain `LoadLibraryA` and `FreeLibrary`. Callers of `LoadLibraryA`
  `[code]`: `SoundInit 0x14017ce4b` (loads `bass.dll`), `GetBatteryLife 0x1401741df`, `user32.dll`
  for raw input in `FUN_140188ce0` (decompiled), and the `GetProcAddress` wrapper `0x14027e6e2`.
  **There is no plugin/mod loader in the game.**
* The `bass.dll` proxy (`Modloader.v4/bass.dll`, PE32+ x86-64) imports `LoadLibraryA`,
  `FreeLibrary`, `LoadLibraryExW`, `GetModuleFileNameW`, `CreateFileW`, `FindFirstFileExW`,
  `FindNextFileW`, `DisableThreadLibraryCalls` — and **not** `ReadDirectoryChangesW` `[code:
  objdump -p]`. Strings include `./Modloader/mods`, `./Modloader/config`, `Failed to find mods: `. 
  So the loader enumerates the mods folder once, `LoadLibrary`s each DLL, reads `logging.json` once,
  and (per `hf_notes/docs/setup.md`) never unloads a mod (`mem::forget`).
* Consequence for (a): "hot-swap a mod DLL" cannot be built on any game facility, and Windows
  will not let you `FreeLibrary` a DLL whose detours are live in the game's code pages. Any
  workable scheme is "load v2 next to v1, hand over patch ownership, leave v1 resident" (part C).
  File I/O is not the obstacle: the loader keeps no share lock on the file, so the DLL on disk can
  be replaced while the game runs `[guess: standard Windows loader behaviour; confirmed by
  replacing a loaded mod DLL during a session]`.

---

## 6. Mod JSON configs: what the file layer shows

The game never reads `Modloader/config/*.json`. Our DLLs read them with the CRT:
`hf_qol_fork/src/config.rs:219` `[code: source]`

```rust
pub fn load(path: &str) -> Result<Self, Box<dyn Error>> {
    let config_str = std::fs::read_to_string(path)?;
    Ok(serde_json::from_str(&config_str)?)
}
```

called once from `init()` (`hf_qol_fork/src/lib.rs:42`), before patches are prepared. There is
no lock, no cache, no handle held between calls, and no format registration in the game. So
re-reading the file while the game runs is trivial at the I/O level; whether the new values do
anything depends on the mod: in the QoL fork most values are consumed at patch-preparation time,
so a re-read must either re-prepare patches (part C) or the values must be moved into
runtime-read state. The loader's own `logging.json` is documented as "changes take effect the
next time the game starts" (`Modloader.v4/README.md`).

---

## 7. Minimal experiments the user could run later (not run here)

**E1 — level file, prove the reload path (cheapest, highest value).**
1. Copy `Data/Levels/City.seria` (or any level you can enter twice) and hash the file.
2. Arrange logging of `LoadSeriaFile` calls: `hf_probe`'s `LOAD` hook, or a log-only mod.
3. Start the game, enter the level, leave, edit one harmless numeric value (e.g.
   `LVL_WIND_FORCE`), re-enter the level without restarting.
4. Expected: two `LOAD` lines for the same path, and the second load shows the edit (wind or
   arena size). If you entered the level from the editor, hash the file before/after leaving:
   the editor's save-on-leave rewrites it (§4.6). A parse error makes the game exit, so keep
   the backup.

**E2 — language pack, prove a text reload.** Note a part description (`#MDL_x_DESC`) on the
ship-info screen, edit that entry in the decoded pack, then switch the language away and back
(the `!ClickFunc` path above). Expected: the new text appears once the screen re-asks for it.
This is the game's own live text reload and it validates the "clear table, then re-read" pattern.

**E3 — `Config.ini` re-read.** From a debug mod, call `FUN_140224c60` on a hotkey after editing
a key binding, then press the key. Expected: the new binding works; a startup-only setting
(video mode, language) does not change. Check before the game exits, because `SaveConfig`
rewrites the file at exit.

**E4 — `parts.seria` palette refresh.** Leave the editor (this writes the file — hash it), edit
one part stat in `parts.seria`, enter the editor again. Expected: the palette is rebuilt from
the file (`loadSeriaForLibraries_` runs on editor entry); the next leave overwrites the edit
again. This experiment measures the write-back, it does not give a usable reload.

**E5 — mod config, prove the trivial case.** In a mod, add a watcher that polls
`GetFileAttributesExA` on `Modloader/config/<mod>.json` once per second and re-runs
`Config::load`; print one line when the content changes. This is safe, needs no Ghidra work,
and separates "file can be re-read" (yes) from "values take effect" (part C).

---

## 8. Risks and rules of thumb

1. **Every writer truncates** (`fopen(...,"w")` through `_Fiopen`): a crash or a partial
   serialize destroys the previous file. Back up before any experiment; keep copies of
   `Libraries/`, `Data/Levels/`, `Config.ini`.
2. **The game rewrites three things you may have edited**: `Libraries/OL.seria` and
   `Config.ini` at every clean exit, `Libraries/parts.seria` when leaving the editor,
   `Data/Levels/<name>` when a level was loaded with the save flag. Do data-file hot reloads on
   files the game does not own, or accept the loss.
3. **A malformed file is not always recoverable.** A level file that fails to parse ends in
   `exit_game` (§4.1); a `parts.seria` that fails at startup is `LogFatalError`; a `Config.ini`
   that cannot be opened makes `LoadConfig` destroy `globalAstruct` and return 0 (what `Main`
   does next was not traced — treat it as fatal) `[code: 0x140224d40..0x140224e61]`. There is no
   "try again" and no quarantine.
4. **No change detection exists** — a reload is a mod-owned poll; there is no inotify equivalent
   in the game (imports).
5. **`.seria` opens are serial, on the game thread, and cheap** (whole file into CRT buffers,
   `fclose` right after): a reload fits at a safe point without a worker thread.
6. **Media resources cannot be redefined by name** (HGE): design "reload art" as a new resource
   name plus re-pointing, never as an override of an existing name.
7. **Two readers of `Config.ini`** (the game's object and HGE's `Ini_*`) can hold different
   values; "reload config" is not one switch.

---

## 9. Not determined

* Whether `Node::Deserialize` (or the class used for libraries) clears its children on a second
  load — I did not read it; part D owns it. What I can say is that the level path reuses one
  `LevelSingleton` and works `[code: reload_sg]`.
* Which exact screens the three `FUN_1400beea0` call sites correspond to (editor / extended /
  builder); a breakpoint inside `loadSeriaForLibraries_` would settle it.
* The full set of `Config.ini` keys the game reads only at startup vs reads live; `ref/config-ini.md`
  lists keys, but I did not map them to readers.
* Whether any `Ini_*` (HGE) value is read per frame — those calls go through the engine vtable
  and I did not enumerate them.
* Whether the modloader holds a share lock on a loaded mod DLL (assumed no; §5).
* Which code paths would notice a CWD change made outside `get_filenames` (the lister restores
  it, but nothing prevents a third-party DLL from switching it while the game reads a relative
  path).

---

## 10. Checked twice

Re-read at the end of the session, at the cited address, against the DS_RULES checklist
(missing sqrt/abs/clamp, polarity, right base object, invented constant):

1. **`LoadSeriaFile` opens with CRT `filebuf` and calls the container's vtable slot `+0x18`,
   with no cache.** Re-read `0x140225930` (decompile + disassembly `0x1402259f9..0x140225a51`)
   and `0x140195f30` (`std::_Fiopen`). **Held**, byte-level: `0x140225a51` is
   `CALL qword ptr [RAX + 0x18]` after `MOV RAX,[RDI]`/`MOV RCX,RDI`, and the open passed
   `R8=1, R9=0x40`. Correction made while checking: the decompiled `if (file != 0)` is the
   filebuf's `_File` member (`+0x80` in `OpenFile_`) aliased onto a stack slot — Ghidra computed
   `RBP-0x50 == RSP+0xb0 == buffer+0x80` — not a second open; the odd `fwrite`/`fclose` pair is
   the filebuf close path. Polarity: open fails → `setstate(2)` → `false`.
2. **`reload_sg` reloads `Data/Levels/<name>` into `LevelSingleton` and exits the game on
   failure.** Re-read `0x140240b90` decompile and the `0x140286ed1..0x140286f38` disassembly of
   `SomethingPreTask`. **Held**, byte-level: `0x140240eac` is `LEA RDX,[0x14036ae10]`
   ("Libraries/OL.seria") with `RCX=[0x143a1c428]` and `CALL 0x14024e3e0`, immediately followed
   by `CALL 0x14024d520` (SaveConfig) and `MOV byte [0x143a11901],1` in the failure branch;
   `TEST AL,AL` / `JNZ 0x140286f38` means success continues, `0x140286f33 CALL 0x140211e10`
   (exit_game) is failure. The `"Data/Lev"`/`"els/"` immediates were decoded byte by byte.
3. **`loadShipworks_` writes `Libraries/parts.seria` from the editor library on the way out.**
   Re-read `0x1400d2260` and disassembled `0x1400d22fe..0x1400d2313`. **Held**: the guard is
   `CMP byte ptr [0x1403ef36a],0` + `JNZ` (skip), i.e. write only when the constructor-mode flag
   is 0, and the path is `[0x14035c0c8]` = `"Libraries/parts.seria"`, called with
   `[0x1403ef4f8]` = `PARTS_CONSTRUCTOR_SERIA` (editor library), not `ALL_PARTS`. Also re-read
   the mirror in `loadSeriaForLibraries_` (`0x1400d09de: CMP byte [0x1403ef36a],0` +
   `CMOVNZ RDX,[0x14035c0a8]` = constructor.seria), so the flag means the same in both places.
4. Extra check made after a `[notes]` claim looked imprecise: the repo says the game rewrites
   `OL.seria`/`parts.seria` **at startup**. The writers are `exit_game` (exit), the
   failed-reload path, and `loadShipworks_` (leaving the editor) `[code: xrefs to
   0x14024e3e0]`. No startup writer was found; the note's practical advice (edit with the game
   closed) stands, the mechanism does not.
5. Correction to my own earlier guess in §1.6: I had written that `SetCurrentDirectoryA`'s use
   was unknown. Re-read `0x14021a2d0`: it is `get_filenames`, which `SetCurrentDirectoryA`s into
   the folder, lists with `FindFirstFileA("*")`, and restores the old directory — so the CWD *is*
   changed during the startup enumeration. The report says that now; the thread warning follows
   from it.
