# Hot-editing `hf_ai.json` (and `ally.json`) without restarting: source study (2026-10-27)

**Historical note (2026-11-05):** this study was written against `hf_ai` v0.10.0. At v0.10.15 the conclusion still holds (no config reload), but the line numbers, the `Params` type name, the `log_scan` hooks and the logging details below are from v0.10.0; public telemetry and scan logging were removed in v0.14.3.

Question: can testers edit `Modloader/config/hf_ai.json` and see the change without restarting the game? Method: read `hf_ai` (then v0.10.0, now in `mxtrnhf/highfleet-allies` under `ai/`; `src/lib.rs`, `tactics.rs`, `ai_flares.rs`, `missile_dump.rs`, `*_config.rs`) and `hf_ally` (`highfleet-allies/ally/src/lib.rs`) by hand. No code was changed and nothing was run. The game-side frame-loop facts come from [hot-reload-feasibility.md](../engine/hot-reload-feasibility.md).

## Short answer
**Yes, for hf_ai, with a modest change (roughly 150 to 250 lines, one new module), and no game patching beyond what hf_ai already does.** At v0.10.15 nothing re-reads the file: `init()` reads it once (`lib.rs`, `CONFIG_PATH`), there is no reload or mtime code in either mod (grep of both source trees), and [`hf-ai-tuning-guide.md`](../../mods/hf-ai-tuning-guide.md) pitfall (d) says "restart the game after editing". The blockers are in how the config is stored and which hooks get installed, not in the game.

## Why it does not work today (hf_ai, all `[code]`)
1. **Write-once storage.** `tactics.rs:33` `static PARAMS: OnceLock<Params>` (set in `tactics::init`, `PARAMS.set` ignores a second call). `ai_flares.rs:191` `static RUNTIME: OnceLock<Runtime>`; `Runtime` holds the whole sanitized `AiFlaresConfig`, the derived `Params` and `curtain_math::Params`, plus function pointers and addresses; set in `patch_ai_flares` (`RUNTIME.set(..)`, a second set logs "already prepared"). Readers: `tactics.rs:217`, `ai_flares.rs:648, 1146, 1165, 1250, 1316`.
2. **Hooks installed from the config at startup.**
   * steering hook (`0x140064a8d`): always installed when the site bytes match, so it already runs for every AI ship every tick.
   * the five `ai_flares` sites and the flare-hook detour (`0x14007f864`): only when `ai_flares.enabled` was true at start (`prepare(config.ai_flares.enabled, ..)`). If the key was false at start, flipping it later changes nothing.
   * engine-command boost hook (`BOOST_RVA`): only if the config at start asked for a boost (`panic_boost > 1` with panic evasion, a barrel roll, a curtain boost, or tactics `dive_boost`/`aim_boost` > 1; see `patch_ai_flares`, variable `boost`).
   * missile dump hooks (`0x140065c6c`, `0x140065edb`): only if `ai_missile_dump_chance > 0` at start (`patch_ai_missile_dump` returns early otherwise).
   * scan-log hooks: only with `log_scan` at start (v0.10.0-era telemetry; removed from public builds, ignore for current hf_ai).
3. **A few values are copied once into statics at init** (`INCLUDE_ALLIES`, `LOG_HZ`, `LOG_STEERING`, `DIVE_BOOST`, `AIM_BOOST`, `ENABLED`). Most of these are already atomics, so a reload only has to store them again. `INCLUDE_ALLIES` is stored only inside `patch_ai_flares`.

## What is already easy
* `missile_dump`: `DUMP_CHANCE`, `MIN_DELAY`, `MAX_DELAY` are `AtomicU32` read on every call; a reload only needs to store new bits (the hooks must exist, see below).
* `tactics`: `ENABLED`, `DIVE_BOOST`, `AIM_BOOST` are atomics; `Params` is a plain `Copy`-style struct.
* The pure math modules (`tactics_math`, `curtain_math`, `panic_math`) take their parameters as arguments, so they need no change.
* Every hook body already runs inside `catch_unwind`, guarded reads, and `try_lock`, so a reload at a tick boundary cannot unwind into the game.

## Proposed design (not implemented)
1. **Swappable config cells.** Replace `PARAMS` and the config part of `Runtime` by `RwLock<Arc<..>>` (or a small `ArcSwap`-style cell). Keep the immutable part of `Runtime` (resolved function pointers, addresses: they never change) in the `OnceLock`. Readers take a cheap `Arc` clone at the top of each hook body.
2. **One loader function used by both `init` and reload:** read file -> `serde_json::from_str::<Config>` -> `sanitized()` -> build all derived params -> publish. On any error (partial write, bad JSON, wrong type) keep the old config and log one line with the error and the file's mtime. Never apply half a file.
3. **Trigger: poll the file's mtime from the steering hook.** `on_steering` runs per AI ship per tick, only during a battle. Check at most once per second of wall clock (`Instant`, not game time: game time stops when frozen) with `std::fs::metadata(..).modified()`; compare against the last applied mtime. Debounce: if the parse fails, retry on the next poll (editors save in two steps). Result for testers: save the file and the numbers change within a second during a fight, and an edit made between battles applies on the first AI tick of the next battle. No hotkey is needed (a hotkey could be added the way `hf_ally` handles `retreat_key`).
4. **Install every hook whose site bytes match, regardless of the config, and gate inside the handler.** The disabled path of each handler must equal vanilla: the detours replay the stolen bytes (`trampoline.bytes(..)`), and `roll_hook`/`launch_hook` fall through to the game's own random and launch when the chance is 0. Cost is one hook call per creature per frame for `on_creature_update`, already the case today whenever `ai_flares` is on.
   * **Conflict to decide first:** hf_ai and the QoL fork's `ai_flares` patch the same sites and "whoever loads first wins" (see the header of `lib.rs`, hooks.md). Installing the `ai_flares` hooks unconditionally would take the sites away from the QoL fork even when hf_ai's `ai_flares` is off. Today's installed setup has QoL's `ai_flares.enabled` false ([STATUS.md](../../../STATUS.md)), so it is safe there. Options: (a) always install, and document that QoL's `ai_flares` must stay off; (b) add a restart-only key (say `install_flare_hooks`, default = current `ai_flares.enabled`) so existing setups behave as before.
5. **State reset on reload.** Per-ship state (`SHIPS`, `WORLD` in `tactics.rs`, `BURSTS`, the curtain/panic timers) can stay: it only holds timers and flags, not config. Entries created under the old numbers simply finish under the new ones. A reload that turns a feature off should clear its own transient state (for example `BOOSTED`, `BURSTS`) so no ship stays boosted.
6. Log a line on each applied reload with the changed keys (the existing `hf_ai: tactics ON (...)` style line makes it checkable), and bump the version.

## What stays restart-only (or needs a decision)
* `enabled` (master) as a way to remove hooks; with the always-install rule it becomes a runtime gate instead.
* `log_scan` hooks (v0.10.0 telemetry only; removed from public builds, so no current decision is needed).
* The build/version guards (`Steam 1.163`, image base, site bytes): startup only.
* The first line of the log row files (battle ids, file names): unaffected.

## Test plan (when someone implements it)
1. Unit tests: parse an edited config, a half-written file (must keep the old values), an unknown key (ignored, as today).
2. In game: start a battle with `tactics.enabled=false`, edit the file to `true` with a visible setting (for example `dive_chance 1.0`), expect the reload log line within a second and the changed behaviour; revert and expect vanilla behaviour again.
3. Toggle `ai_flares.panic_boost` from 1.0 to 2.0 mid-battle (needs the always-installed boost hook).
4. Edit while no battle is running, then start one: the first tick must log the reload.
5. Corrupt the JSON on purpose: one error line, old values kept, game unharmed.
6. Check the `catch_unwind` counters (`CAUGHT_PANICS`) stay at 0.

## hf_ally (read less closely; the user asked for hf_ai)
* `ally.json` is read once in `init` (`lib.rs` around line 2441) into about 35 statics. Most numeric and boolean settings land in atomics (`MAX_ALLIES`, `ALLY_DELAY`, `AUTO_RETREAT`, `HANDOVER`, `RETREAT_KEY`, `AMMO_ON`, `PROBE_LINES`, `MARKER_*`, `MAX_LINES`, `SPAWN_ALLY`, `telemetry::ENABLED`), so a reload could store them again.
* **Install-time (restart needed unless always-installed):** `prepare(&config)` decides hooks from `log_creatures`, `log_precombat`, `ally_toggle && spawn_ally`, `gui_inspect`, `ally_sounds && spawn_ally`, `debug_log`, plus the plane and enemy-count patches. The toggle button, creature log and sounds depend on these. Not read in detail: the plane loadout, `max_enemy_*`, `spare_prizes` and `intercept_ignore_oids` code paths.
* hf_ally already has a per-frame hook (the arcade battle manager `0x1402cc260`), a natural place for a poll, but the larger value is a single shared "config watcher" helper used by both mods so the behaviour matches.

## Where this fits in the bigger study
This is the "class L" case of [hot-reload-feasibility.md](../engine/hot-reload-feasibility.md): values read per call are hot once the storage is swappable; hooks that are installed from the config are class C (they need either always-install or a restart). hf_ai is a good first candidate because its steering hook is already always installed and runs only in battle.
