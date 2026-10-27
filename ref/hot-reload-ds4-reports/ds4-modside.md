# Hot-reload feasibility, part E: mod-side mechanics (DLL unload, repatch, config reload)

Program: `Highfleet.exe.unpacked.exe` v1.163, image base `0x140000000`. Static analysis only; no game
run. Ghidra read-only (no renames, no comments, no bookmarks). Findings about *our own* code are
cited by file:line and were read this session.

Sources read:

* `~/.cargo/git/checkouts/highfleet-modloader-9d58f70c80d6c7ea/9b64b34/` — Modloader v4.1.0 source
  (per `hf_notes/docs/setup.md`), `src/{lib,loader,host_logging}.rs`,
  `crates/highfleet-mod-api/src/logging.rs`.
* `~/.cargo/git/checkouts/patchy-rs-4acddf7b6571a3b5/2d49f4b/` — `patchy-rs` tag v0.1.0,
  `src/{session,patch,trampoline,relative_jump}.rs`. **All four of our mods link this exact tag**
  (`hf_ally/Cargo.toml:20`, `hf_ai/Cargo.toml:14`, `hf_probe/Cargo.toml:13`,
  `hf_qol_fork/Cargo.toml`).
* Mod sources: `hf_qol_fork/src/*` (2026-10-26 checkout), `hf_ally/src/lib.rs`, `hf_ai/src/lib.rs`.
* Notes (leads only, verified where I say `[code]`): `hf_notes/docs/{hooks,setup}.md`,
  `Modloader.v4/README.md`.

Honesty tags: `[code]` = read in this session at the cited place (Ghidra address, or repo
file:line). `[notes]` = a repo note says so, not re-checked. `[guess]` = inference, says what would
confirm it.

---

## 0. Verdicts

| Idea | Verdict | One-line reason |
|---|---|---|
| (a) Hot-swap a mod DLL in-process (`FreeLibrary` + `LoadLibrary` of a new build) | **Not feasible** | Every detour we install calls into DLL code from a trampoline; patchy's own contract says the library must stay loaded; the loader `mem::forget`s the module and mods own threads |
| (a') "Swap" without unloading: stable relay thunks + a swappable *payload* image | **Feasible with caveats** | The only realistic route to "new mod code without restart"; the game must never see a payload address |
| (b) Re-read mod JSON while running, for values the hook reads per call | **Feasible** | Already half-built: refuel rates are `AtomicU32`, sell/zoom are `static mut` read inside the hooks, and hf_ally/hf_ai configs are almost entirely atomics |
| (b') Re-read mod JSON for values that are *code* (feature on/off, ruleset choice, immediates) | **Feasible with caveats** | That is a *repatch*, not a reload: restore original bytes and re-apply. patchy forbids it by registry, so it needs our own writer |
| (c) Repatch machinery in general | **Feasible with caveats** | 5-byte writes are not atomic; patchy keeps no original bytes; needs a game-thread rendezvous. The 8-byte-slot design removes most of the risk |
| (d) Make the *loader* support unload | **Not feasible without a loader rewrite** | `std::mem::forget(library)` in `loader.rs:95`; no unload export; mods get no unload contract |

Confidence: (a)/(d) **high** — two independent hard facts (trampolines call into the DLL; the loader
never frees it). (b) **high** for the classification. (b')/(c) **medium** — the mechanics are
clear, but "safe on every site" depends on thread affinity of the patched functions, which is
[part: threads]' question, and each site has its own residue problem (§3.5).

---

## 1. What a mod actually installs (the inventory unload/repatch must undo)

Every patch goes through `patchy::PatchSession`. Three shapes exist (`src/patch.rs`):

1. **Detour, call + replay of the stolen bytes** —
   `patch_call(addr, hook, size, save_overwritten = true, ret)`. Builds
   `trampoline = [stolen bytes][call hook][jmp addr+size]` and writes `E9 rel32` plus NOP fill at
   `addr`. The trampoline is in a **separate mmap page**, but the call target is the **absolute
   address of the hook inside the mod DLL** — `trampoline::absolute_call` emits
   `FF 15 02 00 00 00 EB 08 <8-byte fn ptr>` `[code, src/trampoline.rs:112-129;
   src/patch.rs:34-84]`.

2. **Detour, call only, stolen bytes NOT replayed** (`save_overwritten = false`) — the hooked
   instruction's effect is re-implemented by the hook. Used where the site is a *replacement*:
   qol `zoom` (14 and 5 bytes), `sell_multiplier` (6), `speed` (5), `refuel` (three 8-byte `MULSS`
   sites), `plane_guns`. `[code, zoom.rs:36-47; sell_multiplier.rs:40-43; speed.rs:14-15;
   refuel.rs:118-124; plane_guns.rs:112-118]`

3. **In-place byte overwrite**, `PatchSession::overwrite(addr, bytes)`, no trampoline
   `[code, src/patch.rs:211-227]`. Used by qol `ttl` (4 bytes -> `90 90 90 90`), `shake`, `guns` on
   1.151, and three sites in `elevation_rules` `[code, ttl.rs:15; shake.rs:17; guns.rs:11;
   elevation_rules.rs:172,189,197]`.

How many: qol's `init` performs up to ~16-18 patch operations depending on the config
(`lib.rs:79-188`); the crate logs the real number at install:
`"Installed {patch_count} permanent patch(es) using {page_count} shared trampoline page(s)"`
`[code, src/session.rs:470-472]` — the user's own `Modloader/logs` line is therefore the exact
inventory for their build.

Consequences for unload, in order of severity:

* Shape 1 gives a live chain **game code -> mmap trampoline -> mod DLL** on hot paths (per frame,
  per bullet, per AI tick). Unmapping the DLL leaves a `call` into freed address space.
* Shape 2 leaves game code calling freed code directly.
* Shape 3 has no mod-code reference, so it is the only shape that survives a DLL unload unharmed.
  It is also the only shape that a "disable" must undo byte-by-byte, because there is no hook to
  gate at runtime.
* The trampoline page is `mmap`ed RWX, then sealed to RX (`make_exec`) and stored in a
  `static OnceLock<Mutex<Vec<PermanentPatchSet>>>` **inside the mod DLL's `.data`**
  `[code, src/session.rs:55-62, 387-436]`. Rust never drops statics and DLL unload does not run
  them, so the page is leaked rather than freed — not a crash, but "unload" can never reclaim that
  address space either.

---

## 2. (a) DLL unload

### 2.1 Blockers, each independently sufficient

**(1) Trampolines hold absolute pointers into the DLL.** `[code, src/trampoline.rs:112-129]` The
8-byte pointer in `absolute_call` is a mod `.text` address. The crate says it in the install docs:
*"Installation is permanent: the source modifications and executable trampoline allocations remain
live until the process exits. A library containing any callback or destination referenced by these
patches must therefore remain loaded for the same duration."* `[code, src/session.rs:376-379]`

**(2) The loader never unloads, and has no unload API.** `[code, loader.rs:56-97]` `load_mod` ends
in `std::mem::forget(library)`. `FreeLibrary` appears in the loader only in `DllMain` for the
proxied original `bass.dll_` `[code, lib.rs:76-80]`. Mods are enumerated once (`find_mods`,
`loader.rs:25-41`) and loaded once, in directory order — unsorted — `[code, loader.rs:43-54]`.

**(3) Mods own OS threads and per-thread state.** qol's elevation feature spawns two threads, a key
poll and an overlay window `[code, elevation.rs:225-236]`. `FreeLibrary` does not stop threads; their
next instruction fetch faults after `DLL_PROCESS_DETACH` returns. Rust statics, TLS, the panic hook
and the `log` crate's global logger slot also live in the DLL image `[code, mod-api/src/logging.rs:
17-18, 74-83 set_logger on a static LOGGER]`.

**(4) Code pointers we handed out survive reload.** Not needed to prove "not feasible", but it is why
a blind unloader cannot be written. Examples: `hf_ally` installs GUI elements whose callbacks are mod
functions `[notes, hooks.md:36-37]`; `hf_voice`/`hf_ally` hook `SomethingInputTask` and keep function
pointers in trampolines `[notes, hooks.md:68]`. Any game object that stored such a pointer outlives a
`FreeLibrary`.

**(5) The loader's logger holds loader-side context per mod.** `Box::leak(Box::new(ModLogContext))`
`[code, host_logging.rs:174-175]` — a leak, not a crash, but it means the loader has no per-mod
teardown at all; nothing in it was designed for a second load.

### 2.2 What a "clean" unload would have to do

1. Restore every patched byte exactly (needs the original bytes — patchy does not keep them, §3.2).
2. Prove no thread is inside a patched range or a trampoline (suspend all threads, or a game-thread
   rendezvous — the same problem as repatching, §4).
3. Remove every pointer to DLL code from game objects and the loader's logger.
4. Stop and join every DLL-owned thread, run TLS destructors, then `FreeLibrary`.
5. Re-do `version()` + `init()` for the new image, including every site's byte precheck.

None of 1-5 exists in any of our mods or in the loader.

### 2.3 Verdict

**Not feasible.** The mechanism is absent on both sides: the loader has no unload, patchy has no
uninstall and an explicit process-lifetime assumption, and mods have no unload contract. It is not
"hard", it is unimplemented by design.

Two narrowed statements that *are* true:

* A mod that installed **only** shape-3 patches and had no threads could in principle be unloaded
  with a hand-rolled byte ledger. Nothing in the repo is in that state (qol alone installs five or
  more call detours with the default config).
* **Even a perfect unloader would not deliver the feature**, because the *new* DLL needs a loader:
  the loader thread has finished and exports nothing that re-enters mod loading (`lib.rs` exports
  only BASS proxies and `wait_dll_proxy_init`). You would be writing an injector inside the game
  process. At that point the payload-swap design below is strictly less work.

### 2.4 The variant that works: keep the DLL, swap the payload

The shipped DLL is a thin **relay** that owns every detour. Each detour target is a one-instruction
thunk that reads a slot: `FF 25 <rel32>` / `jmp qword ptr [rip+disp]` over a
`static AtomicPtr<()>`. The relay `LoadLibrary`s a *payload* DLL from `Modloader/payloads/`, resolves
one `install`/`uninstall` pair, and publishes the payload's function pointers into the slots.
Reload = publish "disabled", wait for in-flight calls to drain, `FreeLibrary` the old payload, load
the new one, publish the new pointers.

Requirements:

* The payload never gives the game a raw function pointer (no GUI callbacks registered from payload
  code); the relay registers stable trampolines that bounce through slots.
* The payload never owns config state that the relay also reads. Config lives in the relay.
* The site *set* stays fixed for the process lifetime. Changing an `enable_*` boolean is not a
  payload swap unless the site is always hooked and the hook gates itself (§5.2 class C).
* Payload reloads need the same quiescence as §4, but only a slot store is atomic, so the window is
  one pointer, not 5 bytes.

**Verdict: feasible with caveats.** Cost: a new small crate (relay + ABI + payload loader) and
splitting each feature's `init` into "install once" and "publish config". No Ghidra work needed. The
hard part is discipline: no payload pointer may escape into the game.

---

## 3. (c) Repatch without unload

### 3.1 What the operation is, per site

| Change | Bytes touched | Can it be gated without touching bytes? |
|---|---|---|
| A value the hook reads (rate, multiplier, min/max zoom, TWR curve) | none — mod memory only | yes, that is §5 |
| `enable_*` on/off for a *detour* site | `E9 rel32` 5..26 bytes | on: install once, gate in the hook; off: gate in the hook |
| `enable_*` on/off for an *overwrite* site (ttl, shake, guns on 1.151, elevation_rules) | 4..7 bytes | **no** — no hook exists; must write the original bytes back |
| `enable_*` on/off for a *shape-2* replacement (`refuel`, `sell`, `zoom`) | none for refuel/sell (identity value), 8-14 bytes for zoom | refuel/sell: yes, §5.2; zoom: no, the hook cannot reproduce the game's value |
| `elevation_rules` variant | fixed byte variants at three sites | no — the variant *is* the bytes |
| `speed` preset | 5-byte `call` + a value | partly: the vanilla path exists in the hook, but `CURVE` is write-once |
| `planes` / loadouts | `TllContainer` rewrite in game data | not a patch at all (§5.2 class D) |

### 3.2 patchy cannot do it, by design

* **Global permanent registry (per DLL).** `ensure_patches_do_not_overlap_installed` rejects any new
  patch overlapping an installed one with `PatchError::OverlappingPatch`
  `[code, src/session.rs:344-371, called at 411]`. So a second `PatchSession` at the same address
  **always fails inside the same mod**. Re-running `init` after a config edit is therefore a
  guaranteed `init -> false`, which the loader only logs (`loader.rs:84-93`) — a silent half-feature
  from the user's point of view.
  Note the registry is a `static` in the crate, i.e. **one per DLL, not one per process**: it does
  not stop a *different* mod from patching the same address. That collision is caught later, by
  `validate_patch_sources` (compare against `expected`, `src/session.rs:328-342`) and by the mods'
  own byte prechecks. Both mechanisms are "first wins, second refuses", which is exactly why
  unloading the winner is not a neutral act (§3.4).
* **No retained originals.** `PendingPatch.expected` is consumed at install; only
  `{address, size}` goes into `PermanentPatchSet` `[code, src/session.rs:427-436]`. Nothing in the
  crate can restore the original instructions after install.
* **Trampolines are sealed.** `make_exec` turns the session's pages into read-exec `Mmap`; an
  installed trampoline cannot be rewritten, only abandoned `[code, src/session.rs:387-408]`.

So repatch = (i) our own ledger of `{address, original: Vec<u8>}`, taken before install, and (ii) our
own writer (`VirtualProtect` + copy + `FlushInstructionCache`), or a patchy fork that grows
`uninstall()` and a registry replacement path. Neither exists today.

### 3.3 The ledger, concretely

The ledger entry is authoritative. §6 gives the exact original bytes for eleven real sites, read from
the image this session. The write path is ~15 lines:

```rust
// one per site, filled before the first patch is installed
struct Site { addr: usize, size: usize, original: Vec<u8> }

unsafe fn write_code(addr: usize, bytes: &[u8]) -> bool {
    let mut old = PAGE_PROTECTION_FLAGS(0);
    if VirtualProtect(addr as *const c_void, bytes.len(), PAGE_EXECUTE_READWRITE, &mut old).is_err() {
        return false;
    }
    std::ptr::copy_nonoverlapping(bytes.as_ptr(), addr as *mut u8, bytes.len());
    let mut ignored = PAGE_PROTECTION_FLAGS(0);
    let restored = VirtualProtect(addr as *const c_void, bytes.len(), old, &mut ignored).is_ok();
    let flushed =
        FlushInstructionCache(GetCurrentProcess(), Some(addr as *const c_void), bytes.len()).is_ok();
    restored && flushed
}
```

and the rule that matters is not in the code: after writing, **re-read** the first bytes and compare
against the expected pattern (the same discipline as `refuel.rs:85-97`, `speed.rs:48-51`). If they
differ, someone else patched it and you must not silently continue.

### 3.4 Instruction boundaries and ownership (the two ways a restore corrupts silently)

* A restore must cover exactly whole instructions. Where `save_overwritten = true` patchy picked the
  span, so the ledger is automatically correct. Where `false`, a human picked it: `zoom` swallows
  **14** bytes at `0x1402c31c9`, which I verified is exactly two 7-byte instructions;
  `sell_multiplier` swallows **6** at `0x140221a3f` (one 6-byte `ADD`); `speed` swallows **5** at
  `0x140080699` (one `CALL`) — §6.
* Ownership: several sites are shared with other mods, and the *loser* of the race installs nothing at
  all. If mod A unloads/restores "its" site at `0x140303fb4` `E8 C7 03 DD FF` (§6) while mod B had
  skipped on a byte mismatch, the site stays **unpatched** until restart — a silent feature
  regression in a *different* mod. The same applies to `0x14012f120` (ClickFunc: hf_ally vs
  hf_probe) and `0x14018dbf0` (SomethingInputTask: hf_voice vs hf_ally) `[notes, hooks.md:37, 68]`.
  Any unload/reload feature must therefore re-run the *other* mods' prechecks, which a single DLL
  cannot do. This is an argument for keeping "reload" inside one mod (config reload) and treating
  cross-mod reload as out of scope.

### 3.5 Residue: state a patch leaves behind that byte restoration does not fix

Concrete, from qol `zoom` `[code, zoom.rs:74-85]`: the hook does not just compute a value, it writes
**two game dwords on every call** — `*0x1403c11d0 = max` and `*0x143a119a4 = min`. Restoring the 14
original bytes stops the hook, but the values it left behind are game state, and they are not the
mod's to keep:

* `0x143a119a4`, `0x1403c11cc` and `0x1403c11d0` are written **as a triple** by the game in several
  places: at the patched site (two of the three: `MOV [0x1403c11cc],R15D` + `MOV [0x1403c11d0],R15D`),
  in `UpdateZoom` (`MOV [0x1403c11d0],R13D` / `[0x143a119a4],R13D` / `[0x1403c11cc],R13D` at
  `0x14026c8ef`, `0x14026c8f6`, `0x14026c8fd`; and all three with the literal `1` at `0x14026c994`,
  `0x14026c99e`, `0x14026c9a8`), and in the level-seria loaders (xrefs at `0x1402c31b5`,
  `0x1402c52c0`, `0x1402d7549`, ...) `[code, disassembly + xrefs]`.
  So a mod value stored in `0x143a119a4` **self-heals only at the next of those writes**, not at
  restore time; between the two, `UpdateZoom` reads it (`0x14026af9a`, `0x14026afa8`) and acts on the
  mod's number `[code, xrefs]`.
* `0x1403c11cc` is read by unrelated systems: `Engine_ApplyThrustForce` (`0x1400288f3`),
  `get_screen_pos` (`0x140048976`), `creatureLogic` (`0x140043c15` and later writes) and
  `AiWeaponController` (`0x14007afef`) `[code, xrefs]`. It is not a private zoom variable; a reload
  that writes it for one frame is visible to them. Prefer "write only when the value changed", and
  only from the game thread.

The general rule for the ledger: a patch entry is
`{addr, original_bytes, game_globals_written: [(addr, original_value, next_game_writer)]}`; bytes
alone are not a complete undo. For qol `zoom` the entry is
`{0x1402c31c9, 14 bytes, [(0x1403c11d0, captured, 0x14026c8ef), (0x143a119a4, captured, 0x14026c8f6)]}`.

### 3.6 Verdict

**Feasible with caveats.** Caveats: own ledger incl. game-global residue; own writer (patchy refuses
by registry); instruction-boundary proof per site (the §6 table does that for qol's sites); a
game-thread rendezvous (§4); and no cross-mod reload (§3.4).

---

## 4. Threading rules

### 4.1 Patches were installed from the loader thread, not the game thread

`[code, lib.rs:63-84, 123-185]` `DllMain(DLL_PROCESS_ATTACH)` calls `DisableThreadLibraryCalls` and
`CreateThread(init, ...)`; that `init` does `AllocConsole`, the logger, `LoadLibraryA(bass.dll_)`,
`get_dll_path`, `get_version`, `create_folders`, `load_config`, `load_mods`. Every mod's `init()` —
and therefore every patch install — runs on **that loader thread**, concurrently with the game's own
start-up. patchy's install contract wants the opposite: *"No other thread may execute a patch source
while its instructions are being replaced."* `[code, src/session.rs:381-386]`

That is survivable at start-up (nothing has reached the patched code yet) and is precisely what a
mid-game reload cannot assume.

### 4.2 The rendezvous a reload needs

* Cheapest sufficient condition in this codebase: perform all writes **on the game thread**, from a
  hook that already runs once per frame. Two exist and are owned by our mods: qol's native elevation
  tick ("runs on the game thread once per editor frame", `[code, elevation.rs:11-14]`) and
  `SomethingInputTask` `0x14018dbf0` (entry prologue verified: `48 8b c4 48 89 58 08 48 89 70 10`,
  §6) used by hf_voice/hf_ally `[notes, hooks.md:68]`.
* A 5-byte `E9 rel32` or a 6-byte `ADD` write is **not atomic**: a thread that fetches inside the
  write sees a half instruction. `[x86 semantics; not a file claim]` The window is nanoseconds, the
  failure is a wild jump, and it is invisible until it isn't.
* The 8-byte-slot design (§2.4) removes this for the swap itself: one aligned `AtomicPtr` store is
  atomic. Keep byte writes for *installing a site the first time*, where the game has not reached it
  (start-up) or the site is provably idle (§5.3 step 4).
* If bytes must be written mid-game with no hook available: either pick a moment where the patched
  function provably cannot run (menu idle; only valid if the site is battle-only), or suspend all
  other threads and check each RIP against the target range. The second is what a real unloader
  would have to do anyway; it is also how you would prove (a) impossible/possible per site.

### 4.3 Which sites are thread-safe is [part: threads]' answer

I did not re-derive thread affinity. My recommendation is designed so that it matters only for the
overwrite sites: `0x140052af2` (bullet impact, `[notes, hooks.md:29]`), `0x14007f864` (per-creature
update, `[notes, hooks.md:26]`), `0x140036bb5` (creatureLogic, `[notes, hooks.md:30]`).

---

## 5. (b) Config reload

### 5.1 Today the file is read once

`[code, hf_qol_fork/src/lib.rs:42-66]` `init()` calls `Config::load("Modloader/config/qol.json")`
exactly once, on the loader thread, then uses the values to decide *which patches to prepare* and to
initialise statics. Nothing re-reads the file. `Config::load` / `save` are
`fs::read_to_string` + serde `[code, config.rs:212-240]`, so reading again is trivial; the work is in
what to do with the new values.

Same picture elsewhere: hf_ally reads `Modloader/config/ally.json` once in `init`
`[code, hf_ally/src/lib.rs:2052-2059]`, hf_ai reads `Modloader/config/hf_ai.json`
(`CONFIG_PATH`, `lib.rs:53`) once `[code, hf_ai/src/lib.rs:396-403]`, and the loader's own
`logging.json` is a `OnceLock`
`[code, host_logging.rs:149-157]` with the README explicitly saying changes apply next start
`[notes, Modloader.v4/README.md:51]`.

There *is* a runtime-file precedent in the repo: hf_ai reads `Modloader/current_battle.txt` at
runtime and its doc comment describes the re-read semantics
`[code, hf_ai/src/lib.rs:109-118]`. So "a file that is read while the game runs" is already an
accepted pattern here; what is missing is a *config* file with that treatment.

### 5.2 The three classes — this is the answer to (b)

**Class L (live).** The hook reads a mod static on every call. Reload = parse + store; no patch
bytes, no game code, no restart.

| Config key | Storage today | Read at | Ref |
|---|---|---|---|
| `refuel.player_rate_multiplier`, `refuel.ai_rate_multiplier` | three `AtomicU32` | every fleet update, in the hooks at `0x14011521f` / `0x140115240` / `0x14011529c` | `[code, refuel.rs:34-56, 76-120]` |
| `sell_multiplier` | `static mut f32` | every sale, `apply_sell_multiplier` | `[code, sell_multiplier.rs:21, 106-116]` |
| `zoom.min_zoom_level`, `max_zoom_level` | `static mut u32` | `set_zoom_level` hook, which also writes the two game globals | `[code, zoom.rs:3-19, 74-85]` |
| `zoom.zoom_levels` | `static mut Vec<f32>` | `calc_zoom_value` per call | `[code, zoom.rs:5, 95-112]` |
| `shop_parts` probabilities | `static mut Vec<CustomPart>` | shop generation hook | `[code, parts.rs:31, 85-165]` |
| hf_ally: whole config | a dozen atomics + one `Mutex<String>` | at use | `[code, hf_ally/src/lib.rs:2071-2093]` |
| hf_ai: `log_steering`, scan/log knobs | atomics | at use | `[code, hf_ai/src/lib.rs:413-416]` |

Caveat for class L: `static mut` holding a `Vec` is a data race if the writer grows it while the
game thread reads it (realloc frees the old buffer under the reader). Fix: keep the value in an
`Arc`/`Box<[T]>` behind an `AtomicPtr`, publish a new one, and leak the old buffer (one buffer per
reload; a dev loop can afford it). Plain scalars are fine as `AtomicU32` with
`f32::to_bits/from_bits` — `refuel.rs` already does exactly this.

One useful consequence of the shape split (§1): for the shape-2 sites that have an **identity value**,
class L is a complete on/off switch, not just a tweak. `refuel` with multiplier `1.0` computes
`dt * base * 1.0`, which is exactly what the replaced `MULSS` did `[code, refuel.rs:40-56]`;
`sell_multiplier = 1.0` computes `price * 1.0` and adds it, i.e. the original `ADD`
`[code, sell_multiplier.rs:106-116]`; `speed` keeps a vanilla branch in the hook
(`twr_minus_one.powf(0.5)`, `speed.rs:35-42`) but cannot be reached because `CURVE` is a `OnceLock`.
So "refuel off / sell off" need no repatch at all; "zoom off" does, because the hook has no way to
reproduce the value the game would have stored (`R15D` at the site, §6).

**Class C (compiled into the code).** The value is a byte pattern we installed. Reload = repatch:
restore original, prepare new, install. Every `enable_*` that selects a patch, every `overwrite`
payload, `elevation_rules`' variant, and `speed.preset` (because `CURVE` is a `OnceLock` —
write-once — `[code, speed.rs:33]`, so the value cannot be replaced at all until that is changed to
`RwLock` or an atomic pointer).

**Class D (data surgery).** `planes` / loadout health: `patch_planes` writes whole `TllContainer`s
into game memory with `std::ptr::write` `[code, plane.rs:117-123]`. Not a code patch; a reload would
replace live containers that game objects may already have borrowed from. Highest risk, least value
to hot-reload.

`enable_*` -> class, from `lib.rs:79-188`:

* `enable_flare_crash_fix` -> C (6 bytes at `0x140036bb5`, `[notes, hooks.md:30]`)
* `enable_anti_wobble` -> C (detour, `dumpable`)
* `enable_arcade_zoom` -> C for on/off, **L for the values**
* `enable_unblocked_guns` -> C on 1.163: `true` installs nothing, `false` installs a detour at
  `0x140032f22` `[code, guns.rs:19-40]` — so the *default* is the patched state
* `enable_reduced_shake` -> C (overwrite)
* `enable_unblocked_ttl` -> C (4-byte overwrite at `0x140052af2` `[code, ttl.rs:1-18]`)
* `enable_shop_parts` -> C for on/off, L for probabilities
* `elevation_rules` -> C (three overwrites `[code, elevation_rules.rs:172-197]`)
* `refuel` -> L
* `speed` -> C, and currently *unreloadable* even as a value (`OnceLock`)
* `elevation` -> C (detour + a `OnceLock<Settings>` at `elevation.rs:152`)

### 5.3 What an honest minimal "config reload" looks like

1. Add `reload_config()` **inside** the mod (not a new export the loader would have to know about).
2. Trigger: a 500 ms mtime poll on `Modloader/config/qol.json` from a worker thread. The mod already
   spawns worker threads (`elevation.rs:225-236`) and the crate's `windows-sys` features do **not**
   include `Win32_Storage_FileSystem` `[code, hf_qol_fork/Cargo.toml]`, so `ReadDirectoryChangesW`
   would mean adding a feature; polling needs only `std::fs`.
3. Apply class-L values immediately (atomics). Log every changed key old -> new, once.
4. For class-C keys: if the key changed, **refuse and log loudly**, unless the mod owns a complete
   ledger + writer for that site. "Refuse" is honest; a half-applied config is how the user gets an
   unexplainable bug. Note that with today's patchy, "apply" *cannot* work anyway (§3.2).
5. Never re-run `init`: it would fail at `install_permanently` (`OverlappingPatch`) and return false,
   which the loader logs as "Failed to initialize mod" and nothing else.

This delivers roughly four groups of qol settings (refuel both rates, sell multiplier, zoom values,
shop probabilities) live, for ~100 lines and no Ghidra work. For hf_ally it is even better: its
config is already atomics, so the same code covers nearly the whole file except the `enabled` /
site-ownership decisions.

### 5.4 Verdict (b)

**Feasible** for class L (small, safe, mostly mechanical). **Feasible with caveats** for class C (it
is repatching, with §3/§4's caveats). **Avoid** class D. User-facing sentence: *"mod JSON reload can
work for values that are read per call; toggling a feature on or off still needs repatch machinery,
which patchy deliberately forbids, so today that part must wait for a restart — or for a small fork
of patchy."*

### 5.5 The mod-side interface to parts (c)/(b) of the study

* If the game ever re-reads its own data files, the mod-side requirement is a **post-reload callback**
  for exactly one thing: qol's class-D write does `std::ptr::write` of new `TllContainer`s over the
  ones the game already points at `[code, plane.rs:117-123]`. A game-side data reload that rebuilds
  those containers must either leave them alone or re-run the mod's apply step; otherwise the health /
  loadout values silently vanish, or the mod writes over the fresh data.
* I found no other cached file-derived game pointer in our mods: part stats are re-queried per use
  through `GET_STATS` `0x140281e00` `[code, guns.rs:116]`, and shop parts are consulted at shop
  generation `[code, parts.rs:85-165]`. So a data reload does not need a general "re-apply everything"
  protocol, only the `TllContainer` case.
* In the other direction, a game-data reload gives a mod nothing for free: our config lives in
  `Modloader/config`, which the game never reads.

---

## 6. Byte-level checks of sites a reload would have to touch

Verified this session in `Highfleet.exe.unpacked.exe` (1.163, image base `0x140000000`). Segments
`[code, list_segments]`: `.text 0x140001000-0x1403505ff`, `.rdata 0x140351000-0x1403bc9ff`,
`.data 0x1403bd000-0x1403c63ff`, `.data 0x1403c6400-0x14807720f`, `.pdata 0x148078000-...`.
Every code site below is inside `.text`; the float constants are in `.rdata` (read-only at runtime,
hence `VirtualProtect` for operand repoints, which is what patchy does).

| Site | Instruction(s) in the image | Original bytes | Len | Shape |
|---|---|---|---|---|
| `0x140080699` | `CALL 0x140336606` then `MULSS XMM0, [0x140352824]` | `e8 68 5f 2b 00` | 5 | 2 (qol `speed`) |
| `0x14011521f` | `MULSS XMM0, dword ptr [0x14035282c]` (200.0f) | `f3 0f 59 05 05 d6 23 00` | 8 | 2 (qol `refuel`) |
| `0x140115240` | `MULSS XMM0, dword ptr [0x1403524e0]` (100.0f) | `f3 0f 59 05 98 d2 23 00` | 8 | 2 |
| `0x14011529c` | `MULSS XMM0, dword ptr [0x1403524e0]` (100.0f) | `f3 0f 59 05 3c d2 23 00` | 8 | 2 |
| `0x140052af2` | `MOVAPS XMM1, XMM10` (`ttl` NOPs 4 bytes) | `41 0f 28 ca` | 4 | 3 (qol `ttl`) |
| `0x140036bb5` | `MOV RBX, RAX` + `MOV RCX, RSI` | `48 8b d8 48 8b ce` | 6 | 1 (qol `flare_crash`) |
| `0x140221a3f` | `ADD dword ptr [RAX+0x2a8], ECX` | `01 88 a8 02 00 00` | 6 | 2 (qol `sell`) |
| `0x1402c31c9` | `MOV dword ptr [0x1403c11cc], R15D` + `MOV dword ptr [0x1403c11d0], R15D` | `44 89 3d fc df 0f 00 44 89 3d f9 df 0f 00` | 14 | 2 (qol `zoom`) |
| `0x14026b03f` | `CALL 0x14024f170` (then `MOVSS [0x1403c11c8], XMM0`) | `e8 2c 41 fe ff` | 5 | 2 (qol `zoom_levels`) |
| `0x140303fb4` | `CALL 0x1400d4380`, next insn `MOV DL,1` at `+5` | `e8 c7 03 dd ff` | 5 | 1 (qol/hf_probe seam, shared) |
| `0x14018dbf0` | `MOV RAX,RSP; MOV [RAX+8],RBX; MOV [RAX+0x10],RSI; MOV [RAX+0x18],RDI` (next insn `PUSH RBP` at `+15`) | `48 8b c4 48 89 58 08 48 89 70 10 48 89 78 18` | 15 | 1 (rendezvous candidate) |

Boundary check (the thing a restore must not get wrong): `0x1402c31c9 + 14 = 0x1402c31d7`, and the
instruction at `0x1402c31d7` is `MOVSS XMM0, [0x1403c2bc0]` — so the 14-byte window is exactly two
whole instructions `[code, disassemble 0x1402c31c9..]`. `0x140052af2 + 4 = 0x140052af6` is
`MOV RAX, [RBX]`, so 4 is a whole instruction. `0x140221a3f + 6 = 0x140221a45` follows the `ADD`
(one instruction). `0x140036bb5 + 6 = 0x140036bbb` is `CALL 0x140048870`. All good.

Constants read as floats `[code, read_memory]`:

* `0x140352824` = bytes `00 00 48 42` = **50.0f**
* `0x14035282c` = bytes `00 00 48 43` = **200.0f**
* `0x1403524e0` = bytes `00 00 c8 42` = **100.0f**
* `0x1403c11cc` = `01 00 00 00` (= 1) and `0x1403c11d0` = `04 00 00 00` (= 4): the image-time values
  of two of the three dwords the game writes as a triple (§3.5) `[code]`.
* `0x1403c2bc0` = `00 80 bb 44` = **1500.0f**, the initial zoom *value* `[code]` (used by the
  instruction right after the qol `zoom` window).

One unreadable-by-design address: `0x143a119a4` (qol's `MIN_ZOOM_ADDR`) returns
`"Unable to read bytes"` in Ghidra `[code, read_memory]`. It lies inside the `.data` block
`0x1403c6400-0x14807720f`, i.e. the part of the image with no file bytes — it is zero-initialised by
the loader and only meaningful after the game writes it. Consequence for a ledger: this global
cannot be restored from the file image; whatever was there before the mod wrote it must be captured
at runtime, or simply treated as "mod-owned from first call".

---

## 7. Proposed minimal experiment (do not run here)

Goal: prove the three graded claims with the smallest possible game-side surface. E1 uses
`hf_qol_fork`; E2/E3 use a throwaway mod. All of it on a **copy** of the game folder.

### E1 — live config reload (class L only). ~1 hour, no Ghidra, no risk of a stuck patch.

1. In `hf_qol_fork`, add a `reload_live(&Config)` step: `refuel` (both rates),
   `sell_multiplier` (change `SELL_MULTIPLIER` to `AtomicU32`), `zoom` min/max/levels (atomic ptr for
   the `Vec`). Everything else: `log::warn!("config changed but <key> needs a restart")`.
2. Start a 500 ms mtime-poll thread in `init` **after** `install_permanently`, logging
   `reload: qol.json changed` and then one line per changed key: `refuel.player_rate_multiplier 1.0 -> 4.0`.
3. In game: land a fleet at a fuel station, start refuelling, edit the JSON while it runs.
   Expected: `Modloader/logs` shows the reload line, and fuel flow visibly speeds up within a frame.
4. Kill criteria: any log line containing `OverlappingPatch`, any crash, or a refuel rate that
   changes only after a restart. If any of those appear, the class-L premise is wrong.
5. Second pass: change `enable_reduced_shake` in the same edit. Expected: the log says it needs a
   restart and the shake behaviour does **not** change — that is the honest confirmation of §5.2
   class C.

### E2 — repatch mechanics, both negative and positive. ~2 hours, throwaway mod, no shipped feature.

1. New tiny mod (`hf_reload_probe`) that installs **one** detour with patchy at
   `0x140303fb4` (or a scratch copy of the site in a private build) and logs
   `patch_session_1 ok`.
2. In its `init`, immediately try a second `PatchSession` at the same address. Expected: fails with
   `OverlappingPatch` — this reproduces §3.2 in one log line and proves patchy cannot be the
   repatch backend.
3. Add an own-writer `write_code` (§3.3) and a per-frame hook. First frame after start: read the
   original 5 bytes at `0x140303fb4`, log them, restore them, read back, re-install the detour. If
   the game survives 60 s of menu idle and of one battle, shape-1 self-repatch is mechanically
   possible on this build.
4. Kill criteria: any crash, or a readback mismatch. Note in the log which thread did the write:
   if it is the loader thread, you have reproduced §4.1 and the result is not transferable to a
   mid-battle reload.
5. Optional add-on worth one line: log `Suspended` thread count if you try the suspend-all variant;
   the point is to learn whether the game has a single-threaded render+logic loop.

### E3 — payload swap. Only if E2 passes.

Relay with one slot at `0x140303fb4` (a `jmp [rip+slot]` thunk), payload A and payload B that log
different strings; edit the payload file while running; confirm the log switches without a restart
and that the game never holds a payload address (assert by `FreeLibrary` immediately after the swap).

---

## 8. Risks

* **Silent cross-mod feature loss** if a reload ever restores a shared site (§3.4). Mitigation: keep
  reload inside one mod; never restore a site whose ownership is shared.
* **Non-atomic byte writes** (§4.2): a reload that writes 5 bytes while the game thread runs can
  jump into garbage, non-deterministically hours later.
* **Residue** (§3.5): byte restore does not undo game-global values; after a "vanilla" reload
  `0x143a119a4` keeps the mod's min value until the game's next triple write (`UpdateZoom` or a level
  loader), and `0x1403c11d0` until the restored instruction runs again.
* **`static mut` + `Vec`** (§5.2 class L): a hot-reloaded `zoom_levels` can free the buffer the game
  thread is indexing. Use an atomic pointer with leaked old buffers.
* **`OnceLock` masks** (`speed.rs:33`, `elevation.rs:152`): a reload cannot change those values even
  though the hook reads them per call — the failure mode is a log line claiming a reload that did not
  happen.
* **Loader logging is load-once** (`host_logging.rs:149-157`): flipping a mod to `trace` while
  debugging a reload needs a restart, which is ironic but harmless.
* **Users will expect (b') to work** because (b) works. The log messages in E1 step 5 are the
  mitigation: name the keys that need a restart, every reload.

## 9. What would change my verdicts

* For (a): a mod that patches nothing (pure data/overlay) could be loaded/unloaded with `LoadLibrary`
  from a *new* tool that runs inside the process. That is a different product, not a hot-swap of our
  mods.
* For (c): if [part: threads] shows the game is effectively single-threaded for logic+render, a
  per-frame-hook writer makes mid-game byte writes safe with no suspension, and (b') becomes a
  ~300-line feature instead of a risky one.
* For (b'): a `patchy` fork with `uninstall()` + byte ledger + registry replacement would remove the
  main structural blocker; that is ~150 lines in `session.rs` and is worth doing if (b') matters.

## 10. Not determined

* Thread affinity of each patched function (`0x14011521f` fleet update, `0x140080699` ship stats,
  `0x140052af2` bullet impact) — [part: threads]' remit; I only cited the notes.
* Whether any *game* object stores a pointer into a mod DLL besides GUI callbacks. I checked the note
  tables (`hooks.md:36-37, 68`) but did not audit hf_ally's GUI registration code.
* The exact role of each slot in the `0x1403c11cc` / `0x1403c11d0` / `0x143a119a4` triple (which is
  min, max, current). I read their image-time values, the two instructions qol replaces, the
  `UpdateZoom` triple writes and the xref sets; the assignment is `[guess]`, confirmable by
  decompiling `UpdateZoom` `0x14026af9a` and `FUN_14024f170`.
* Whether a mid-game `VirtualProtect` on a `.text` page can fail on this build (no game run allowed).
* The real `patch_count` for a given user config — readable from their log
  (`src/session.rs:470-472`), not from static analysis.
* Whether the loader's `find_mods` order is stable enough that "the first mod wins a shared site"
  is reproducible across runs (directory order, `loader.rs:25-41`) — `[notes, setup.md:40]` says
  order is unspecified.

## 11. Checked twice

Re-opened the three claims that carry the verdicts, at the cited addresses, after writing the first
draft:

1. **`0x1402c31c9` is 14 bytes of exactly two whole instructions** (`MOV [0x1403c11cc],R15D` 7 +
   `MOV [0x1403c11d0],R15D` 7, next instruction `MOVSS XMM0,[0x1403c2bc0]` at `0x1402c31d7`).
   Re-read after the first draft: same three instructions, same lengths, same bytes. Held. I also
   re-decoded `0x1403c2bc0` from bytes `00 80 bb 44` to `1500.0f` (the rule about hex constants
   shown as ints), not guessed. Held.
2. **`patchy` keeps no original bytes and refuses a second patch at the same address**
   (`src/session.rs:344-371` + `411`, `427-436`). Held on re-read. One correction to my first draft:
   the registry is a `static` inside the crate, i.e. **per DLL, not process-wide**; it does not
   prevent another mod from patching the same address. That is now stated in §3.2 and it is why §3.4
   (ownership) exists at all.
3. **The qol `zoom` hook writes two game dwords every call, and byte restoration does not undo
   them** (`zoom.rs:74-85`). Held, but my first draft was too strong in one place and I corrected
   §3.5: I had written that `0x143a119a4` "has no writer in the restored path", implying it never
   self-heals. Re-reading the xrefs and disassembling `0x14026c8e0`-`0x14026c9b0` showed the game
   writes `0x1403c11d0`, `0x143a119a4` **and** `0x1403c11cc` as a triple in `UpdateZoom` (`0x14026c8ef`,
   `0x14026c8f6`, `0x14026c8fd`, and with literal `1` at `0x14026c994`, `0x14026c99e`, `0x14026c9a8`),
   so the residue self-heals at the next zoom update — not at restore time. The qol hook overwrites
   slot 1 and slot 2 of that triple and leaves slot 3 (`0x1403c11cc`) to the game. Also re-read:
   `0x143a119a4` has **no file bytes** in the Ghidra image, so it cannot be restored from disk.
4. **The loader never frees a mod** — the single fact that decides (a). Re-opened `loader.rs` a
   second time: `std::mem::forget(library)` is the last statement of `load_mod` (`loader.rs:95`), and
   `grep -rn "FreeLibrary" src/` returns exactly two hits: the `use` at `lib.rs:33` and the
   `DllMain` detach path for the proxied original `bass.dll_` at `lib.rs:79`. Nothing frees a mod.
   Held.

Checked against the rules' known failure modes: no sqrt/abs/clamp formula is involved in this part
(the only arithmetic claims are float constant decodings, each read with `read_memory` and stated as
bytes); both sides of every "gate" I describe are stated (on = site installed + hook gates; off = site
absent, so bytes must be restored); base objects are named (mod statics vs game globals vs DLL code,
each with its owner); no invented constants — the three floats are `50.0`, `100.0`, `200.0` and
`1500.0`, read as bytes.
