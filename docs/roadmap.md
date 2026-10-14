# Mod development roadmap (long term)

**Status: wish list. Not scheduled; partly started (see the status markers). Do not act on any item without being asked.**
Item names (Zenith, A220, Pytor, Khiva) are the game's own. Category tags: Bug, QoL, Feature, AI, Mod Scope, Physics Engine.

## Version scope
**Focus is 1.163.** Some players still use 1.151 because of gameplay differences from later versions. The ones that matter for us are the **speed curve** (already fixed, [mods/speed.md](mods/speed.md)) and the **damage changes**. The code-side differences are listed in [ammo-1151-vs-1163.md](findings/ammo-1151-vs-1163.md) (per-ammo shell lifetime, rocket warheads, incendiary power and more). Other 1.163 changes found: the close-range weapon cutoff, the 3500/3000 special-target ranges and the 0.025 rad aim tolerance in the AI weapon controller ([findings/ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md)), the harpoon, KAZ ammo and a removed debug overlay ([version-differences.md](version-differences.md)). Damage changes: done, see [findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md) (compared live on both versions; what stays open is listed there).

## Items

### Bugs and QoL
* **[Bug]** A proximity-fused missile colliding with flares crashes the game. *(open)*
  * Not located; what is known about the flare body and how to get the crash address: [findings/flare-crash-hunt.md](findings/flare-crash-hunt.md).
* **[QoL]** Remove the mechanic by which rockets (A220) lower mouse sensitivity globally for all weapon systems. *(partial: path mapped, cause not found)*
  * Partial: the sensitivity path is mapped and the slowdown is shown NOT to be a write to the device scale or global; location still unknown: [mouse-sensitivity.md](findings/mouse-sensitivity.md).
* **[QoL / Bug]** Changing an A220 rocket's weapon priority (to change hotkey grouping) removes the extended aiming reticle for rocket weapons. *(open)*
* **[QoL / Inconsistent behavior]** Salvage minigame: when a safety hazard occurs while the wreck site is out of focus, the game enters auto-mode instead of pausing. *(open)*
* **[QoL]** Option to disable Pytor's map-pointing interactions. *(open)*
* **[QoL]** Audio cue (or auto-pause) when aircraft intercept enemy forces on the strategic map. *(partial: hook point found, nothing built)*
  * Hook point: the two `SetLevelSeriaToLoad_` calls in the map aircraft group update; the existing intercept cue is `radio_kill_06` on `MAPMODE_RADIO_HANDSET`: [findings/map-air-groups.md](findings/map-air-groups.md).
* **[QoL]** Toggle for auto-pause on the strategic map. *(open)*
* **[Bug]** Capturing all cities around Khiva before the end-game event causes a crash loop / infinite loading. *(partial: probable cause and patch recipe, not reproduced or built)*
  * Probable cause found in the code (four unguarded list-head writes, same code in 1.151), with a patch recipe: [khiva-crash.md](findings/khiva-crash.md). Not reproduced in game.

### New features
* **[Feature]** Cruise-missile barrage mechanic (for example salvos of 4 simultaneous incoming cruise missiles). *(partial: hf_salvo)*
  * Partly done by hf_salvo: `map_launch_delay` lets a volley leave together (AI fleets too) and `group_missiles` merges a salvo into one fight (3-4 missiles verified [game]): [mods/salvo.md](mods/salvo.md). The AI's per-target salvo caps are untouched.
* **[Feature, missing]** A functional crew-requirement system. *(partial: research only)*
  * The per-ship totals already exist (`+0x17ec` present, `+0x17f0` capacity, `+0x17f4` needed); what consumes them was not looked for: [findings/sensors-and-crew.md](findings/sensors-and-crew.md).
* **[Feature]** Tracking of ballistic missiles in the terminal phase (near the target) on the strategic map. *(open)*
* **[Feature]** Editing of new enemy ship spawning events. *(open: saved strike groups can be rewritten, see `content.md`)*

### AI
* **[Strategic]** The AI launches all its aircraft when it detects the player within strike range, so none are left for defensive interception. *(partial: cause and patch sites found, not applied)*
  * Cause and byte-level patch sites: [ai-aircraft-launch.md](findings/ai-aircraft-launch.md). Not applied or run in game.
* **[Strategic]** The AI has no evasive manoeuvring against cruise missiles on the strategic map. *(open)*
  * Related, but interception odds, not evasion (no evasion code has been read): the intercept probabilities (75% missiles, 66% aircraft) are two literal `Random_Float` compares in `FUN_140111110`: [findings/map-air-groups.md](findings/map-air-groups.md).
* **[Tactical, exploitable]** Closing to very short range of an enemy ship in tactical combat disables all of its weapon systems. *(partial: patch sites found, not applied)*
  * Found, and a 1.163 addition: the cutoff and its patch sites are in [ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md) (section 1). Not applied or run in game.
* **[Tactical, exploitable]** The AI consistently gives way to the player's ship, which gives the player easy positional advantage. *(partial: patch sites listed, guess, untested)*
  * Likely mechanism (the stand-off retreat) and its patch sites: [ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md) (section 2). Guess; not run in game.
* **[Tactical]** The AI cannot use some ordnance or parts (LG/INC shells); AP rounds are fired only at extremely short range; the AI cannot deploy flares. *(partial: flares: cause and design; shells: patch-site notes; nothing built)*
  * Flares: the cause and a mod design are in [ai-flares.md](findings/ai-flares.md) (the release code is generic; only the player's input sets the flag `Creature +0xbc0`). Not yet implemented or run in game.
  * LG/INC/AP ammo choice by the AI: [findings/ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md) (section 3).
* **[Tactical, exploitable]** High convergence angles can be used to disable enemy turrets. *(open)*

### Mod scope
* **[Mod Scope / Bug]** Support for combined sensors. Sensor range calculation is currently bugged (accumulative) with two or more sensor types. *(partial: code reading done, live test not run)*
  * Code reading says sensors combine by per-sector maximum per type; only jammers sum, so the accumulation claim is not confirmed: [findings/sensors-and-crew.md](findings/sensors-and-crew.md). Test: two radars vs one in the range readout.
* **[Mod Scope]** HP modification for missiles (Zenith), aircraft, rockets (A220) and cannon shells. *(partial: constants located, no mod)*
  * Where each constant lives: all cannon shells have 1 HP (a single argument to `BulletImpact__`), rockets 10 HP in `FireShell`, canister pellets 30/10: [findings/firing-and-shells.md](findings/firing-and-shells.md). Missile HP is the stats-record field `+0x184 launched_health` ([structures.md](structures.md)); aircraft and missile HP are not tied in yet.
* **[Mod Scope]** Wider ship-roster modification (additional ship variants, adjustable composition ratio). *(open)*
* **[Mod Scope]** Editing the repair-part composition menu (hull, armor, landing gear, etc.). *(open)*
* **[Mod Scope]** Adjustable time-to-live (TTL) for cluster munitions and mine bomblets. *(partial: spawn function and call sites found)*
  * Spawn function and its two call sites (`0x140036c68`, `0x140036886`) found (sixth argument): [cluster-bomblet-ttl.md](findings/cluster-bomblet-ttl.md). TTL source at the second call site not traced; not applied or run in game.
* **[Mod Scope]** Damage model: calibers above 30 mm should not destroy missiles (Zenith), aircraft, rockets (A220) or cannon shells in a single shot. *(partial: mechanism pieces located, no mod)*
  * Starts from the `Ammo` fields (`explosivePower`, `penetrativePower`, `apDrag`) and `BulletImpact__`: [findings/firing-and-shells.md](findings/firing-and-shells.md), [findings/ammo-1151-vs-1163.md](findings/ammo-1151-vs-1163.md).
  * 1.163 multiplies area damage x5 on bodies with an aircraft-logic pointer (aircraft and missiles) [code, not live-tested]: [findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md).
* **[Mod Scope]** Acceleration and top-velocity modification for rockets (A220). *(partial: constants located, no mod)*
  * Rocket speed lives partly in the `Ammo` record (`speed` 150) and partly in the guidance branch of `creatureLogic` (logic id 130); `FireShell` sets `logicF2 = 1.5`: [findings/firing-and-shells.md](findings/firing-and-shells.md).

### Content pipeline
* Inject names/descriptions and part definitions at runtime instead of editing game files (removes the Python step and the update-overwrite problem).

### Physics engine
* **[Physics]** Limited acceleration restricts the turn rate of missiles (Zenith) and aircraft; capped top speeds restrict projectile velocity. *(open)*

## Tooling for modders (debug, edit, test)
Same status as above: wish list, partly started (see the markers). What exists today:
* `hfcrypt.py`: encodes and decodes the language packs.
* `apply_data.py` (identical copies in the multicharge and multimissile repos): creates variants of parts by cloning stats into `OL.seria`, body prototypes into `parts.seria`,
  text into the language packs and entries into `Shipworks.json`. Idempotent, makes a `.bak` once, supports `--dry-run`. It is a generator for one specific job (charge-level
  variants), not a general editor, but it holds working code for reading and appending `.seria` blocks.
* `dec`/`enc` (C++ with build script) in `hf_dialog_src`, another language-pack decoder; a `binwalk` binary in `hf_mods_unpack/tools/bin`.
* Per-mod log files, the modloader 4.1.0 logging SDK (`setup.md`), and Ghidra with an MCP bridge.
* `hf_probe` ([docs/mods/probe.md](mods/probe.md); log-only debug DLL, local, not a mod to ship): input and memory diff, `MODE`, `CLICK`/`TEXT`/`SOUND`/`LOAD` hooks, ammo dump, `MARK` hotkey (F9), HUD watch panel, and the 1.151/1.163 `BLAST`/`DMG` mode ([findings/probe-run-1.md](findings/probe-run-1.md), [findings/ui-events-and-screens.md](findings/ui-events-and-screens.md)); `hf_draw_test` (throwaway draw test, debug only). Beyond these, work is mostly hand-edited text.
Ordered by how much time each would save, not by effort. Tag: **[guess]** is an expected benefit (legend in `../README.md`); other claims are from problems we hit in practice.

### 1. `.seria` library and CLI (parse, query, patch, diff) *(partial: `apply_data.py` is only a generator)*
* **Why (hit in practice):** `.seria` is picky (nested `header=number { }`, braces alone on a line, never indented, defaults omitted, repeated `attr=value` lines are arrays), so by-hand edits
  of 2051 `m_stats` records break silently. The game also **rewrites `OL.seria` and `parts.seria` at startup**, and a game update overwrites `Libraries/`.
* A parser/serializer that round-trips a file byte-for-byte when nothing is changed (so a diff shows only the intended edit). Then:
  * `get`/`set` by id and field, for example `OL.seria[MDL_NUKE_03_CONV].m_launched_range`, with bulk edits from a CSV or JSON.
  * **Patch files instead of edited game files:** a small declarative list of changes (id, field, new value, expected old value) applied on top of vanilla. It survives game updates
    (re-apply), shows the old value when vanilla changed under it, and is what we would share with other modders instead of whole libraries. `apply_data.py` is the seed.
  * Decode and validate: `m_category` shown as bit names (table in `structures.md`), class codes as names, warnings for a cloned part whose `m_id` is not replaced everywhere
    it occurs (`formats.md`), unknown fields, wrong types.
  * `diff` between two game versions' libraries, for example 1.151 vs 1.163 (that is also the evidence for "which differences do players still prefer").

### 2. Save editor and save snapshots *(open; backups are manual)*
* **Why (hit in practice):** saves are plain text but huge (every part of every ship is a full Body record). Cash, unlocks, fuel and ship swaps are one-line edits that are tedious to find.
* Named snapshots (backup before editing is already the rule, make it one command) and a **save diff**: take two snapshots around an action (fire a volley, enter a city,
  refuel) and list exactly which fields changed. **[guess]** this is the cheapest way to learn what a game action writes, and it can confirm offsets in `structures.md`.
* Common edits as commands: cash (`m_scores`), `m_countdown`, unlocks, a city's fuel stock, escadra composition, NPC loyalty. Sanity checks before writing (`m_id` uniqueness, escadra
  references still resolve). Optionally a read-only "what is in this save" summary (fleets, cities, characters).

### 3. In-game debug mod (our own DLL) *(partial: `hf_probe` covers live reads and a HUD; pause/step, teleport, spawn, launcher, crash capture and watchdog are not done)*
* **Debug overlay or console on hotkeys** [guess]: pause and single-step the frame, time scale, teleport the fleet, set fuel/cash, spawn a part or a fleet, toggle invulnerability,
  kill a target, set `fleet+0x50c` directly. Each one removes a replay of the campaign from a test.
* **Live struct watch:** pick an object (selected part, selected fleet) and show its known fields by name using the layouts in `structures.md`, updating each frame (partial: `hf_probe` watches HELD, FLEET, LOCATION and GOLD). A field list that
  disagrees with the game is then visible immediately instead of in a later log.
* **Direct-to-scenario launcher:** call the level loader (`FUN_14025afd0`, owned by highfleet-salvo, so coordinate) to start `Missile.seria`, `Bombers.seria` and similar with chosen
  sides, skipping the map. Needed for testing salvo and AI work (`systems.md`), and for reproducing the crash bugs in the roadmap on demand.
* **Crash capture** [guess]: a vectored exception handler that logs faulting address, module, registers and a short stack, and writes a minidump. The flare-collision crash is
  currently "it crashes" with no address; this should turn it into an RVA we can open in Ghidra.
* **Hang watchdog** [guess]: the Khiva "infinite loading" is a loop, not an exception, so the handler above never fires. A watchdog thread that notices the main thread has made
  no frame or load progress for N seconds and then dumps its stack (or a periodic stack sampler) is what would find the loop. Two tools, one per failure kind.

### 4. Logging and tracing *(partial: marker hotkey and noise filtering done; JSON log hooks, structured lines and viewer not)*
* **Declarative log hooks:** a JSON file `{address, expected bytes, what to log}` that installs a log-only detour with the existing version guard (expected bytes compared before
  patching, see `hooks.md`), so a new probe needs no C++ rebuild. The "cheapest live probe" in `setup.md` is then a config edit.
* **Structured logs:** one line per event with frame number and game time, JSON lines, to the modloader's logging SDK (replaces our per-mod files). A small viewer that filters by
  mod/function and merges several mods in time order.
* **Marker hotkey:** the player presses a key and a marker line is written ("now I fired", "now the crash is about to happen"), so a log and a play session can be matched without
  guessing. Pairs with the save snapshots above. (Done: `hf_probe` `MARK`, F9.)
* Rate limiting: the AI calls the launch every frame (hundreds of failures per fight, `systems.md`), so any hook needs count-and-summarise or "log only changes". (Done in effect: `hf_probe` filters noise and prints summaries.)

### 5. Verification and regression *(partial: manual site checks and guards, `install.md` section 6 smoke test; no scripts or fingerprint)*
* **Site verifier (we did this by hand in practice):** read the patch-site table in `hooks.md` and check that every address still holds the expected bytes in a given exe or dump, plus the constants
  patched (300.0f launch cooldown, the 100/200 refuel rates, the 50.0f speed factor) and the class sizes in `structures.md`. We did this by hand for 1.163; scripted, it
  is a local script run after each game update (it needs the game exe or a dump, which cannot go in a public repo or public CI). It also answers "is this dump the same build" without opening Ghidra.
* **Install smoke test:** from a clean game folder, check modloader present, mods load, version guards pass, `hge.log` has no new errors, pass/fail log lines from `install.md`.
* **Notes vs binary check:** the same idea for `structures.md` offsets: a script that decompiles/greps a function and confirms a stated offset, so notes cannot drift unnoticed
  (the MapCraft size was wrong for a while).
* Game-file fingerprint (hash of `Libraries/`, `Data/`, exe) stored with each report, so a bug report says which build it came from.

### 6. Ghidra side (for the sync work between versions) *(open: assessment done, no Ghidra edits)*
* Export names, signatures and structs of a program to text in this repo (and import them back), so annotations live in git and can be reviewed. Complements Version Tracking
  for carrying 1.151 work to 1.163 and gives the second person a diffable view of changes.
* A checked-in list of named functions with address, and a script to flag the ones whose bytes differ between builds.
* **How automatable is the type transfer?** (checked read-only, nothing changed.) Names and function signatures: mostly yes, via Version Tracking (a session `1.15TO1.16Test` exists in the local project): matches at 0.99 and above can be applied, 0.9-0.99 spot-checked, below that by hand. Global labels: mostly yes. Plain/enum types and typedefs: yes (`clone_data_type`, `import_data_types`). Comments: only for matched functions. **Struct layouts (`Body`, `Escadra`, `Missile`, `Profile`, `Creature`): no, semi-manual**: offsets moved by region, so each needs a remap table (built in [version-differences.md](version-differences.md) for `Body` and `Profile`) and `resize_struct` / `modify_struct_field`; copying 1.151 structs over would put names on the wrong offsets.
* Tooling notes: the MCP also has `run_script_inline` / `run_ghidra_script` (custom transfer scripts are possible). Its archive-ingest function is disabled unless `GHIDRA_MCP_ARCHIVE_URL` is set; it would send data to an outside service, so leave it disabled. Every write needs the shared project checked out and saved; do it only after logdot's review, in small batches that can be undone by versions.
* Suggested order, each a separate Ghidra version so it can be reverted: (1) delete the `.conflict` duplicate types in 1.163 after checking nothing references them; (2) Version Tracking markup of function names and signatures; (3) import the `hge.h` types and HGE function names; (4) struct by struct, starting with `Body`, `Escadra`, `Missile`: resize to the real object size, lay fields at the 1.163 offsets, then bring the 1.151 names across.
* Not done: the 1,449 data types of 1.151 (535 in 1.163) have not been opened beyond `Body`, `Profile`, `ShipPart`, `HGEVFTABLE`; 1.151 comments, plate comments and bookmarks were not reviewed; 354 names exist only in 1.151 and were not opened except the ones in the findings.

### What to build first
1. The `.seria` round-trip parser with patch files (1) and the site verifier (5): both are small, scriptable and pay off at every game update.
2. Save snapshots with diff (2): turns "play and notice" into data for the notes.
3. Crash capture and the direct-to-scenario launcher (3): unblocks the crash bugs and combat testing in the roadmap. (Partly served by `hf_probe`; crash capture and the launcher are still open.)
4. The rest as the work needs it.
