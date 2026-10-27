# Hot-reload feasibility, part B: frame loop, threads, safe points

Highfleet 1.163 (`Highfleet.exe.unpacked.exe`, image base `0x140000000`), static analysis only.
Ghidra was read-only (no renames, no comments, no bookmarks). Tags: `[code]` = read in this
session at the cited address with the quoted line; `[notes]` = repo note, not re-checked;
`[guess]` = inference, with what would confirm it. "Not found" lists the searches.
Part A/C/D material is only touched where the frame/thread picture needs it.

**Scope of this part.** Where a frame starts and ends, what runs inside it, which threads
exist, and which instants are safe for (i) replacing mod code and (ii) re-reading data.

---

## 1. Verdicts (short form)

| Idea | Verdict | One-line reason |
|---|---|---|
| (a) hot-swap a mod **DLL** (unload old, load new, same name) | **not feasible** as unload/reload; **feasible with caveats** as "resident shim + generation swap" | the loader never unloads mods; patchy patches are permanent (trampoline pages live outside the DLL and point straight into it). A new generation can be `LoadLibraryA`'d at runtime, but the old one must stay mapped and every hook must call through a swappable pointer table owned by a resident shim. |
| (b) re-read **mod JSON configs** while the game runs | **feasible with caveats** | the game has no JSON reader at all; configs are 100 % mod-side. Re-parse, validate, apply all values at one frame boundary. Values baked into an installed trampoline cannot be re-applied (no second patch on that site). |
| (c) re-read the **game's own data files** | **feasible with caveats** for per-scene `.seria` scripts; **not feasible** for libraries/media/config | the game re-reads a scene script on every scene change through its own two-phase `SeriaToLoad` → load-at-next-PreTask mechanism. `Libraries/OL.seria`, `Media/*.res`, the Box2D world and the task objects are built once at startup and never rebuilt. |
| Needed frame hook (all three ideas) | one site, proven shape | the 5-byte `CALL SomethingPreTask` at `0x1401a8eb8` becomes a 5-byte jump to a trampoline that calls our function (which calls `SomethingPreTask` first or second). No argument forwarding, no alignment trap, no relative-call relocation. |

Nothing here depends on suspending the main thread, and none of the proposals asks for one.

---

## 2. The frame loop

### 2.1 Where the loop lives

`Main` `0x14027e8a0` creates the app singleton, logs, then calls `PrepareMainLoop`;
`PrepareMainLoop` `0x1401ad5a0` does all startup loading and then calls the HGE loop
through the interface vtable and blocks there for the whole session `[code]`:

```
                    /* Main Loop? */
      (**(code **)(*HGE + 0x18))();
      WriteToClientLog(1,2,"@");
      WriteToClientLog(1,2,"EXITING MAIN LOOP.");
```

* `HGE` is the global `0x143a119e0`; `+0x18` is vtable slot 3 = `System_Start` `0x14017e080`
  (the only xrefs to `0x14017e080` are the vtable words at `0x140367308` and a data pointer)
  `[code]`.
* Everything after the call is exit-only teardown: the task/level singletons are destroyed,
  then `SuperBigDeconstructor(SuperBig)` (the Box2D world), `Media_res` is freed,
  `SDL_Quit()`, `HGE->Shutdown`, `HGE->Release` `[code, same decompile]`.
  **Consequence: the Box2D world and the task objects exist exactly once per process.**
* There is no second call into the loop: the frame function is entered only from HGE (§2.2).

### 2.2 What `System_Start` does per iteration

Decompiled at `0x14017e080`; quoted lines, my reading after each `[code]`:

```
  do {
    if (*(longlong *)(this + 0x978) == 0) {
      BVar4 = PeekMessageA(local_68,(HWND)0x0,0,0,1);
      if (BVar4 != 0) {
        if (local_68[0].message == 0x12) goto LAB_14017e2b5;
        DispatchMessageA(local_68);
```

* message pump first (only when the qword at `HGE+0x978` is null); `WM_QUIT` leaves the loop.
* `UpdateMouse(this);` then `if ((this[0x308] == 0) && (this[0x975] == 0)) goto Sleep(1)` —
  when the window is not active and a second flag is clear, the loop only pumps + sleeps.

```
    do { DVar5 = timeGetTime(); uVar6 = DVar5 - *(int *)(this + 0xd78);
         *(uint *)(this + 0xd80) = uVar6; } while (uVar6 == 0);
    uVar2 = *(uint *)(this + 0xd70);
    if (uVar6 < uVar2) break;                       // -> Sleep(1) path
    fVar8 = (float)uVar6 / 1000.0;                  // seconds
    *(float *)(this + 0xd6c) = fVar8;               // HGE's own frame delta
    if (0.2 < fVar8) { ... *(float *)(this + 0xd6c) = ...; }   // 200 ms cap
    *(float *)(this + 0xd68) = fVar8 + *(float *)(this + 0xd68);  // accumulated time
```

* `uVar2` is HGE's fixed-frame-time in ms (state `HGE_FPS`). `Init_HGE` `0x1401ad080` calls
  `SetStateInt` (`+0x50`) only with ids `0x18`, `0x11`, `0x12`, `0x13` — i.e. the
  screen-state ids, not an FPS id (`0x11/0x12/0x13` are width/height/bpp per
  [engine-hge.md](../hf_notes/docs/engine-hge.md)) `[code, disasm 0x1401ad280..0x1401ad2ec]`.
  So `HGE+0xd70 == 0` at runtime is the strong reading `[guess]`; worth confirming with a
  one-line log. With it 0, the `break` and therefore the `Sleep(1)` at `0x14017e2aa` are
  never reached in normal play (`[guess]`, same premise).
* HGE's delta (`HGE+0xd6c`) has a 200 ms cap. The game's own frame function does **not**
  read it; it computes its own wall-clock dt (§2.3). Whether any other game code calls
  HGE `Timer_GetDelta` was not checked `[not determined]`.

```
    cVar3 = (**(code **)(this + 0x610))();          // FrameFunc, 0x14017e264
    if (cVar3 != '\0') { ClearQueue(this); this[0x308] = 0; return '\x01'; }
    if (*(code **)(this + 0x618) != (code *)0x0) (**(code **)(this + 0x618))();  // RenderFunc
    ...
    ClearQueue(this);
  } while( true )
```

* The loop also leaves when the qword at `HGE+0x978` is non-null: after the frame function
  it does `CMP qword [RBX+0x978], RDI` (RDI = 0) and jumps to the exit block if different
  (`0x14017e27c..0x14017e283`); the same field being non-null also *disables* the message
  pump at the top of the iteration. What sets it was not determined `[code for both uses,
  not determined for the setter]`.

* `HGE+0x610` = frame function; `Init_HGE` registers it as state id `8`:
  `0x1401ad0c0 LEA R8,[0x1401a8970]` / `0x1401ad0c7 MOV EDX,0x8` /
  `0x1401ad0cc CALL [RAX+0x40]` (SetStateFunc) `[code]`. The other `SetStateFunc` ids in
  that block are `0xb` (FOCUSLOST `0x1401a8900`), `0xa` (FOCUSGAIN `0x1401a8940`), `0xc`,
  `0xd`; **there is no id `9`**, so `HGE_RENDERFUNC` is never set and `HGE+0x618` stays null
  `[code]` (the decompile only calls it when non-null).
* Frame-function return value = "quit": the last real instruction of `_FrameFunc` loads
  the exit flag into `EAX` (`0x1401a90c7 MOVZX EAX, byte ptr [0x143a11901]`), and
  `0x14017e26a TEST AL,AL` decides `[code]`. So the game exits via `0x143a11901`
  (set by the quit menu), not via `PostQuitMessage` `[code for the load/site, notes for who
  sets the flag]`.

### 2.3 `_FrameFunc` `0x1401a8970`: time, then seven tasks, then the idle sleep

Disassembly of the task chain (`[code]`, bytes quoted):

```
0x1401a8eb8  E8 83 DF 0D 00   CALL 0x140286e40   SomethingPreTask
0x1401a8ebd  E8 BE D4 0D 00   CALL 0x140286380   SomethingPhysicTask
0x1401a8ec2  E8 29 4D FE FF   CALL 0x14018dbf0   SomethingInputTask
0x1401a8ec7  E8 B4 82 E6 FF   CALL 0x140011180   SomethingAITask
0x1401a8ecc  E8 BF E6 F7 FF   CALL 0x140127590   SomethingGameTask
0x1401a8ed1  E8 BA 49 13 00   CALL 0x1402dd890   SomethingSoundTask
0x1401a8ed6  40 0F B6 CE      MOVZX ECX, SIL    (the "render this frame" bool)
0x1401a8eda  E8 41 DF 16 00   CALL 0x140316e20   SomethingVideoTask
```

All seven calls are unconditional in the binary. Each of the seven task functions has
exactly one code caller — this very block (`get_bulk_xrefs`; all other references are
DATA/vtable words) `[code]`, so this is the only frame driver. The bool passed to the video task is
computed just above from a frame-time history (see the ledger); the video task's first
0xE0 bytes never read `ECX` — its early-outs are two globals (`0x1403c2d42`, and a
one-shot skip byte `0x143a11963` at `0x140316ea0..0x140316eba`) `[code]`.
**Do not assume "no render this frame" from that bool**; whether it is used later in the
5 KB body was not checked `[not determined]`.

Then the tail `[code]`:

```
0x1401a8edf..0x1401a8f88   walk the temporary link vector DAT_143a15868: clear body+0x910,
                           free each link, reset DAT_143a15870 = begin
0x1401a8f96  CALL 0x1402ab980           stamp work time: (QPC now - base)*1e6/freq, ring push
                              (base was set at 0x1401a89c6 by 0x1402abed0: QPC freq/counter
                               into timer+0x380/+0x378)
0x1401a8fa9  CALL 0x1402abd50           mean work time -> FPS -> clamp into FLOAT_1403c0e14
0x1401a8fe7..0x1401a9030                CORE_USE_SLEEP path: Sleep(20 ms - work)
0x1401a9036..0x1401a90c4                append this frame's work time to the 20-entry ring
0x1401a90c7  MOVZX EAX, [0x143a11901]   exit flag
0x1401a90d6  CALL 0x1403345a0           __security_check_cookie
0x1401a90f6  RET
```

**The main thread spends most of its life inside `Sleep` at `0x1401a9030`, with the whole
frame's stack still live**, because the sleep tops the frame up to 20 ms of *total* time
(20 ms budget minus work done so far). (Sleep is reached through the IAT slot `0x140351120`;
the same slot is used by `System_Start` at `0x14017e2aa` and by `0x14017daa6` `[code]`.)

### 2.4 Two clock systems

* Fixed **simulation** step: `time_related_global_` = `(1.0 / coreFrameRateFlt_) *
  coreTimeWrap_`, forced to 0 when the freeze byte is set; `coreFrameRateFlt_` at
  `0x1403c0de4` is `0x42480000` = **50.0f** `[code, read_memory]`; `coreTimeWrap_` at
  `0x1403c0dec` is `0x3F800000` = 1.0f static default `[code, read_memory]` and is
  configurable (the property registered next to `CORE_USE_SLEEP` is `CORE_TIMEWRAP`, string
  at `0x140371bc8`) `[code]`. The product is written to `0x1403c126c`, and the only
  writers of that global are two stores in `_FrameFunc` (`0x1401a8a85`, `0x1401a8a96`)
  `[code, xrefs]`; readers include `CalculateStats` (`0x140080dab`),
  `Engine_ApplyThrustForce` (`0x14002872e`) and `creatureLogic` `[code, xrefs]`.
  So one frame = one physics step of 0.02 s; a slow frame slows game time, it does not
  run extra steps.
* **Wall-clock** dt: written by `_FrameFunc` at `0x1401a8a19` into `0x1403c1268`
  (negative clamped to 0 at `0x1401a8a29`) `[code]`. `creatureLogic` reads `0x1403c1268`
  in 120+ places `[code, xrefs]`. So part of the game's logic (timers etc.) advances by
  *real* elapsed time. Normally the frame-level sleep makes the wall dt ≈ 20 ms; when a
  frame's work exceeds the 20 ms budget there is no sleep and the wall dt grows to the work
  time. A *one-off* stall (a load, or a mod doing work inside the frame) shows up as a
  **large wall dt on the next frame**, because the "previous timestamp" is refreshed at the
  *start* of each frame.
* Freeze byte `0x143a11909` (`Ghidra: doRecoil_global`): set to 1 at `0x14023271d` inside
  `displayTextOnCreature_`, cleared at `0x140269cd3` inside `LocalFileReadAndUpdate`, read
  by `_FrameFunc` at `0x1401a8a8d` to force `time_related_global_ = 0` `[code, xrefs]`.
  It freezes **time only**; all seven tasks still run every frame. It is not a barrier, a
  lock, or a "safe" state.

---

## 3. Threads

### 3.1 The executable creates no threads

Full import table checked (`list_imports`, last index `0x11f`) `[code]`:

* **No `CreateThread`, no `_beginthreadex`, no `_beginthread`** anywhere.
* The only synchronisation imports are `CreateEventW`, `WaitForSingleObjectEx`,
  `ResetEvent`, `SetEvent`, `EnterCriticalSection`, `LeaveCriticalSection`,
  `InitializeCriticalSectionAndSpinCount`; every xref I checked for them is inside the CRT's
  guarded-static-init helpers `_Init_thread_header` / `_Init_thread_wait` /
  `_Init_thread_footer` / `InitializeCriticalSectionAndSpinCount`
  (`0x1403346d4..0x14033485c`) `[code, xrefs]`.
* `Sleep` is imported once (slot `0x140351120`) and called from three places, all in HGE
  (`0x14017daa6`, `0x14017e2aa`) or in `_FrameFunc` (`0x1401a9030`) `[code, xrefs]`.
* `GetCurrentThreadId` is imported (`EXTERNAL:0x6c`) — useful for a mod to verify which
  thread a hook is on `[code]`.

**But the executable does import OpenMP and uses parallel regions.** `vcomp140.dll`
functions are imported (`_vcomp_fork` `EXTERNAL:0xb3`, `_vcomp_enter_critsect` `0xb4`,
`_vcomp_leave_critsect` `0xb5`, `_vcomp_for_static_end` `0xb6`,
`_vcomp_for_static_simple_init` `0xb7`) and really called through the CRT thunks at
`0x140336550..0x140336576` from three functions `[code, xrefs]`:

* `Precache` `0x140170a20` (HGE resource manager; `_vcomp_fork(1,3,body,...)`; called from
  `Init_HGE` at `0x1401ad3a0` `[code]`),
* `0x140170b90`, a `for` loop over a vector of 0x28-byte records: for each record it builds
  `prefix + "/" + name`, calls the HGE resource manager's load (`*AnotherHGE_ + 0x88`) under
  a critical section (`DAT_1439e8658`), stores the result, and on failure calls
  `MessageBoxA(0, "Texture not found", name, 0)` — the texture precache loop `[code,
  decompiled]`,
* `0x140170e30` (0xF18 bytes, a resource/HGE routine) at `0x1401718b2` `[code, xrefs]`.

`vcomp140.dll` runs these bodies on its own worker pool, so **during Precache the resource
manager is touched by vcomp threads, not only by the main thread**, and a failed texture
load raises a `MessageBoxA` (and therefore a nested message loop, and therefore
`DispatchMessageA`/the window proc) **on a worker thread** `[code]`.

So, precisely: **the simulation, the GUI and every frame-loop structure are touched by one
thread** — the process main thread that ran `Main`; the resource manager (HGE) can
additionally be busy on vcomp workers while `Precache` runs. There is no game-level mutex
for the frame state and no worker pool reading it.

### 3.2 The threads that do exist

* **The mod loader** (`bass.dll` proxy) is loaded **by the game itself**: `SoundInit`
  calls `LoadLibraryA("bass.dll")` at `0x14017ce4b` (string `0x140366f08`, error string
  `"Can't load BASS.DLL"` `0x140366f18`), resolves `BASS_*` with `GetProcAddress`, and
  `SoundDone` calls `FreeLibrary` at `0x14017cdb1` `[code]`. Its import table has
  `CreateThread` + `LoadLibraryA/ExW` + `FreeLibrary` (objdump of `Modloader.v4/bass.dll`)
  `[code]`; the loader starts a thread in `DllMain` that runs `init` and loads mods `[notes]`.
* **Mod init therefore runs on a loader thread**, concurrently with `PrepareMainLoop`, not
  on the game thread `[notes]`. Our mods install hooks and read game memory from there
  today; that works because the loop is not running yet (and the loader waits for the
  unpacked bytes `[notes]`).
* **BASS audio threads** (inside `bass.dll`, plus whatever the driver spawns), the **D3D
  driver's** internal threads, and **mod-created threads** (hf_probe's log thread [notes],
  the elevation poller in `hint: window` mode [notes]). None of these execute game code if
  the mods behave; the mod loader never unloads a mod `[notes]`.

### 3.3 The practical rule

Any mutation of game state, any patch/unpatch of game code, and any call into game
functions must happen on the main thread, inside a known frame instant (§4), or before the
loop starts. There is no lock that would make a second-thread call safe, and `SuspendThread`
is not a substitute: the main thread is inside `Sleep` most of the time but can equally be
inside `VirtualProtect`, the heap, or a blocking file read. The one exception to know about
is `Precache`'s vcomp workers (§3.1): do not touch the HGE resource manager while a precache
may be running, and do not assume a `MessageBoxA` can only appear on the main thread.

---

## 4. Safe points

"Safe" here means: no game function is half-executed on the stack, no per-frame temporary
structure is half-built, and no other thread is in game code. The only such instants are
frame boundaries.

### 4.1 Candidate sites (all verified `[code]`)

| # | Site | Bytes | When it runs | Use |
|---|---|---|---|---|
| S1 | `0x1401a8eb8` `CALL 0x140286e40` (PreTask) | `E8 83 DF 0D 00` (5) | once per frame, before the frame's task chain | **recommended commit point** (see 4.2) |
| S2 | `0x1401a8eda` `CALL 0x140316e20` (VideoTask) | `E8 41 DF 16 00` (5) | after all logic, at the render | read-only per-frame tap; the call needs its bool argument if replaced |
| S3 | `0x1401a90c7` `MOVZX EAX,[0x143a11901]` | `0F B6 05 33 88 86 03` (7) | last game instruction of the frame (after the sleep and after the frame-time record) | most quiescent point inside game code, but the 7 bytes are a RIP-relative load inside the canary/epilogue region: needs a hand-built trampoline with the displacement recomputed (plain `patch_call` copies the operand verbatim and breaks it) |
| S4 | `0x14017e264` `CALL qword [RBX+0x610]` (HGE→FrameFunc) | `FF 93 10 06 00 00` (6) | in HGE, **after** `_FrameFunc` returned, before post-frame bookkeeping | the cleanest "outside the game's frame function" point; the 6 bytes are position-independent (register-indirect), so a hand-built trampoline can run them and continue |
| S5 | IAT `Sleep` slot `0x140351120` | — | at `0x1401a9030` (frame idle), `0x14017e2aa` (HGE limiter), `0x14017daa6` | observe "the main thread is about to idle"; filter by thread id, it also fires on mod threads |
| S6 | HGE window proc `0x14017e2f0` (registered at `0x14017d6bf`, class style `0x2b`) | — | `DispatchMessageA` in `System_Start`'s pump (between frames) | hotkey input only; see the caveat 4.4 |
| — | inside `SomethingPreTask` while `SeriaToLoad` is set (`0x140286f2a CALL 0x140240b90`) | — | **not safe**: blocking scene load, world torn down | do not re-enter |
| — | inside `ClickFunc` `0x14012f120` where it calls `LoadSeriaFile` (`0x140135297`, `0x14013d875`) | — | **not safe**: blocking save load | do not re-enter |
| — | inside `SomethingVideoTask` (5 KB, D3D11 immediate context, state objects) | — | **not safe**: renderer state | do not call game render from another hook |

### 4.2 The recommended commit point S1, and why it is the shape it is

`_FrameFunc` calls `SomethingPreTask` with no arguments. Replace that call with
`patchy::PatchSession::patch_call(0x1401a8eb8, f, 5, false, ReturnType::None)`.
patchy rewrites the five bytes as a near **jump** (`patch.rs` `build_near_jump`, `NEAR_JUMP =
0xe9`) to a trampoline that calls `f` and jumps back to `0x1401a8ebd` `[code, patchy
source]`. `save_overwritten = false` means patchy does *not* copy the stolen bytes; our
function is responsible for the original call, which gives control of the order:

```
#[no_mangle] extern "C" fn frame_commit() {
    unsafe { game::something_pre_task() };   // 0x140286e40
    shim::apply_pending();                    // code swaps / config apply / reload request
}
```

Why this exact site and shape:

* **Alignment is already correct.** At `0x1401a8eb8` we are at a `call` site, so
  `RSP % 16 == 0`; because the site is rewritten as a jump (not a call), the trampoline
  starts with the same `RSP`. patchy's `build_call` (see `src/arch.rs`) pushes 7 registers
  and then emits `SUB RSP,8` (`ALIGN_STACK`) precisely for that assumption. At a *function
  entry* `RSP % 16 == 8` and the same code produces a misaligned call — the documented
  `ACCESS_VIOLATION ...FA2514FB` crash in [sound.md](../hf_notes/docs/sound.md) `[notes]`.
* **No relative-call relocation.** With `save_overwritten = true` patchy copies the stolen
  bytes verbatim into its `mmap` trampoline; the stolen bytes here are themselves a `call
  rel32`, which would land in the wrong place after the copy. `patch_call(..., false, ...)`
  sidesteps that entirely.
* **Implicit byte guard.** `install_permanently` re-reads the five original bytes and fails
  with `SourceChanged` if they moved (`src/session.rs:328`) `[code]`, so a wrong build is
  rejected at install. Keep the explicit version/log line anyway.
* **No flags hazard.** The bytes after the call site are another `CALL`, so no `Jcc` consumes
  flags set before our hook.
* **Two orderings, both useful.** `original-then-mod` (as above) runs after PreTask's
  cleanup (`BreakUpFrame`, `CollectDeadNodes`, `Creature_RecalcStatsPass`) and after any
  pending scene load, i.e. with the world fully consistent and simulation about to start.
  `mod-then-original` runs before that same cleanup, i.e. immediately after the previous
  frame finished — the natural place to *request* a scene/data reload (see 4.3).
* **Nothing else to hook.** One site, no per-feature sites in `FrameFunc`; a generation
  swap only has to move one pointer table, not re-patch the game.

### 4.3 The game's own two-phase load (this is the data-reload model to copy)

`SetLevelSeriaToLoad_` `0x14025afd0` does **not** load. It copies the requested name into the
global `SeriaToLoad` `0x1403c1390` (length `0x1403c13a0`, capacity `0x1403c13a8`) at
`0x14025b012`, sets `0x143a11903` / `0x143a11908`, builds a loading GUI when the name is
`Map.seria` or `City_generated.seria`, and then calls three small helpers `[code]`:

* `FUN_1402db350` `0x1402db350` — only compares the name and sets two booleans
  (`BOOL_147fc6f80`, `DAT_147fc6f81`); no I/O `[code, decompiled]`.
* `FUN_14000e430` `0x14000e430` — resets a block of intrusive list heads
  (`0x1403c6340..0x1403c6380` stride 0x10, plus `0x1403c6320/0x1403c6330`) `[code]`.
* `FUN_1402e4b50` `0x1402e4b50` — stops/frees audio objects in the `somethingAudio` table `[code]`.

The load happens at the **next** frame's first task, `SomethingPreTask` `0x140286e40`
`[code, decompiled + disassembly]`:

```
0x140286e70  MOV R9, [0x1403c13a0]        ; pending name length
0x140286e8c  TEST R9,R9 ; JZ 0x140286f58  ; nothing pending -> skip
0x140286ea0  CMP R9,4 ; ... "exit"        ; special-case: quit
0x140286f2a  CALL 0x140240b90             ; <-- the loader (also calls LoadSeriaFile 0x140225930)
0x140286f4a  MOV byte [0x143a11903],0     ; clear the two flags
0x140286f51  MOV byte [0x143a11908],0
```

So frame *N* (the click) builds and renders the loading screen; frame *N+1* blocks inside
`SomethingPreTask` while `FUN_140240b90` `0x140240b90` parses the scene, then clears the
request. The request is made from in-frame code (`ClickFunc`, `SomethingWithLevelSerias`,
`UpdateStrategicFleet`, `creatureLogic`, `UpdateMapAircraftGroup`, `precombatOk` are
callers of `0x14025afd0` `[code, xrefs]`), so "next frame" is the normal case.

**Two consequences.** (1) There already is a well-defined, game-owned deferred-load
transaction with a loading screen; a mod can reuse it by writing `SeriaToLoad` and the two
flags at S1, which is much safer than calling the loader itself. (2) A scene load is a
single blocking frame: the HGE loop cannot pump messages until the frame function returns,
so a hotkey pressed then is delivered afterwards (whether the loader itself pumps messages
was not checked); and the frame after the load sees a large wall dt (§2.4).

### 4.4 Things that look like safe points but are not

* **The window proc** `0x14017e2f0` runs in `System_Start`'s `DispatchMessageA`, i.e.
  between frames — but it is not dormant: the `WM_ACTIVATE` branch (`message 6`, at
  `0x14017e3e5`) calls two game-side functions (`CALL 0x14024c0b0` at `0x14017e438`,
  `CALL 0x14025f810` at `0x14017e443`; bodies not read), and the `WM_KILLFOCUS` branch
  (`message 8`, at `0x14017e3a5`) calls into the object at `HGE+0x2e8`, which
  [engine-hge.md](../hf_notes/docs/engine-hge.md) calls a renderer-like object `[code,
  notes]`. It is not a "game does nothing" moment.
  Worse, `MessageBoxA` is imported and called from five places (`0x14016cdec`,
  `0x140170d9f`, `0x140202df5`, `0x140089141`, `0x140085b1d`), each of which runs a nested
  message loop **inside** game code — and `0x140170d9f` is the "Texture not found" box inside
  the vcomp precache loop, i.e. it can run on a worker thread (§3.1) `[code, xrefs]`. A
  window-proc hook can therefore fire mid-task and on a non-main thread. Use S6 for input
  only, never for code swaps.
* **"Paused"** (Esc menu) is a screen state. The freeze byte `0x143a11909` is a *time*
  freeze, not a state freeze: all seven tasks still run (§2.4). Neither gives a consistency
  guarantee.
* **`Sleep` inside the frame** means the main thread is idle with a live stack. Hooking the
  `Sleep` IAT slot (S5) tells you *when* it is idle, but by the time a second thread sees
  the flag the main thread may already be running again. Do not use it as a mutual-exclusion
  primitive; use it for diagnostics only.

---

## 5. (a) Hot-swapping a mod DLL

### 5.1 Why unload/reload cannot work

* The loader `LoadLibraryA`s every `Modloader/mods/*.dll` once, calls `version` then `init`,
  and never unloads them (`mem::forget`) `[notes]`; the game only frees the loader DLL
  itself, at `SoundDone` `[code]`.
* `patchy` is explicit: *"installed patches are permanent"*, *"a library containing any
  callback or destination referenced by these patches must therefore remain loaded for the
  same duration"* (`src/session.rs` docs) `[code]`. After install, `PermanentPatchSet`
  keeps only `address` and `size`, not the original bytes; there is no unpatch API
  `[code, session.rs:45 and :387]`.
* Trampoline pages are anonymous `mmap` allocations outside the DLL and contain the
  absolute address of the Rust callback (`build_call`: `... CALL_BYTES, function as usize`)
  `[code, arch.rs:50]`. Unloading the DLL leaves those pages pointing into freed
  memory; the very next hit of any hooked function jumps into a hole.
* `ensure_patches_do_not_overlap_installed` refuses a second patch over an installed one
  `[code, session.rs:344]`, so a new generation cannot simply install the same hooks
  again.

### 5.2 What does work: resident shim + generation swap

Design that fits the facts above:

1. **Shim** (one DLL, loaded at startup like today): owns *all* game patch sites for its
   feature set, plus a table `static TABLE: [AtomicPtr<Fn>; N]`. Installed once; never
   replaced; never freed.
2. Each installed hook is a thin stub: it snapshots the inputs it needs and tail-calls
   `TABLE[i]` if non-null, else returns "do nothing"/the pass-through value.
3. **Generation DLLs** are loaded at runtime with `LoadLibraryA` (the exe imports it and
   uses it for `bass.dll` at `0x14017ce4b`, so calling it from inside the process on the
   main thread is unremarkable) and export a versioned descriptor: ABI version, table of
   function pointers, an `init(host_api)` and a `shutdown()`. No patching is done by the
   generation itself.
4. **Swap at S1**: call `shutdown()` on the old generation (join/stop any threads it
   started), read the new descriptor, validate the ABI, publish the pointer table with a
   single exchange, keep the old DLL loaded forever (or until exit).
5. Anything the *game* keeps a pointer to must live in the shim or in memory that survives
   the generation (the old DLL stays mapped, so leaks are safe; frees are not).

Caveats: the shim's hook ABI per site is fixed (you cannot change a hook's signature
without a game patch); a generation that adds a *new* game patch site cannot install it at
runtime unless the shim already owns that site or the site is currently unpatched and is
installed from S1 (which is safe precisely because S1 is a frame boundary and only the main
thread runs game code — but it permanently consumes the site, so a later generation that
needs a different patch there is stuck); mod-created threads must be stoppable; per-site
argument marshalling and return-value policy (`ReturnType`) must be decided once.

Verdict: **feasible with caveats**; the old DLL is never unloaded, which is the price.

### 5.3 Risks

* A generation that installs its own permanent patch creates a site the next generation can
  never change (patchy overlap refusal). Keep patches in the shim.
* Swapping while a hook frame is live. At S1 the only live mod frame is the shim's own
  commit function; every other mod hook runs later in the frame and has returned. Do not
  swap from S5/another thread.
* Allocator/lifetime: anything the game holds (captured `std::string`, `Vec`, vtable
  pointers) must belong to the shim or the old generation, and the old generation must stay
  mapped.
* If any mod thread calls a hooked game function, a swap can change behaviour mid-call.
  Contract: generations are main-thread-only.
* Crash-at-exit: the game `FreeLibrary`s the *loader* at `SoundDone`; whatever runs after
  that must not need loader or mod code `[guess]` (not exercised here).

---

## 6. (b) Re-reading mod JSON configs

* The game has no JSON code at all: an ASCII-`json` string search returns 0 matches in
  `Highfleet.exe.unpacked.exe` `[code]`. Only mods read `Modloader/config/*.json`
  (e.g. `hf_qol_fork/src/lib.rs:42 let config = Config::load("Modloader/config/qol.json")`,
  parsed once with serde in `init`) `[code]`.
* So this is a mod-side feature. Two classes of values, with different costs:
  * **Read at hook time from a `static`**: e.g. `zoom.rs` installs `set_zoom_level` /
    `calc_zoom_value` that read `static mut MIN_ZOOM / MAX_ZOOM / ZOOM_LEVELS` `[code]`.
    Reload = parse + validate + assign the statics at S1. No re-patch, no restart.
  * **Baked into the trampoline/instruction at install time**: e.g. `elevation_rules::
    patch_elevation_rules(session, rules)` takes the parsed rules and builds the tolerance
    trampolines from them (`[code, signature/body start; whether every field is baked into
    code was not read]`). These cannot be re-applied: the site is permanently patched
    (§5.1), and patchy refuses an overlapping second patch. Only a restart (or a shim that
    reads config at runtime) changes them.
* Apply policy: parse into a *new* config object off-thread (or in the same hook), validate
  fully, then swap the statics in one block at S1; on any error keep the old values and log.
  Do not apply half a file.
* Values that change allocation/geometry (plane health, shop parts, loadouts) should be
  applied at the scene boundary (S1 with a pending load) rather than mid-battle; some of
  them populate city shops only when a city's shop is first generated `[notes]`, so
  re-reading them later has no effect at all until the next city.
* Verdict: **feasible with caveats**; the caveat is the second class above, and it is a
  design constraint, not a frame-loop problem.

---

## 7. (c) Re-reading the game's own data files

Three groups, three answers.

1. **Per-scene scripts (`*.seria` for a level) — feasible.** The game itself re-reads them
   on every scene change through `SeriaToLoad` → `FUN_140240b90` in `SomethingPreTask`
   (§4.3). Editing the file and changing screens is already a hot reload of that data; a
   mod can also request the same reload by writing `SeriaToLoad` at S1. This is the only
   game-data path that is designed to be re-run.
2. **Libraries and parts (`Libraries/OL.seria`, `parts.seria`) — not feasible while
   running.** `LoadSeriaFile("Libraries/OL.seria")` is called once from `PrepareMainLoop`
   `0x1401ad9d6` before `Init_HGE` `[code]`; the library singleton is built there and the
   game rewrites those files at startup `[notes]`. `LoadSeriaFile` does have other callers
   (`PreLoadLibraries` `0x1402337c2..0x140234706`, `loadSeriaForLibraries?`,
   `loadShipBackups?`, `ClickFunc` for save loading, `Load` `0x140293f90`,
   `FUN_140240b90`, `FUN_140224ec0`) `[code, xrefs]`, but there is no path that re-parses
   the libraries into the live objects, and doing it by hand means freeing and rebuilding
   every `Body`/`Creature`/shop reference in the process while Box2D is live.
3. **Media and global config (`Media/media.res`, fonts, sounds, `Config.ini`) — not
   feasible while running.** The resource manager is built in `Init_HGE` from
   `Media/media.res` (`0x14016fd30`) and cached; `.res` scripts are parsed then
   [notes/engine-hge.md]. `CORE_USE_SLEEP` / `CORE_TIMEWRAP` are registered once as config
   properties in `InitializeAppProperties` (`0x14023d5e4..0x14023d5f5`) `[code]`; the globals
   could in principle be written directly, but that is re-implementing config handling, not
   reloading it.

Verdict: **(c) is "feasible with caveats" only for scene scripts; "not feasible" for
libraries/media/config without a restart** — a restart is exactly what the user wants to
avoid, which is why (b) and scene reloading are the realistic targets.

---

## 8. Risks that apply to all three

1. **Patching from a non-game thread while frames run**: the main thread may be inside the
   exact bytes being replaced. There is no lock to take. Do patches at S1 only.
2. **Misalignment traps**: patchy's `ALIGN_STACK` assumes `RSP%16==0` at the call site; a
   function entry is `8`. Either hook a call site (S1/S2) or steal the prologue's stack
   adjustment, or use an explicit padded trampoline (the `hf_voice` pattern) `[notes]`.
3. **Stolen bytes that are address-dependent**: `patch_call(..., save_overwritten=true)`
   copies the stolen bytes verbatim into the trampoline. Both a `call rel32` (the S1 site)
   and a RIP-relative memory operand (the S3 site) break unless relocated; patchy's
   `Trampoline` builder only fixes up your own labels/jumps, it does not disassemble and
   relocate stolen instructions. Use `false` + call the original yourself, or write the
   trampoline by hand for position-independent sites (S4).
4. **Flags**: patchy restores registers but not `RFLAGS`; never steal bytes that end in a
   `CMP`/`Jcc` pair whose branch is resumed after the hook (the `SomethingPreTask` entry is
   exactly such a case: `CMP [0x1403c2b11],0` at `0x140286e44` feeds `JZ` at `0x140286e4b`).
5. **Blocking windows**: scene load at `0x140286f2a`, save load inside `ClickFunc`,
   `MessageBoxA` paths. A deferred-work queue must not assume it will run within one frame.
6. **Wall-dt jump**: a long in-frame operation raises `0x1403c1268` for the next frame and
   `creatureLogic` timers consume it. Keep the work short or do it during a scene load
   where the game already expects a stall.
7. **Renderer**: D3D11 immediate-context work happens in `SomethingVideoTask` on the main
   thread; no mod should call `Gfx_*`/D3D from its own thread. `[guess]` the device is not
   created for multi-threaded use: the game reaches it through the import
   `D3D11CreateDeviceAndSwapChain` (thunk at `0x140333f93`); the create-flags argument was
   not decoded, so the `D3D11_CREATE_DEVICE_SINGLETHREADED` bit is unverified. Confirming
   it means reading the flags argument at that thunk's caller.
8. **Do not patch the bytes you are standing on.** From inside the S1 hook, patching any
   site other than S1 itself, the frame-function call site, or `System_Start` is fine
   (they are not executing); re-patching S1 or patching the HGE call site while its frame is
   live would rewrite an instruction that is currently on the call stack.
9. **Exit ordering**: the game frees the loader DLL (`FreeLibrary` at `0x14017cdb1`) during
   `SoundDone`; a resident shim must not need anything after that.
10. **vcomp workers**: never patch or inspect the HGE resource manager while a `Precache`
    may be running, and do not treat "a message box is up" as proof that the main thread is
    the one pumping messages (§3.1, §4.4).

---

## 9. Proposed minimal experiment (do not run now)

Goal: prove the frame boundary claim and the swap mechanism without touching gameplay data.
Two stages, each a separate throwaway DLL in `Modloader/mods`, one at a time.

**Stage 1 — frame tap (read-only except one hook), ~30 min of play.**
Install one hook with a version precheck for the five bytes `E8 83 DF 0D 00` at
`0x1401a8eb8`:

```
patch_call(0x1401a8eb8, frame_commit as *const (), 5, false, ReturnType::None)

#[no_mangle] extern "C" fn frame_commit() {
    unsafe { something_pre_task(); }            // 0x140286e40, call it yourself
    log_frame_tap();                            // see below
}
```

`log_frame_tap` writes one line per frame to the mod's own log: a monotonically increasing
frame number, `GetCurrentThreadId()`, `QueryPerformanceCounter` delta in µs, the pending-load
length at `0x1403c13a0`, and the freeze byte `0x143a11909`.
Pass criteria: (i) exactly one line per frame at ~50 Hz; (ii) one and the same thread id,
and it equals the id `init` logged (that proves the frame runs on the main thread and that
`init` did not); (iii) on a deliberate scene change (dock and enter a city, enter combat),
a gap of many milliseconds in the deltas, coinciding with a non-zero pending-load length on
the previous line — that is the blocking load window, measured; (iv) no crash for 10 minutes.
This also measures how much wall time S1 itself costs, which is the budget for any swap.

**Stage 2 — swap spike (two extra DLLs, no game patches by them).**
A shim DLL holds the S1 hook and a single `AtomicPtr` "tick function" that it calls after
`something_pre_task()`. Generation DLLs `gen1.dll` and `gen2.dll` export
`get_descriptor()` returning a versioned `{abi, tick}`. The shim exposes a hotkey (checked at
S1 with `GetAsyncKeyState` + foreground check, the documented pattern) that does, at S1:
`LoadLibraryA("gen2.dll")` → read descriptor → validate ABI → `exchange` the pointer →
log old/new. Pass criteria: the log line switches from gen1 to gen2 on the next frame,
no restart, no crash for 10 minutes, and `gen1.dll` remains mapped (deliberately leaked).
Fail criteria to record: any frame gap, any crash, any double tick.
This is the whole of (a) with no game-state mutation: if it works, the remaining work is
moving the existing features behind the same pointer table.

Do not attempt either experiment on a save you care about; Stage 1 runs in a battle or on
the map, and Stage 2 needs no battle at all.

---

## 10. Operation ledger (formulas copied literally first)

**L1. Wall-clock frame dt** — decompiled `_FrameFunc`, quoted:

```
  lVar4 = _Xtime_get_ticks();
  frame_time_ = (float)((lVar4 - _currentTimeData_) / 10) / 1e+06 - _DAT_143a119b8;
  if (frame_time_ < 0.0) { frame_time_ = 0.0; }
  lVar4 = _Xtime_get_ticks();
  _DAT_143a119b8 = (float)((lVar4 - _currentTimeData_) / 10) / 1e+06;
```

Disassembly confirms the shape: `0x1401a89e9 IMUL RCX` (magic divide by 10), `0x1401a8a05
DIVSS` by `[0x1403548f4]` = `0x49742400` = **1e6f** (read from memory), `0x1401a8a11 SUBSS`
the previous-stamp global `0x143a119b8`, store at `0x1401a8a19`, clamp (`COMISS`/`JBE` and a
`MOV dword [...],0` at `0x1401a8a29`) `[code]`.
Reading term by term: `(ticks_now - epoch) / 10` is integer µs (the counter is in 100 ns
units — the /1e7 total conversion matches FILETIME-style ticks `[guess]`), `/1e6` is
seconds, minus the previous timestamp in seconds. No sqrt/abs/clamp other than the
"negative → 0" clamp. `_currentTimeData_` is the global `0x143a13b90` (start-time epoch) in
the disassembly; Ghidra only gave it a name.

**L2. Simulation step** — quoted:

```
  time_related_global_ = (1.0 / coreFrameRateFlt_) * coreTimeWrap_;
  if (doRecoil_global != '\0') { time_related_global_ = 0.0; }
  GameClock = GameClock + (double)time_related_global_;
```

`coreFrameRateFlt_` `0x1403c0de4` = 50.0f, `coreTimeWrap_` `0x1403c0dec` = 1.0f (default)
`[code, read_memory]`; destination `0x1403c126c`, `GameClock` `0x143a119c0` `[code]`.
Product: 0.02 s per frame. `doRecoil_global` `0x143a11909` zeroes it. No other term.

**L3. Frame idle sleep** — quoted disassembly:

```
0x1401a89c6 CALL 0x1402abed0                 ; QueryPerformanceFrequency(&+0x380)
                                             ; QueryPerformanceCounter(&+0x378)  <-- base = now
0x1401a8f96 CALL 0x1402ab980                 ; (QPC_now - base)*1e6/freq -> ring[count], +0x388
0x1401a8fe7 MOVSS XMM0,[0x1403c1268]         ; frame_time_ (wall dt of the previous frame)
0x1401a8fef UCOMISS XMM0,XMM7 ; JP/JZ skip   ; 0.0
0x1401a8ff6 CMP byte [0x1403c0df0],0 ; JZ skip
0x1401a8fff DIVSS XMM6,XMM2                  ; 1.0 / 50.0
0x1401a9007..0x1401a901e                     ; - FUN_1402abd10(= ring[last]/1e6, work seconds)
0x1401a9023 MULSS XMM1,[0x140352844]         ; * 1000.0f (read from memory)
0x1401a902b CVTTSS2SI RCX, XMM1              ; truncate to int ms
0x1401a9030 CALL qword [0x140351120]         ; Sleep
```

`0x1403c0df0` is the `CORE_USE_SLEEP` property (string `0x140371bb8`, 14 chars, registered
in `InitializeAppProperties` at `0x14023d5e4..0x14023d5f5`), static value 1 `[code]`.
Reading: sleep = trunc((1/50 − work_so_far)×1000) ms, only when the frame's wall dt
(measured at frame entry) is non-zero and the property is on; if the subtraction is ≤ 0
nothing is slept (`JBE` at `0x1401a9021`) `[code]`. No sqrt/abs.

**L4. Frame health value**:

```
fVar12 = FUN_1402abd50(DAT_147fc6a88,0);   // 1 / mean(ring of up-to-100 work times), i.e. FPS
fVar12 = fVar12 / coreFrameRateFlt_;       // FPS / 50
if (0.0 <= fVar12) { FLOAT_1403c0e14 = 1.0; if (fVar12 <= 1.0) FLOAT_1403c0e14 = fVar12; }
else FLOAT_1403c0e14 = 0.0;
```

`FUN_1402aba30` (`0x1402aba30`) sums the 100 ring entries and divides by 100.0 to get the
mean work time, caching it at timer+0x370 (invalidated to -1 by each stamp, `0x1402ab9c6`)
`[code]`. So this is "FPS the game would have if the sleep were removed", clamped to [0,1].

**L5. Frame-skip heuristic** (the bool passed to the video task):

```
fVar12 = 1.0 / (coreFrameRateFlt_ * *(float*)(ring + (len/2)*4) * 1.1);
if (fVar12 < 1.0) { thresholds 0.9/0.8/0.66/0.5/0.33/0.2 pick a period uVar6; ... }
bVar11 = ...;  // passed in SIL/ECX to SomethingVideoTask
```

The ring here (`DAT_143a1c450`, 20 entries max) holds this frame's **work time** (appended
at `0x1401a9046` from `FUN_1402abd10`, which reads the value stamped before the sleep), and
the sample is the middle entry. Terms: 50.0, that sample, 1.1 (constant at the site)
`[code, decompiled]`. With a 5 ms work time the ratio is ~3.6, so no frame is skipped; the
heuristic only becomes active when a frame's work approaches ~18 ms. The bool's consumer
was not found in the video task's prologue (§2.3).

**L6. Day-time advance** (context only):

```
DAT_143a119bc = (DAT_1403c1270 * time_related_global_) / 3600.0;
```

`DAT_1403c1270` is reset to 50.0 and then to 25/100/150/500/1000/2000/4000 depending on
campaign/zoom; `/3600.0` makes hours `[code, decompiled]`. Not used here.

---

## 11. Not determined / not found

* **Whether `SomethingVideoTask` uses its bool argument later** in its 5 KB body. Searched:
  decompiled prologue and the first 0xE0 bytes of disassembly (44 instructions) — no read of
  `ECX`; the two early-outs are globals. A full instruction scan of the body was not done.
* **Runtime value of `HGE_Impl+0xd70`** (fixed frame time). Inferred 0 from "no FPS state id
  in `Init_HGE`'s `SetStateInt` calls"; not read at runtime.
* **Which task dispatches `ClickFunc`** (the GUI click). `get_function_xrefs(0x14012d050)` and
  `(0x14012d168)` return only data/vtable references, so the dispatch is virtual; the
  calling task was not identified. Not needed for the safe-point argument (the load is
  inside the frame either way).
* **HGE state id semantics** for `SetStateInt(0x18)` in `Init_HGE` (`0x1401ad284`); ids
  `0x11/0x12/0x13` are width/height/bpp per [engine-hge.md].
* **Whether any other game code calls HGE `Timer_GetDelta`**; only the frame function's own
  time computation was traced.
* **What sets `HGE_Impl+0x978`** (disables the message pump at the top of the loop and exits
  the loop after the frame when non-null). Not searched; its role is unknown.
* **What triggers `Precache` after startup.** If a scene load or a new resource can call it
  mid-game, vcomp workers run during that frame. Only the `Init_HGE` call site and the
  function's own body were inspected; the callers of `Precache` at runtime were not
  enumerated.
* **Meaning of `DAT_1403c2b11`**, the byte that gates the whole `SomethingPreTask` body
  (`0x140286e44`). Presumably "initialised"; not checked.
* **BASS/D3D/vcomp threads**: BASS owns audio threads, the D3D driver its own, and
  `vcomp140.dll` a worker pool used by `Precache` (§3.1) `[code for the vcomp calls; the
  other two are out of static scope]`. `Precache` is the only known place where game code
  runs off the main thread.
* **Whether `FUN_140240b90` re-enters the resource manager** for media: not read (the
  loader's body was not decompiled); the scene-script path is proven by the call site and
  by `LoadSeriaFile` being one of its callees (`0x140240e54`).

(For completeness: "one frame driver" **was** checked, see §2.3 — each of the seven task
functions has exactly one code caller, `_FrameFunc`, and no modal loop calls them.)

---

## 12. Checked twice (mandatory self-check)

1. **Seven task calls, order and bytes at `0x1401a8eb8..0x1401a8eda`.** Re-read the
   decompiled `_FrameFunc` and the byte-level disassembly a second time; the five-byte
   `E8 ...` sequences and targets match the table, the values task is the 7th call and is
   unconditional. The recommended hook site is the first of them, no argument, flags dead
   after it. **Held.**
2. **Exit protocol: last instruction loads `[0x143a11901]` into `EAX`, `System_Start` tests
   `AL`.** Re-read `0x1401a90c7` (`0F B6 05 33 88 86 03`) and `0x14017e264`/`0x14017e26a`
   (`FF 93 10 06 00 00`, `84 C0`). Both sides re-checked. The loop's other exits are
   `WM_QUIT` from the pump and the `HGE+0x978` test (`0x14017e283`), whose setter I did not
   find. **Held** (with the extra exit condition noted).
3. **"The executable creates no threads."** Re-read the whole import table and the xrefs of
   `CreateEventW`, `WaitForSingleObjectEx`, `SetEvent`, `EnterCriticalSection`,
   `LeaveCriticalSection`: every non-data xref is in the CRT `_Init_thread_*` helpers; no
   `CreateThread`/`_beginthreadex` symbol exists in the program at all. **Held, with a
   correction found on the second pass**: the exe does import OpenMP (`vcomp140`) and calls
   `_vcomp_fork` from `Precache` `0x140170a20`, `0x140170b90` and `0x140170e30`, so
   `vcomp140.dll` runs those bodies on its own workers during precaching. The claim in the
   report is now "the simulation/frame state is single-threaded; the resource manager can be
   on vcomp workers during `Precache`", not "the process has one thread".
4. **`SeriaToLoad` is consumed in `SomethingPreTask`, not in `ClickFunc`.** Re-checked the
   xref list (reads at `0x140286e70..0x140286f2a`) and the `CALL 0x140240b90` at
   `0x140286f2a`, plus the two flag clears at `0x140286f4a/0x140286f51`; `SetLevelSeriaToLoad`
   only writes it (`0x14025b012`). **Held.**
5. **`patchy` cannot unpatch and calls into the DLL from `mmap` trampolines.** Re-read
   `src/session.rs` (`install_permanently` docs, `PermanentPatchSet { _pages, patches }`,
   overlap check) and `src/arch.rs` (`CALL_BYTES` + `function as usize`). Base object /
   ownership re-checked: the pages are `Mmap` allocations, not part of the DLL. **Held.**
6. **The frame function is registered once, as state `8`, and no render function is
   registered.** Re-read `Init_HGE` `0x1401ad0c0..0x1401ad145`: `LEA R8,[0x1401a8970]`,
   `MOV EDX,0x8`, `CALL [RAX+0x40]`, then ids `0xb/0xa/0xc/0xd` for other callbacks and no
   id `9`; `0x14017e26e` then only calls `[RBX+0x618]` if non-null. **Held.**
7. **Byte-level re-read of the four sites the recommendations depend on** (fresh
   `read_memory`): `0x1401a8eb8` = `E8 83 DF 0D 00`, `0x1401a8eda` = `E8 41 DF 16 00`,
   `0x1401a90c7` = `0F B6 05 33 88 86 03`, `0x140286f2a` = `E8 61 9C FB FF`. All four match
   the bytes quoted above. **Held.**
8. **`patchy` rewrites the site as a near jump, so the alignment argument holds.** Checked
   `patch.rs::prepare_detour` (`build_near_jump`, `NEAR_JUMP = 0xe9`, `NEAR_JUMP_SIZE = 5`)
   and `session.rs::allocate_trampoline` (`hook + NEAR_JUMP_SIZE`); the site is not a `call`.
   **Held** (an earlier draft said "replace the call with a call"; corrected to "jump to a
   trampoline that calls our function").

One correction made during the check: an earlier draft said the frame-skip bool *suppresses*
the video task. The video task is called unconditionally and its prologue never reads the
bool, so the report now says the consumer is unverified (the game itself may skip only part
of the 5 KB body, or the bool may be dead in 1.163).
